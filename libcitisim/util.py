# FIXME decorator property/functools.lru_cache provides the same
class memoizedproperty:
    """Memoized properties

    >>> import random
    >>> class A:
    ...     @memoizedproperty
    ...     def a_property(self):
    ...         return random.randrange(1000)
    ...
    >>> a1 = A()
    >>> v1 = a1.a_property
    >>> v2 = a1.a_property
    >>> assert v1 == v2
    """

    def __init__(self, method):
        self.method = method
        self.instance = None
        self.cache = {}

    def __get__(self, instance, owner):
        self.instance = instance
        if instance not in self.cache:
            self.cache[instance] = self.method(instance)

        return self.cache[instance]

    def reset(self):
        del self.cache[self.instance]
