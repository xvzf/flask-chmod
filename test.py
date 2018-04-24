from flask import Flask, g
from flask_chmod import PermissionManager
from functools import wraps

try:
    from flask import _app_ctx_stack as stack
except ImportError:
    from flask import _request_ctx_stack as stack

app = Flask("Test")
pm = PermissionManager(app)


@pm.groups_for_user
def groups_for_user(username):
    if username == "testuser":
        return ["testgroup1", "testgroup2"]
    elif username == "testuser2":
        return ["testgroup1"]
    else:
        return []


def setuser(username):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            g.current_user = username
            return f(*args, **kwargs)
        return wrapper
    return decorator


def setuser_stack(username):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            ctx = stack.top
            ctx.user = username
            return f(*args, **kwargs)
        return wrapper
    return decorator


@app.route("/")
@setuser("testuser")
@pm.chmod(10, group="testgroup1")
def test():
    return "Hello World"

if __name__ == "__main__":
    app.run()