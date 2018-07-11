# -*- coding: utf-8 -*-
"""
    flask_chown.permission_manager
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Most basic Permission Manager

    :copyright: (c) 2018 by Matthias Riegler.
    :license: APACHEv2, see LICENSE.md for more details.
"""
import logging
from functools import wraps
from flask import abort, g

logger = logging.getLogger(__name__)

try:
    from flask import _app_ctx_stack as stack
except ImportError:
    from flask import _request_ctx_stack as stack
    logging.warning("It is recommended to update flask to a current version")

try:
    from flask_login import current_user
except ImportError:
    # If there is no flask login detected, just drop support
    current_user = None
    logging.warning("No flask-login available")


class PermissionManagerException(Exception):
    """ Exception happened during the function annotation, registering
    functions to get group info about a user or g.current_user is not set
    """


class PermissionManager(object):
    """ The `PermissionManager` provides a POSIX like access control to
    flask views (best used in combination with `flask-login`)
    The extension relies of `ctx.user` or `g.user` to being set
    (in this order), therefore it is possible to provide a custom
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


    If you are providing an extension that manages authentication, it is
    highly recommended to not use the `g` context,
    instead you can set `ctx.user` like this: ::

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
        """ Initializes the PermissionManager """
        if app:
            self.init_app(app)

    def init_app(self, app):
        """ Initializes the PermissionManager and registers an APP """
        app.permission_manager = self

    @property
    def current_user(self):
        """
        :returns: current user name
        """
        ctx = stack.top
        return str(getattr(ctx, 'user', None) or
                   getattr(g, 'current_user', None) or
                   current_user.username)

    def groups_for_user(self, callback):
        """ A decorator that is used to get a function that returns a list of
        groups where a given user is in.::

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
        """ Checks if a user is member of a given group """
        get_groups = getattr(self, "_get_groups_for_user", lambda user: [])

        # Checks if the user is a groupmember
        if group in get_groups(user):
            return True

        return False

    def check_granted(self, owner, group):
        """ Checks if a user is granted access to a view based on owner
        and group """

        # Base case, user equals the current user
        if owner and self.current_user == owner:
            return True

        # User has to be in a group to gain access to the view
        if group and self.user_in_group(self.current_user, group):
            return True

        # Default return False
        return False

    def chown(self, owner=None, group=None, action=None):
        """ A decorator that is used to determine whether a logged in user has
        access to a view::

            @app.route("/")
            # You can pass user and group
            @pm.chown(owner="test", group="users")
            def index():
                return "Hello World"

            @app.route("/")
            @pm.chown(group="users")
            def index():
                return "Hello World"

        :param owner: owner
        :param group: group
        :param action: lambda which handles redirects/abort whenever access
                       is denied
        """

        if not owner and not group:
            raise PermissionManagerException("You have to provide at least" +
                                             "one out of owner and group")

        def decorator(view):
            @wraps(view)
            def wrapper(*args, **kwargs):
                if self.check_granted(owner, group):
                    return view(*args, **kwargs)
                else:
                    if action:
                        return action()
                    else:
                        return abort(401)
            return wrapper

        return decorator
