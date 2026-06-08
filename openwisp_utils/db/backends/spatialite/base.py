import functools

from django.contrib.gis.db.backends.spatialite import base

# Django's SpatiaLite backend builds ``DatabaseWrapper.lib_spatialite_paths`` with
# ``ctypes.util.find_library("spatialite")`` on every new connection. On Linux
# ``find_library`` forks an ``ldconfig`` subprocess, so this happens once per
# connection. Besides being wasteful, it is dangerous in multi-threaded servers
# such as the selenium live-server test cases (WSGI ``StaticLiveServerTestCase``
# and the Daphne/ASGI ``ChannelsLiveServerTestCase``): forking while another
# thread is inside ``malloc``/``free`` (a SQLite connection close) corrupts the C
# heap, which surfaces intermittently on Python 3.13 as "double free or
# corruption" / segmentation fault. The lookup is deterministic, so memoize it.
base.find_library = functools.lru_cache(maxsize=None)(base.find_library)


class DatabaseWrapper(base.DatabaseWrapper):
    def prepare_database(self):
        # Workaround for https://code.djangoproject.com/ticket/32935
        with self.cursor() as cursor:
            cursor.execute("PRAGMA table_info(geometry_columns);")
            if cursor.fetchall() == []:
                cursor.execute("SELECT InitSpatialMetaData(1)")
        super().prepare_database()
