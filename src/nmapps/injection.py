# src/nmapps/injection.py
"""
The `nmapps.injection` module provides a simple dependency injection
implementation.

The following module members form the basic interface of this module:
    To **provide** dependencies:
     * :func:`set()` - provides a dependency value for a key with optional name
     * :func:`provide()` - decorator to provide classes, methods and functions for dependency
     * :func:`factory()` - decorator to call a callable to get a value for a dependency  
    
    To **get** dependencies:
     * :func:`get()` - gets the selected (last one provided by default) dependency for a key
     * :func:`get_all()` - gets all alternatives for a key
     * :func:`select()` - selects a named alternative (even before it is provided)

Typical usage:

>>> from nmapps import injection
>>> 
>>> # Notice that ImportantClass doesn't ever mention the DefaultDelegate
>>> # class.
>>> class ImportantClass(object):
>>>     def do_stuff(self):
>>>         delegate = injection.get("mypackage.ImportantClass.delegate")
>>>         if not delegate:
>>>             raise Exception
>>>         return delegate.do_stuff()
>>> 
>>> # And the DefaultDelegate class can provide its services without
>>> # mentioning the ImportantClass.
>>> @injection.provide("mypackage.ImportantClass.delegate", "default")
>>> class DefaultDelegate(object):
>>>     def do_stuff(self):
>>>         return "Hello World!"
>>> 
>>> # Yet, by default (unless other alternative is provided), they work
>>> # together. 
>>> obj = ImportantClass()
>>> obj.do_stuff() # returns "Hello World!"

"""

import logging

from .utils import UserException


LOGGER = logging.getLogger("nmapps.injection")


class DependencyException(UserException):
    pass


class DependencyManager(object):
    def __str__(self):
        return "%s()" % (type(self).__name__, )
    
    def set(self, key, value, *args, **kwargs):
        pass
    
    def get(self, key, fallback = None):
        if fallback is not None:
            return fallback
        raise DependencyException()
    
    def get_all(self, key):
        return []
    
    def select(self, *args, **kwargs):
        pass
    
    def clear(self):
        pass


class NullDependencyManager(DependencyManager):
    pass


class DependencyEntry(object):
    def __init__(self, key):
        self.key = key
        
        self.dirty = True
        self._selected = None
        self.selected_name = None
        
        self.alternatives = []
        self.named = {}
    
    @property
    def selected(self):
        if self.dirty:
            if self.selected_name is not None:
                try:
                    self._selected = self.named[self.selected_name]
                    return self._selected
                except KeyError:
                    LOGGER.warning("Selected named alternative %r for " \
                                   "dependency %r could not be found, " \
                                   "falling back to the last alternative.",
                                   self.selected_name, self.key)
            if len(self.alternatives) < 1:
                LOGGER.error("There are no alternatives for dependency %r.", self.key)
                raise DependencyException()
            self._selected = self.alternatives[-1]
            self.dirty = False
        return self._selected
    
    def add(self, value, name = None):
        self.dirty = True
        
        self.alternatives.append(value)
        
        if name is not None:
            if name in self.named:
                raise DependencyException()
            self.named[name] = value
    
    def select(self, name):
        self.dirty = True
        self.selected_name = name
    
    def get_all(self):
        return list(self.alternatives)


class DefaultDependencyManager(DependencyManager):
    def __init__(self):
        self.entries = {}
    
    def get_entry(self, key, throw = False):
        entry = self.entries.get(key, None)
        if entry is None:
            if throw:
                raise DependencyException()
            entry = DependencyEntry(key)
            self.entries[key] = entry
        return entry
    
    def set(self, key, value, name = None):
        entry = self.get_entry(key)
        entry.add(value, name)
    
    def select(self, key, name):
        entry = self.get_entry(key)
        entry.select(name)
    
    def get(self, key, fallback = None):
        if fallback is None:
            entry = self.get_entry(key, True)
            return entry.selected
        else:
            entry = self.get_entry(key)
            try:
                return entry.selected
            except DependencyException:
                return fallback
    
    def get_all(self, key):
        entry = self.get_entry(key)
        return entry.get_all()
    
    def clear(self):
        self.entries.clear()


MANAGER = DefaultDependencyManager()


def get(key, fallback = None):
    """
    Gets the value of a dependency by a key.
    
    Gets the value of a dependency by a key. If dependency is not found for the
    specified key, then :class:`DependencyException` is thrown unless
    `fallback` is not `None`, in which case `fallback` is returned.
    
    :param string key: the dependency key
    :param fallback:   the value to provide if the dependency is not found
    :returns: selected dependency
    
    :throws: :class:`DependencyException`
    """
    return MANAGER.get(key, fallback)


def get_all(key):
    """
    Returns list of all alternatives for the specified key.

    If no alternatives have been provided, empty list is returned.
    
    :param string key: the dependency key
    :returns: list of all alternatives for the specified key
    :rtype: list
    """
    return MANAGER.get_all(key)


def set(key, value, name = None):
    """Set the value of a dependency, optionally specifying a symbolic name."""
    if name is None:
        LOGGER.info("Setting the value %r for the dependency key %r.", value, key)
    else:
        LOGGER.info("Setting the value %r for the dependency key %r with name %r.", value, key, name)
    MANAGER.set(key, value, name)


def select(key, name):
    """
    Select an alternative for a dependency by name.
    
    An alternative can be selected by name *before* it is provided.
    """
    LOGGER.info("Selection the alternative %r for the dependency key %r.", name, key)
    MANAGER.select(key, name)


def clear():
    """Resets and clears all the values for the dependencies."""
    LOGGER.info("Clearing dependencies...")
    MANAGER.clear()


def provide(key, name = None):
    """
    Class, method and function decorator which specifies dependencies by key
    and name.
    
    :param string key:  the dependency key, which can be used to obtain it using :func:`get()`
    :param string name: name of the alternative, by which it can be selected using :func:`select()`
    
    >>> from nmapps import injection
    >>> 
    >>> @injection.provide("mypackage.frontend", "xml")
    >>> class XmlFrontend(object):
    >>>     # ... XML reading code ....
    >>> 
    >>> @injection.provide("mypackage.frontend", "csv")
    >>> class CsvFrontend(object):
    >>>     # ... CSV reading code ...
    >>> 
    >>> @injection.provide("mypackage.frontend", None)
    >>> class UnnamedFrontend(object):
    >>>     # ... whatever ...
    
    """
    def decorator(value):
        set(key, value, name = name)
        return value
    return decorator


def factory(key, name, *args, **kwargs):
    """
    Class and function decorator. Calls the decorated object (and passes any
    extra arguments or keywords to it) to get the dependency value to be set
    for the specified key and name.
    
    :param string key:  the dependency key, which can be used to obtain it using :func:`get()`
    :param string name: name of the alternative, by which it can be selected using :func:`select()`
    """ 
    def decorator(factory_callable):
        set(key, factory_callable(*args, **kwargs), name = name)
        return factory
    return decorator


if __name__ == "__main__":
    print __doc__

