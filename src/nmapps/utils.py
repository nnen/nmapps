# src/nmapps/usrexcept.py


import sys


def args_repr(*args, **kwargs):
    """
    Returns human-readable string representation of both positional and
    keyword arguments passed to the function.

    This function uses the built-in :func:`repr()` function to convert
    individual arguments to string.
    
    >>> args_repr("a", (1, 2), some_keyword = list("abc"))
    "'a', (1, 2), some_keyword = ['a', 'b', 'c']"
    """
    items = [repr(a) for a in args]
    items += ["%s = %r" % (k, v) for k, v in kwargs.iteritems()]
    return ", ".join(items)


def obj_repr(obj, *args, **kwargs):
    """
    Returns human-readable string representation of an object given that it has
    been created by calling constructor with the specified positional and
    keyword arguments.
    
    This is a convenience function to help implement custom `__repr__()`
    methods. For example:
    
    >>> class Animal(object):
    ...    def __init__(self, hit_points, color, **kwargs):
    ...       self.hit_points = hit_points
    ...       self.color = color
    ...       self.hostile = kwargs.get("hostile", False)
    ...    def __repr__(self):
    ...       return obj_repr(self, self.hit_points, self.color, hostile = self.hostile)
    >>> dog = Animal(2.3, "purple")
    >>> repr(dog)
    "Animal(2.3, 'purple', hostile = False)"
    """
    cls_name = type(obj).__name__
    return "%s(%s)" % (cls_name, args_repr(*args, **kwargs), )


class PrefixDict(object):
    def __init__(self):
        self.prefixes = {}
    
    def __len__(self):
        return len(self.prefixes)
    
    def __iter__(self):
        return iter(self.prefixes)
    
    def __getitem__(self, key):
        return self.prefixes[key]
    
    def __setitem__(self, key, value):
        key = str(key)
        
        for i in range(1, len(key) + 1):
            try:
                self.prefixes[key[:i]].add((key, value))
            except KeyError:
                self.prefixes[key[:i]] = set([(key, value), ])


def decorate_exception(e):
    if e is not None:
        e.exc_info = sys.exc_info()


class UserException(Exception):
    def __init__(self, *args, **kwargs):
        msg = kwargs.get("msg", None)
        if msg is None:
            Exception.__init__(self)
        else:
            Exception.__init__(self, msg)
        
        self.args = args
        self.kwargs = kwargs
        
        self.exc_info = None
        
        self.inner_exception = kwargs.get("inner", None)
        decorate_exception(self.inner_exception)
    
    def __str__(self):
        if self.message is not None and len(self.message) > 0:
            return self.message
        return type(self).__name__
    
    def __repr__(self):
        return "%s(%s)" % (
            type(self).__name__,
            ", ".join(["%r" % x for x in self.args] +
                      ["%s = %r" % (key, name, ) for key, name in self.kwargs.iteritems()]),
        )


class Null(object):
    """A class for implementing Null objects.
    
    This class ignores all parameters passed when constructing or 
    calling instances and traps all attribute and method requests. 
    Instances of it always (and reliably) do 'nothing'.
    
    The code might benefit from implementing some further special 
    Python methods depending on the context in which its instances 
    are used. Especially when comparing and coercing Null objects
    the respective methods' implementation will depend very much
    on the environment and, hence, these special methods are not
    provided here.
    
    Original code by Dinu C. Gherman.  Code found at
    http://code.activestate.com/recipes/68205/.
    """
    
    # object constructing
    
    def __init__(self, *args, **kwargs):
        "Ignore parameters."
        pass
    
    # object calling
    
    def __call__(self, *args, **kwargs):
        "Ignore method calls."
        return self
    
    # attribute handling
    
    def __getattr__(self, mname):
        "Ignore attribute requests."
        return self
    
    def __setattr__(self, name, value):
        "Ignore attribute setting."
        return self
    
    def __delattr__(self, name):
        "Ignore deleting attributes."
        return self
    
    # container/sequence methods
    
    def __len__(self):
        return 0

    def __getitem__(self, key):
        return self
    
    def __setitem__(self, key, value):
        return self
    
    def __iter__(self):
        return self
    
    def __reversed__(self):
        return self
    
    def __contains__(self, item):
        return False
    
    def next(self):
        raise StopIteration
    
    # comparsion
    
    def __eq__(self, other):
        return (self is other) or isinstance(other, Null)
    
    def __ne__(self, other):
        return not (self == other)
    
    # misc.
    
    def __nonzero__(self):
        """
        Used to convert Python objects to bool.

        This implementation always return `False` as the null object should
        evaluate to `False`.
        """
        return False
    
    def __hash__(self):
        return 73 + hash(Null)
    
    def __repr__(self):
        "Return a string representation."
        return "Null()"
    
    def __str__(self):
        "Convert to a string and return it."
        return "Null"


def test():
    "Perform some decent tests, or rather: demos."
    
    # constructing and calling
    
    n = Null()
    n = Null('value')
    n = Null('value', param='value')
    
    n()
    n('value')
    n('value', param='value')
    
    # attribute handling
    
    n.attr1
    n.attr1.attr2
    n.method1()
    n.method1().method2()
    n.method('value')
    n.method(param='value')
    n.method('value', param='value')
    n.attr1.method1()
    n.method1().attr1
    
    n.attr1 = 'value'
    n.attr1.attr2 = 'value'
    
    del n.attr1
    del n.attr1.attr2.attr3
    
    # representation and conversion to a string
    
    assert repr(n) == '<Null>'
    assert str(n) == 'Null'


if __name__ == '__main__':
    test()


