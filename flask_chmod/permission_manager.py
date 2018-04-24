"""
    :Filename:
        permission_manager.py
    :Authors:
        Matthias Riegler <matthias@xvzf.tech>
    :Version:
        24.04.2018
    :License:
        Apache 2.0
"""
from flask import abort, g
from functools import wraps

try:
    from flask import _app_ctx_stack as stack
except ImportError:
    from flask import _request_ctx_stack as stack


class PermissionManagerException(Exception):
    """
    Exception happened during the function annotation, registering functions to get
    group info about a user or g.current_user is not set
    """


class PermissionManager(object):
    """
    The `PermissionManager` provides a chmod like access control to flask views
    (best used in combination with `flask-login`)
    The extension relies of `ctx.user` or `g.user` to being set (in this order), therefore it is
    possible to provide a custom authentication framework, e.g.:

    .. code-block:: python

        from flask import Flask, g

        app = Flask()

        pm = PermissionManager()
        pm.init_app(app)


        def setuser(username):
            def decorator(func):
                def wrapper(*args, **kwargs):
                    g.current_user = username
                    return func(*args, **kwargs)
                return wrapper

            return decorator


    If you are providing an extension that manages authentication, it is highly recommended to not use
    the `g` context, instead you can set `ctx.user` like this: ::

        # Import the stack, _app_ctx_stack is only available for flask > 0.8,
        # if you need to support older versions,
        # just fall back to _request_ctx_stack
        try:
            from flask import _app_ctx_stack as stack
        except ImportError:
            from flask import _request_ctx_stack as stack


        def setuser_stack(username):
            def decorator(f):
                @wraps(f)
                def wrapper(*args, **kwargs):
                    ctx = stack.top
                    ctx.user = username
                    return f(*args, **kwargs)
                return wrapper
            return decorator

    """


    def __init__(self, app=None):
        """
        Initializes the PermissionManager
        """
        if app:
            self.init_app(app)


    def init_app(self, app):
        """
        Initializes the PermissionManager and registers an APP
        """
        app.permission_manager = self


    @property
    def current_user(self):
        """
        :returns: current user name
        """
        ctx = stack.top
        return getattr(ctx, 'user', None) or getattr(g, 'current_user', None)


    def groups_for_user(self, callback):
        """
        A decorator that is used to get a function that returns a list of groups where
        a given user is in.::

            @pm.groups_for_user
            def groups_for_user(username):
                if username == "test":
                    return ["test2", "test3"]
                else:
                    return ["test1"]


        """

        self._get_groups_for_user = callback
        return callback


    def user_in_group(self, user, group):
        """
        Checks if a user is member of a given group
        """
        get_groups = getattr(self, "_get_groups_for_user", lambda user: [])

        # Checks if the user is a groupmember
        if group in get_groups(user):
            return True

        return False


    @staticmethod
    def _check_chmod(chmod, msg=None):
        """
        Checks if a chmod is valid
        """
        # Never trust user input, especially when it comes to permissions ;-)
        if chmod not in [1, 10, 11, 100, 101, 110, 111]:
            if not msg:
                raise PermissionManagerException("Invalid chmod, valid values are 1[01]{1,2}")
            else:
                raise PermissionManagerException(msg)


    def check_granted(self, chmod, user, group):
        """
        Checks if a user is granted access to a view based on chmod
        """
        PermissionManager._check_chmod(chmod)

        # 'Parse' the chmod
        user_allowed = int(chmod / 100) > 0
        group_allowed = (int(chmod / 10) % 10) > 0
        other_allowed = (int(chmod % 10)) > 0

        # Base case, access is allowed to 'other', therefore everyone
        # can access the view
        if other_allowed:
            return True

        # Another base case, user equals the current user
        if user_allowed:
            if user == self.current_user:
                return True

        # User has to be in a group to gain access to the view
        if group_allowed:
            if self.user_in_group(self.current_user, group):
                return True

        # Default return False
        return False


    def chmod(self, chmod, user=None, group=None, action=None):
        """
        A decorator that is used to determine whether a logged in user has access to a view::

            @app.route("/")
            # You can pass user and group
            @pm.chmod(110, user="test", group="users")
            def index():
                return "Hello World"

            @app.route("/")
            # Or just a group or user
            # It makes no sense to use a 1XX value for chmod, as the user is set to None
            # and cannot be matched against the current user
            @pm.chmod(10, group="users")
            def index():
                return "Hello World"

        Available individual chmod values:
            - 100 -> 'User'  access is allowed
            - 010 -> 'Group' access is allowed
            - 001 -> 'Other' access is allowed

        Add up the values to get the correct chmod value, e.g. to allow
        user AND group access: `100 + 10 = 110`

        :param chmod: chmod
        :param user: user
        :param group: group
        :param action: lambda which handles redirects/abort whenever access is denied
        """

        # Security counter measurements to prevent unregistered user access
        # to views which are only restricted by group access and have a chmod
        # of 1XX. It would just match None == None == True and therefore
        # grant access to an unprivileged user
        if not user and chmod in [100, 101, 110, 111]:
            raise PermissionManagerException("Missing user")

        # Just do the same for group to provide consistency, even though
        # there is no vulnerability involved
        if not group and chmod in [110, 10, 111, 11]:
            raise PermissionManagerException("Missing group")

        def decorator(view):
            @wraps(view)
            def wrapper(*args, **kwargs):
                if self.check_granted(chmod, user, group):
                    return view(*args, **kwargs)
                else:
                    if action:
                        return action()
                    else:
                        return abort(401)
            return wrapper

        return decorator
