#!/usr/bin/python
# -*- coding: utf-8 -*-
"""nmapps.fs module.

Author: Jan Milík <milikjan@fit.cvut.cz>
"""


import sys
import os
import os.path as path
import zipfile
import logging


__all__ = ["Path", "File", "Directory", "ZipFile", "replace_ext", "executing_file", ]


LOGGER = logging.getLogger(__name__)


def replace_ext(pth, extension = None):
    """
    Replaces extension in a path string.
    
    >>> replace_ext("/path/to/file.c")
    '/path/to/file'
    >>> replace_ext("/path/to/file.dot", "svg")
    '/path/to/file.svg'
    >>> replace_ext("/path/to/file", "log")
    '/path/to/file.log'
    >>> replace_ext("/some/dotted.path/file.md", "html")
    '/some/dotted.path/file.html'
    >>> replace_ext("/some/dotted.path/file", "html")
    '/some/dotted.path/file.html'
    """
    limit = pth.rfind(os.sep)
    limit = len(pth) if limit < 0 else limit
    dot = pth.rfind(".", limit)
    
    if dot < 0:
        left = pth
    else:
        left = pth[:dot]
    
    if extension is None:
        return left
    return left + "." + extension


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
    
    def replace_ext(self, extension):
        return Path(replace_ext(self.value, extension))
    
    def base_with_ext(self, extension):
        return replace_ext(self.base, extension)
    
    def get_parts(self):
        return self.value.split(os.sep)
    
    def iter_parents(self):
        parts = self.real.get_parts()

        if str(self.real).startswith(os.sep):
            root = os.sep
        else:
            root = parts[0]
        
        for end in range(1, len(parts) - 1):
            yield Path.make(os.sep.join(parts[:-end]))
        
        yield Path.make(root)
    
    def add_to_import(self):
        sys.path.insert(1, self.abs)
    
    @classmethod
    def make(cls, value):
        if isinstance(value, Path):
            return value
        value = getattr(value, "path", value)
        if isinstance(value, basestring):
            value = Path(value)
        else:
            raise TypeError("Type \"" + type(value).__name__ + "\" is not supported.")
        return value
    
    @classmethod
    def get_current(cls):
        return Path(os.getcwd())


class File(object):
    @property
    def exists(self):
        return path.isfile(self.path)
    
    @property
    def basename(self):
        return path.basename(self.path)
    
    @property
    def extension(self):
        return self.path.extension
    
    def __init__(self, pth):
        self.path = Path.make(pth)
    
    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, str(self.path), )
    
    def __str__(self):
        return str(self.path)
    
    def open(self, mode = "r"):
        try:
            return open(self.path.real, mode)
        except Exception, e:
            LOGGER.exception("Failed to open a file.", extra = {"path": str(self.path.real)})
    
    def read(self):
        c = None
        try:
            f = self.open()
            c = f.read()
            f.close()
        except Exception, e:
            LOGGER.exception(e, extra = {"path": str(self.path)})
            return None
        return c
    
    @classmethod
    def make(cls, pth):
        pth = Path.make(pth)
        
        if pth.is_dir:
            return Directory(pth)
        
        if pth.extension.lower() in ZipFile.EXTENSIONS:
            return ZipFile(pth)
        
        return File(pth)


class Directory(File):
    @property
    def exists(self):
        return path.isdir(self.path)
    
    def __init__(self, pth = os.curdir):
        File.__init__(self, pth)
    
    def __iter__(self):
        return self.iter_list()
    
    def iter_list(self):
        for f in os.listdir(str(self.path)):
            yield File.make(self.path + f)
    
    def list(self):
        files = os.listdir(str(self.path))
        result = []
        for f in files:
            result.append(File.make(self.path + f))
        return result


class ZipFile(File):
    EXTENSIONS = set(["zip", "jar", "egg", ])
    
    def __init__(self, pth):
        File.__init__(self, pth)
        self._zip_file = None
    
    @property
    def zip_file(self):
        if self._zip_file is None:
            self._zip_file = zipfile.ZipFile(str(self.path), "r")
        return self._zip_file
    
    def iter_list(self):
        for info in self.zip_file.infolist():
            yield ZipFileEntry(self, info)
    
    def list(self):
        return list(self.iter_list())


class ZipFileEntry(object):
    def __init__(self, zip_file, info):
        self.zip_file = zip_file
        self.info = info
    
    def __repr__(self):
        return "ZipFileEntry(%r, %r)" % (self.zip_file, self.info.filename, )
    
    def __str__(self):
        return self.info.filename
    
    def open(self):
        return self.zip_file.zip_file.open(self.info)
    
    def read(self):
        return self.zip_file.zip_file.read(self.info)


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


