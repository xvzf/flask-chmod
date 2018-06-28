# -*- coding: utf-8 -*-
"""
    flask_chown.permission_manager_cached
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Cached permission manager (based on redis)

    :copyright: (c) 2018 by Matthias Riegler.
    :license: APACHEv2, see LICENSE.md for more details.
"""
import logging
import json
from . import PermissionManager

import redis

logger = logging.getLogger(__name__)


class CachedPermissionManager(PermissionManager):
    """ Caches user groups in a redis datastore, optionally pass a timeout

    The `CachedPermissionManager` can be used as a drop in improvement for the
    `PermissionManager`. You can create an instance using::

        pm = CachedPermissionManager(redis_url="redis://localhost",
                                     timeout=3600)

    In this example, a timeout of one hour is set (60 minutes a 60 seconds)

    :param redis_url: Redis connection url
    :param timeout: Sepcify how long the groups should be cached (in seconds);
                    Set to 0 for no timeout
    """

    def __init__(
            self,
            *args,
            redis_url="redis://localhost",
            timeout=0,
            **kwargs):
        """ Init """
        super().__init__(*args, **kwargs)
        self.timeout = timeout

        # Connect to redis
        self._redis = redis.from_url(redis_url)

    @classmethod
    def _gen_json_pair(cls, user, group):
        return "flask_chown:CachedPermissionManager:granted" + json.dumps({
            "user": user,
            "group": group
            })

    def user_in_group(self, user, group):
        """ Cache this function """
        _cached = self.redis.get(self._gen_json_pair(user, group))
        if _cached:
            return b"True" == self.redis.get(self._gen_json_pair(user, group))
        else:
            return self._cache(user, group)

    def _cache(self, user, group):
        """ Caches the call """
        result = super().user_in_group(user, group)

        key = self._gen_json_pair(user, group)

        # Cache in redis
        self.redis.set(key, result)
        # Set timeout if requested
        if self.timeout > 0:
            self.redis.expire(key, self.timeout)

        return result

    @property
    def redis(self):
        """ Redis """
        return self._redis

    @property
    def timeout(self):
        """ :returns: Caching timeout """
        return self._timeout

    @timeout.setter
    def timeout(self, timeout):
        """ Sets the timeout """
        if timeout >= 0:
            self._timeout = timeout
        else:
            logger.error("{} is not a valid timeout value".format(timeout))
