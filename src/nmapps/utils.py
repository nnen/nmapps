# src/nmapps/usrexcept.py


import sys
import logging


LOGGER = logging.getLogger(__name__)


#####################################################################
## OBJECT UTILITIES                                                ##
#####################################################################


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
        """
        Implements the `iterator protocol
        <http://docs.python.org/library/stdtypes.html#iterator-types>`_.
        Iterating over a :class:`Null` object always yields no elements.
        """
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
        return ""


#####################################################################
## COLLECTIONS                                                     ##
#####################################################################


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


#####################################################################
## EXCEPTIONS                                                      ##
#####################################################################


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


class NMAppsException(UserException):
    pass


#####################################################################
## MISC                                                            ##
#####################################################################


class Callbacks(object):
    def __init__(self, owner = None, name = None, error_callback = None):
        self.callbacks = []
        self.owner = owner
        self.name = name
        self.error_callback = error_callback
    
    def __len__(self):
        return len(self.callbacks)
    
    def __getitem__(self, key):
        return self.callbacks.__getitem__(key)
    
    def __iter__(self):
        return iter(self.callbacks)
    
    def __call__(self, *args, **kwargs):
        return self.invoke(args, kwargs)
    
    def add(self, callback):
        self.callbacks.add(callback)
    
    def clear(self):
        self.callbacks = []
    
    def invoke(self, args = None, kwargs = None):
        args = args or ()
        kwargs = kwargs or {}
        
        for callback in self:
            try:
                callback(*args, **kwargs)
            except Exception, e:
                self.handle_callback_error(callback, e)
    
    def collect(self, args = None, kwargs = None):
        args = args or ()
        kwargs = kwargs or {}
        
        result = []
        
        for callback in self:
            try:
                result.append(callback(*args, **kwargs))
            except Exception, e:
                self.handle_callback_error(callback, e)
        
        return result
    
    def handle_callback_error(self, callback, exception):
        LOGGER.exception("Exception occured in callback %r in callbacks "
                         "owned by %r, named %r.",
                         callback, self.owner, self.name)
        if self.error_callback:
            try:
                self.error_callback(self, callback, e)
            except Exception, e:
                LOGGER.exception("Ironically, exception occured in error callback %r "
                                 "in callbacks owned by %r, named %r.",
                                 self.error_callback, self.owner, self.name or "<unnamed>")


if __name__ == '__main__':
    test()


