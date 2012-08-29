#!/usr/bin/python

import sys
import os.path as path


__all__ = ["Path", "File", ]


class Path(object):
    @property
    def is_file(self):
        return path.isfile(self.value)
    
    @property
    def is_dir(self):
        return path.isdir(self.value)

    @property
    def is_abs(self):
        return path.isabs(self.value)
    
    @property
    def exists(self):
        return self.is_file or self.is_dir

    @property
    def base(self):
        return path.basename(self.value)

    @property
    def dir(self):
        return Path(path.dirname(self.value))
    
    @property
    def extension(self):
        parts = self.base.split(".")
        if len(parts) > 1:
            return parts[-1]
        return ""

    @property
    def base_without_ext(self):
        ext = self.extension
        if len(ext) < 1:
            return self.base
        return self.base[:-(len(ext) + 1)]
    
    @property
    def abs(self):
        return Path(path.abspath(self.value))
    
    @property
    def real(self):
        return Path(path.realpath(self.value))
    
    @property
    def relative(self):
        return Path(path.relpath(self.value))
    
    def __init__(self, value):
        self.value = value
    
    def __str__(self):
        return str(self.value)

    def __unicode__(self):
        return unicode(self.value)

    def __repr__(self):
        return "Path(%r)" % (self.value, )
    
    def __add__(self, right):
        right = Path.make(right)
        return Path(path.join(self.value, right.value))
    
    def add_to_import(self):
        sys.path.insert(1, self.abs)
    
    def make(self, value):
        if isinstance(value, Path):
            return value
        value = getattr(path, "path", path)
        if isinstance(value, basestring):
            value = Path(value)
        else:
            raise TypeError("Type \"" + type(value).__name__ + "\" is not supported.")
        return value


class File(object):
    @property
    def exists(self):
        return path.isfile(self.path)
    
    @property
    def basename(self):
        return path.basename(self.path)
    
    @property
    def extension(self):
        pass
    
    def __init__(self, path):
        self.path = Path.make(path)


def executing_file():
    return Path(sys.argv[0]).real


def foo():
    print executing_file()
    print __file__
    print __name__

    import __main__
    print "\n===== __main__ ====="
    print "__name__: %r" % (getattr(__main__, "__name__", None), )
    print "__file__: %r" % (getattr(__main__, "__file__", None), )

    import inspect
    import pprint
    s = inspect.stack()
    print "\n"
    pprint.pprint(s)

