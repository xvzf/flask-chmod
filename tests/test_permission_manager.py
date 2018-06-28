import unittest
from .helper import mkapp, setuser, setuser_stack


class PermissionManagerBaseTest(unittest.TestCase):
    """ Setup used in the following test classes """

    def setUp(self):
        """ Setup the testcase """
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

    def _get_request_status_code(
            self,
            current_user=None,
            owner=None,
            group=None):
        """ Creates a client """
        app, _ = mkapp(self._setuser,
                       self._groups_for_user,
                       current_user,
                       owner,
                       group,
                       self._mkapp_factory)
        return app.test_client().open("/").status_code


class PermissionManagerAccessTestCase(PermissionManagerBaseTest):

    def test_restrict(self):
        """ Checks if invalid user cannot access the view """
        assert 401 == self._get_request_status_code(
                owner="testuser1", group="testgroup1")
        assert 401 == self._get_request_status_code(group="testgroup1")
        assert 401 == self._get_request_status_code(owner="testuser1")

    def test_user_in_group(self):
        """ Checks if a user in group (and not the privileged user) can access
        the view which requires the user to be in a group
        """
        # User 'testuser1' is member of 'testgroup1'
        assert 200 == self._get_request_status_code(current_user="testuser1",
                                                    group="testgroup1")
        assert 200 == self._get_request_status_code(current_user="testuser1",
                                                    owner="testuser2",
                                                    group="testgroup1")

    def test_user_not_in_group(self):
        """ Checks if a user (not the privileged user) who is NOT member of
        the required group is denied
        """
        # User 'testuser2' is NOT member of 'testgroup1'
        assert 401 == self._get_request_status_code(current_user="testuser2",
                                                    group="testgroup1")
        assert 401 == self._get_request_status_code(current_user="testuser2",
                                                    owner="testuser1",
                                                    group="testgroup1")

    def test_current_user_is_privileged(self):
        """ Checks if a user can access a view if he is the privileged user
        and NOT inside a group
        """
        # user 'testuser2' is the privileged user
        assert 200 == self._get_request_status_code(current_user='testuser2',
                                                    owner='testuser2')

    def test_current_user_is_not_privileged(self):
        """ Checks if a user can access a view if he is the privileged user
        and NOT inside a group
        """
        # user 'testuser1' is NOT the privileged user
        assert 401 == self._get_request_status_code(current_user='testuser1',
                                                    owner='testuser2')


class PermissionManagerAccessCtxStackTestCase(PermissionManagerAccessTestCase):

    def setUp(self):
        """ Just run the same tests again, but now set the user with the
        context stack
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


class PermissionManagerFactoryCtxStackTest(
        PermissionManagerAccessCtxStackTestCase):

    def setUp(self):
        """
        Just run the standart test set again, now with using a factory
        """
        super().setUp()
        self._mkapp_factory = True
