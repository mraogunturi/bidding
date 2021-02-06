# internal caching mechanism of django, 
# resued to cache the game timings
# import warnings
# from django.core.cache import CacheKeyWarning
from django.core.cache.backends.locmem import LocMemCache
# warnings.simplefilter("ignore", CacheKeyWarning)

class InternalCacheCls(LocMemCache):
    def validate_key(self, key):
        return True

INTERNAL_CACHE = InternalCacheCls('TestCache', {})