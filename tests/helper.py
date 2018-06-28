from time import time
from functools import wraps
from flask import Flask, g
from flask_chown import PermissionManager, CachedPermissionManager

try:
    from flask import _app_ctx_stack as stack
except ImportError:
    from flask import _request_ctx_stack as stack


def setuser(username):
    """ Sets g.user to username

    :param username: username which should be set
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            g.current_user = username
            return f(*args, **kwargs)
        return wrapper
    return decorator


def setuser_stack(username):
    """ Sets ctx.user to username

    :param username: username which should be set
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            ctx = stack.top
            ctx.user = username
            return f(*args, **kwargs)
        return wrapper
    return decorator


def return_time(f):
    """ Returns the time it took to execute a function """
    @wraps(f)
    def wrapper(*args, **kwargs):
        start = time()
        f(*args, **kwargs)
        return time() - start

    return wrapper


def mkapp(
        setuser_function,
        groups_for_user_function,
        current_user,
        owner,
        group,
        use_factory=False,
        cached=False,
        cached_timeout=0):
    """ Basic test app factory """

    app = Flask(__name__)
    app.debug = True
    app.secret_key = "veryimportantkey"

    if use_factory:
        if not cached:
            pm = PermissionManager()
        else:
            pm = CachedPermissionManager(timeout=cached_timeout)
        pm.init_app(app)
    else:
        if not cached:
            pm = PermissionManager(app)
        else:
            pm = CachedPermissionManager(app, timeout=cached_timeout)

    # Simple group resolution
    @pm.groups_for_user
    def groups_for_user_test(user):
        return groups_for_user_function(user)

    # Sample view so we can test behaviour
    @app.route("/")
    @setuser_function(current_user)
    @pm.chown(owner=owner, group=group)
    def index():
        return "OK"

    return app, pm
