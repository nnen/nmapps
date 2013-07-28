#!/usr/bin/python
# -*- coding: utf-8 -*-
"""nmapps.monad module.

Author: Jan Milík <milikjan@fit.cvut.cz>
"""


def make_decorator(func, *dec_args):
    def decorator(undecorated):
        def decorated(*args, **kwargs):
            return func(undecorated, args, kwargs, *dec_args)
        
        decorated.__name__ = undecorated.__name__
        decorated.__doc__  = undecorated.__doc__
        return decorated
    
    decorator.__name__ = func.__name__
    decorator.__doc__  = func.__doc__
    return decorator


class Monad(object):
    def bind(self, fn):
        raise NotImplementedError
    
    def __rshift__(self, fn):
        return self.bind(fn)
    
    @classmethod
    def maybe(cls, value):
        if value is None:
            return Nothing()
        return Just(value)


class Nothing(Monad):
    def __nonzero__(self):
        return False
    
    def bind(self, fn):
        return self


class Just(Monad):
    def __init__(self, value):
        Monad.__init__(self)
        self.value = value
    
    def bind(self, fn):
        return fn(value)


class Identity(Monad):
    def __init__(self, value):
        Monad.__init__(self)
        self.value = value
    
    def bind(self, fn):
        return Monad.maybe(self.value)


def main():
    print __doc__


if __name__ == "__main__":
    main()

