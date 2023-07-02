from django.core.cache import cache as cache_db, caches
#from django.core.cache.backends.memcached import PyMemcacheCache
from django.http.request import HttpRequest
from django.utils.module_loading import import_string
from django.core.exceptions import ImproperlyConfigured
from functools import lru_cache, partial

def view_caching_separator(watcher, request: HttpRequest, *args, **kwargs):
    print(request.session.get_expiry_age())
    return 

def cache_method_based_on(*conditions:any, watcher=None, is_a_view=False):
    """
        @param watcher a method that receives function args and kwargs and will returns a list of 
            watcher params to be passed to condition each time is called
        @param condition a method class or variable that returns true when the cache must expire
    """
    def wrapped_func(func: callable, conditions, watcher):
        def given_func(conditions, watcher, *args, **kwargs):
            if is_a_view:
                conditions += (view_caching_separator, )
            cached = cache_db.get(func.__name__, False) # gets the cached value from db if exists
            expire_cache = False
            if watcher:
                if not callable(watcher): 
                    raise ImproperlyConfigured("Watcher must be a callable that receives the sames args and kwargs that the wrapped function")
                watcher = watcher(*args, **kwargs)
            if cached:
                for condition in conditions:
                    if type(condition) is str:
                        condition = import_string(condition)
                    if callable(condition):
                        expire_cache = condition(cached, *args, **kwargs)
                    elif hasattr(condition, "__class__") and hasattr(condition, "should_expire"):
                        expire_cache = condition.should_expire(cached, *args, **kwargs)
                    else:
                        expire_cache = bool(condition)
                    if expire_cache:
                        break
                if not expire_cache: # if found returns the value in cache
                    return cached[0]
            data = func(*args, **kwargs)
            cache_db.set(func.__name__, [data, watcher])
            return data
        return partial(given_func, conditions, watcher)
    return partial(wrapped_func, conditions=conditions, watcher=watcher)

cache_view_based_on = partial(cache_method_based_on, is_a_view=True)

"""
c = 0
def test_counter():
    global c
    c += 1
    if c > 1:
        return True

@cache_method_based_on(condition1=test_counter)
def test_hello():
    print('hello world')
    return 'Yupiii'

print(test_hello())
print(test_hello())
print(test_hello())
print(test_hello())
"""