import unittest
from .helper import mkapp, setuser, return_time
from time import sleep
import redis


class CachedPermissionManagerTest(unittest.TestCase):
    """ Tests the cache implemtation of TestPermissionManager

        !!! THIS TESTS REQUIRES A LOCAL RUNNING REDIS SERVER !!!
    """

    TTL = 20

    def setUp(self):
        """ Setup the testcase """
        def groups_for_user(username):
            if username == "testuser1":
                # Add some delay so we can test better if caching works
                sleep(1)
                return ["testgroup1", "testgroup2"]
            elif username == "testuser2":
                sleep(1)
                return ["testgroup2"]
            elif username == "testuser3":
                sleep(1)
                return ["testgroup3"]
            else:
                sleep(1)
                return []

        self._groups_for_user = groups_for_user
        self._setuser = setuser

    def get_client(
            self,
            current_user=None,
            owner=None,
            group=None):
        """ Creates a client """
        app, pm = mkapp(self._setuser,
                        self._groups_for_user,
                        current_user,
                        owner,
                        group,
                        use_factory=False,
                        cached=True,
                        cached_timeout=self.TTL)

        return app.test_client(), pm

    def get_request_status_code(self, *args, **kwargs):
        """ Creates a client """
        client, _ = self.get_client(*args, **kwargs)
        return client.open("/").status_code

    def get_redis(self):
        """ Connects to the local running redis server """
        return redis.from_url("redis://localhost")

    def test_ttl_set(self):
        """ Checks if the expires is set correctly """
        rd = self.get_redis()
        client, pm = self.get_client(current_user="testuser1",
                                     group="testgroup1")
        key = pm._gen_json_pair("testuser1", "testgroup1")

        # Do a request so that the redis key gets generated
        assert 200 == client.open("/").status_code

        # Now check if the key TTL is in range of 0..TTL
        assert rd.ttl(key) <= self.TTL and rd.ttl(key) > 0

    def test_stored_key_access(self):
        """ Checks if access right is stored correctly """
        rd = self.get_redis()
        client, pm = self.get_client(current_user="testuser1",
                                     group="testgroup1")
        key = pm._gen_json_pair("testuser1", "testgroup1")

        assert b"True" == rd.get(key)

    def test_stored_key_denied(self):
        """ Checks if access denied is stored correctly """
        rd = self.get_redis()
        client, pm = self.get_client(current_user="testuser2",
                                     group="testgroup1")
        key = pm._gen_json_pair("testuser2", "testgroup1")

        assert b"False" == rd.get(key)

    def test_caching_persistant_user_in_group(self):
        """ Test if cached result always performs the same """
        client, _ = self.get_client(current_user="testuser1",
                                    group="testgroup1")

        for _ in range(10):
            assert 200 == client.open("/").status_code

    def test_caching_persistant_user_not_group(self):
        """ Test if cached result always performs the same """
        client, _ = self.get_client(current_user="testuser2",
                                    group="testgroup1")

        for _ in range(10):
            assert 401 == client.open("/").status_code

    def test_caching_speedup(self):
        """ Tests if caching is acutally successfull (sleep(1)) before return
        in the groups_for_user function
        """
        client, _ = self.get_client(current_user="testuser1",
                                    group="testgroup1")

        @return_time
        def get():
            assert 200 == client.open("/").status_code

        get()  # First call for caching :-)
        for _ in range(10):
            assert 1.0 > get()
