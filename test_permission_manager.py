# Python 2.7 compatibility
from __future__ import absolute_import, division, print_function
from builtins import super

import unittest
from functools import wraps
from flask import Flask, g
from flask_chmod import PermissionManager, PermissionManagerException

try:
    from flask import _app_ctx_stack as stack
except ImportError:
    from flask import _request_ctx_stack as stack


def setuser(username):
    """
    Sets g.user to username

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
    """
    Sets ctx.user to username

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


def mkapp(setuser_function, groups_for_user_function, current_user, chmod, user, group, use_factory=False):
    """
    Basic test app factory
    """

    app = Flask(__name__)
    app.debug = True
    app.secret_key = "veryimportantkey"

    if use_factory:
        pm = PermissionManager()
        pm.init_app(app)
    else:
        pm = PermissionManager(app)
    

    # Simple group resolution
    @pm.groups_for_user
    def groups_for_user_test(user):
        return groups_for_user_function(user)
    

    # Sample view so we can test behaviour
    @app.route("/")
    @setuser_function(current_user)
    @pm.chmod(chmod, user=user, group=group)
    def index():
        return "OK"
    
    return app


class PermissionManagerBaseTest(unittest.TestCase):
    """
    Setup used in the following test classes
    """
    def setUp(self):
        """
        Setup the testcase
        """
        def groups_for_user(username):
            if username == "testuser1":
                return ["testgroup1", "testgroup2"]
            elif username == "testuser2":
                return ["testgroup2"]
            elif username == "testuser3":
                return ["testgroup3"]
            else:
                return []
        
        self._groups_for_user = groups_for_user
        self._setuser = setuser
        self._mkapp_factory = False


    def _get_request_status_code(self, current_user=None, chmod=1, user=None, group=None):
        """
        Creates a client
        """
        client = mkapp( self._setuser, self._groups_for_user, current_user,
                        chmod, user, group, self._mkapp_factory).test_client()
        return client.open("/").status_code
    

class PermissionManagerChmodTestCase(PermissionManagerBaseTest):

    def test_chmod_invalid(self):
        """
        Test if invalid chmods are correctly discarded
        """
        with self.assertRaises(PermissionManagerException):
            self._get_request_status_code(chmod=100)

        with self.assertRaises(PermissionManagerException):
            self._get_request_status_code(chmod=110)

        with self.assertRaises(PermissionManagerException):
            self._get_request_status_code(chmod=10)
        
        with self.assertRaises(PermissionManagerException):
            self._get_request_status_code(chmod=2)
    

    def test_chmod_valid(self):
        """
        Tests valid chmods
        """
        self._get_request_status_code(chmod=1)
        self._get_request_status_code(chmod=10, group="test")
        self._get_request_status_code(chmod=11, group="test")
        self._get_request_status_code(chmod=100, user="test")
        self._get_request_status_code(chmod=101, user="test")
        self._get_request_status_code(chmod=110, user="test", group="test")
        self._get_request_status_code(chmod=111, user="test", group="test")


class PermissionManagerAccessTestCase(PermissionManagerBaseTest):

    def test_chmod_XX1_other(self):
        """
        Checks if everyone can access when the correct chmod is set
        """
        assert self._get_request_status_code() == 200
        assert self._get_request_status_code(chmod=11, group="testgroup1") == 200
        assert self._get_request_status_code(chmod=111, user="testuser1", group="testgroup1") == 200
    
    
    def test_chmod_XX0_other(self):
        """
        Checks if invalid user cannot access the view
        """
        assert self._get_request_status_code(chmod=110, user="testuser1", group="testgroup1") == 401
        assert self._get_request_status_code(chmod=10, group="testgroup1") == 401
        assert self._get_request_status_code(chmod=100, user="testuser1") == 401
    

    def test_chmod_X10_in_group(self):
        """
        Checks if a user in group (and not the privileged user) can access the view
        which requires the user to be in a group
        """
        # User 'testuser1' is member of 'testgroup1'
        assert self._get_request_status_code(chmod=10, current_user="testuser1", group="testgroup1") == 200
        assert self._get_request_status_code(chmod=110, current_user="testuser1", user="testuser2", group="testgroup1") == 200
    

    def test_chmod_X10_not_in_group(self):
        """
        Checks if a user (not the privileged user) who is NOT member of the required group is denied
        """
        # User 'testuser2' is NOT member of 'testgroup1'
        assert self._get_request_status_code(chmod=10, current_user="testuser2", group="testgroup1") == 401
        assert self._get_request_status_code(chmod=110, current_user="testuser2", user="testuser1", group="testgroup1") == 401
    

    def test_chmod_100_current_user_is_privileged(self):
        """
        Checks if a user can access a view if he is the privileged user and NOT inside a group
        """
        # user 'testuser2' is the privileged user
        assert self._get_request_status_code(chmod=100, current_user='testuser2', user='testuser2') == 200


    def test_chmod_100_current_user_is_not_privileged(self):
        """
        Checks if a user can access a view if he is the privileged user and NOT inside a group
        """
        # user 'testuser1' is NOT the privileged user
        assert self._get_request_status_code(chmod=100, current_user='testuser1', user='testuser2') == 401
    

class PermissionManagerAccessCtxStackTestCase(PermissionManagerAccessTestCase):

    def setUp(self):
        """
        Just run the same tests again, but now set the user with the context stack
        """
        super().setUp()
        self._setuser = setuser_stack


class PermissionManagerFactoryTest(PermissionManagerAccessTestCase):
    
    def setUp(self):
        """
        Just run the standart test set again, now with using a factory
        """
        super().setUp()
        self._mkapp_factory = True


class PermissionManagerFactoryCtxStackTest(PermissionManagerAccessCtxStackTestCase):
    
    def setUp(self):
        """
        Just run the standart test set again, now with using a factory
        """
        super().setUp()
        self._mkapp_factory = True