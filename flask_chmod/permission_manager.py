"""
    :Filename:
        permission_manager.py
    :Authors:
        Matthias Riegler <matthias@xvzf.tech>
    :Version:
        23.04.2018
    :License:
        Apache 2.0
"""
from flask import abort, g

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
    The `PermissionManager` provides a chmod like access control to flask views.
    Best used in combination with `flask-login`, however after checking the app/request
    stack, it checks `g.current_user` therefore it is possible to provide a custom
    authentication framework, e.g.:

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


    def user_in_group(self, user, group):
        """
        Checks if a user is member of a given group
        """
        return False
    

    def check_granted(self, chmod, user, group):
        """
        Checks if a user is granted access to a view based on chmod
        """
        # Never trust user input, especially when it comes to permissions ;-)
        if chmod not in [1, 10, 11, 100, 101, 111]:
            raise PermissionManagerException("Invalid chmod, valid values are 1[01]{1,2}")
        
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
            print("Checking for user", self.current_user)
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
            @pm.chmod(110, user="test", group="users")
            def index():
                return "Hello World"
            
        :param chmod: Available individual chmod values:
                      - 100 -> 'User'  access is allowed
                      - 010 -> 'Group' access is allowed
                      - 001 -> 'Other' access is allowed
                      Add up the values to get the correct chmod value, e.g. to allow
                      user AND group acces, `100 + 10 = 110`
        :param user: user
        :param group: group
        :param action: lambda which handles redirects/abort whenever access is denied
        """

        def decorator(view):
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
