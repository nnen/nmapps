# src/nmapps/usrexcept.py


import sys


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


