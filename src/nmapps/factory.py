#!/usr/bin/python
# -*- coding: utf-8 -*-
"""nmapps.factory package.

Author: Jan Milík <milikjan@fit.cvut.cz>
"""


import logging

from utils import Null, NMAppsException
import injection


LOGGER = logging.getLogger(__name__)


class FactoryException(NMAppsException):
    pass


class Factory(object):
    def __call__(self, *args, **kwargs):
        return self.create(*args, **kwargs)
    
    def create(self, *args, **kwargs):
        raise NotImplementedError
    
    def try_create(self, *args, **kwargs):
        try:
            return self(*args, **kwargs)
        except FactoryException:
            return None


class NullFactory(Factory):
    NULL = Null()
    
    def create(self, *args, **kwargs):
        return self.NULL


class FactoryContainer(Factory):
    def __init__(self):
        self.factories = []
        self.error_callback = None
    
    def add(self, factory):
        self.factories.append(factory)
    
    def iter_factories(self):
        return iter(self.factories)
    
    def create(self, *args, **kwargs):
        for factory in self.iter_factories():
            try:
                result = factory(*args, **kwargs)
                if result:
                    return result
            except FactoryException:
                pass
            except Exception, e:
                LOGGER.exception("Exception occured while calling %r factory.", factory)
                if self.error_callback:
                    try:
                        self.error_callback(factory, e)
                    except Exception:
                        LOGGER.exception("Exception occured inside factory "
                                         "container error callback %r.",
                                         self.error_callback)
        raise FactoryException()


class InjectedFactory(FactoryContainer):
    def __init__(self, dependency_key):
        FactoryContainer.__init__(self)
        self.dependency = injection.get_dependency(dependency_key, all_ = True)
    
    def iter_factories(self):
        for factory in FactoryContainer.iter_factories(self):
            yield factory
        for factory in self.dependency.value:
            yield factory


INJECTED_FACTORIES = {}


def create(key, *args, **kwargs):
    try:
        factory = INJECTED_FACTORIES[key]
    except KeyError:
        factory = InjectedFactory(key)
        INJECTED_FACTORIES[key] = factory
    return factory.create(*args, **kwargs)


def main():
    print __doc__


if __name__ == "__main__":
    main()

