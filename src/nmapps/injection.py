# src/nmapps/injection.py

import logging

from .utils import UserException


LOGGER = logging.getLogger("nmapps.injection")


class DependencyException(UserException):
    pass


class DependencyManager(object):
    def __str__(self):
        return "%s()" % (type(self).__name__, )
    
    def set(key, value, *args, **kwargs):
        pass
    
    def get(key, fallback = None):
        if fallback is not None:
            return fallback
        raise DependencyException()
    
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
    
    def clear(self):
        self.entries.clear()


MANAGER = DefaultDependencyManager()


def get(key, fallback = None):
    """Get the value of a dependency by a key."""
    return MANAGER.get(key, fallback)


def set(key, value, name = None):
    """Set the value of a dependency, optionally specifying a symbolic name."""
    MANAGER.set(key, value, name)


def select(key, name):
    """Select an alternative for a dependency by name.
    
    An alternative can be selected by name before it is provided."""
    MANAGER.select(key, name)


def clear():
    """Resets and clears all the values for the dependencies."""
    MANAGER.clear()


def provides(key, name, *args, **kwargs):
    """Class and function decorator which specifies dependencies by key and name.""" 
    def decorator(factory):
        set(key, factory(*args, **kwargs), name = name)
        return factory


if __name__ == "__main__":
    print __doc__

