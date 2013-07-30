#!/usr/bin/python
# -*- coding: utf-8 -*-
"""nmapps.fs module.

Author: Jan Milík <milikjan@fit.cvut.cz>
"""


import sys
import os
import os.path as path
import shutil
import zipfile
import logging

import utils


__all__ = ["Path", "File", "Directory", "ZipFile", "ZipFileEntry", "replace_ext", "copy", "executing_file", ]


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


def copy(src_root, src, dst_root, dst = None):
    """
    Recursively copies files or directories. Sanely.
    
    Can copy file to dir (``a`` to ``b/``), file to file (``a`` to ``b``),
    files in dir to dir (``a/*`` to ``b/``) or dir to dir (both ``a`` to ``b/``
    and ``a`` to ``b/c``).
    
    **File To Dir**
    
    >>> copy("/file/dir", "file_name", "/dest/dir")
    
    **File To File**
    
    >>> copy("/file/dir", "file_name", "/dest/dir", "other_file_name")
    
    **Files In Dir To Dir**
    
    >>> copy("/file/dir", ".", "/dest/dir")
    
    **Dir To Dir**
    
    >>> copy("/dir/dir", "dir_name", "/dest/dir")
    >>> copy("/dir/dir", "dir_name", "/dest/dir", "other_dir_name")
    """
    src_root = Path.make(src_root)
    src = Path.make(src)
    dst_root = Path.make(dst_root)
    if dst:
        dst = Path.make(dst)
    
    full_src = src_root + src
    
    if full_src.is_file:
        if dst:
            LOGGER.info("Copying file %s to file %s...", full_src, dst_root + dst)
            shutil.copyfile(str(full_src), str(dst_root + dst))
        else:
            dst_dir = dst_root + src.dir
            if not dst_dir.is_dir:
                #LOGGER.info("Creating directory %s...", dst_dir)
                os.makedirs(str(dst_dir))
            LOGGER.info("Copying file %s to directory %s...", full_src, dst_dir)
            shutil.copy(str(full_src), str(dst_dir))
    elif full_src.is_dir:
        if dst:
            full_dst = dst_root + dst
        else:
            full_dst = dst_root + src
        if not full_dst.is_dir:
            #LOGGER.info("Creating directory %s...", full_dst)
            os.makedirs(str(full_dst))
        LOGGER.info("Copying files in %s to directory %s...", full_src, full_dst)
        for dir_file in os.listdir(str(full_src)):
            copy(full_src, dir_file, full_dst)
    else:
        raise ValueError


class Path(object):
    """
    Represents a file system path.

    This class is mostly just an OOP wrapper around the functions in `os.path
    <http://docs.python.org/2.7/library/os.path.html>`_.
    
    .. attribute:: value
        
        String value of the path.

        :type: string
    """
    
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
        return Path.join(self, right)
    
    def replace_ext(self, extension):
        return Path(replace_ext(self.value, extension))
    
    def base_with_ext(self, extension):
        return replace_ext(self.base, extension)
    
    def get_parts(self):
        return self.value.split(os.sep)
    
    def list_dir(self):
        val = str(self)
        return [Path.join(val, name) for name in os.listdir(val)]
    
    def iter_dir(self):
        val = str(self)
        for name in os.listdir(val):
            yield Path.join(val, name)
    
    def list_names(self):
        return os.listdir(str(self))
    
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
    def join(cls, *parts):
        return Path.make(path.join(*(str(part) for part in parts)))
    
    @classmethod
    def make(cls, value = None):
        if value is None:
            return Path.get_current()
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
    """
    Represents a file.
    
    .. attribute:: path
        
        Path to the file.

        :type: :class:`Path`
    """
    
    @property
    def exists(self):
        """
        Calls `os.path.isfile
        <http://docs.python.org/2.7/library/os.path.html#os.path.isfile>`_ to
        determine whether the instance's `path` attribute points to an existing
        file.
        
        :rtype: bool
        """
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
    
    def open(self, mode = "r", exc = True):
        """
        Opens a file and returns a `file object
        <http://docs.python.org/library/stdtypes.html#bltin-file-objects>`_.
        
        :param string mode: the file access mode, defaults to read-only
        :returns: a file object or None
        
        :throws: :class:`IOError`
        """
        try:
            LOGGER.debug("Opening file %s...", str(self.path.real),
                         extra = {"path": self.path,
                                  "real": self.path.real,
                                  "mode": mode, })
            return open(str(self.path.real), mode)
        except Exception, e:
            LOGGER.exception("Failed to open a file %s.", str(self.path.real))
            if exc:
                raise
        return None
    
    def read(self, exc = True):
        """
        Reads the contents of the file and returns its contents.
        
        :param bool exc: if `True`, the method throws an exception on failure
        :returns: contents of the file
        :rtype: string or None
        
        :throws: :class:`IOError`
        """
        c = None
        try:
            with self.open() as f:
                c = f.read()
        except Exception, e:
            LOGGER.exception("Failed to open and read a file %s.", str(self.path.real))
            if exc:
                raise
        return c
    
    def write(self, contents, exc = True):
        """
        Writes a contents to the file.
        
        :param string contents: the content to be written to the file
        :param bool exc: if `True`, the method throws an exception on failure
        :returns: `True` on success, `False` otherwise
        
        :throws: :class:`IOError`
        """
        with self.open("w") as f:
            try:
                f.write(contents, exc = exc)
            except Exception, e:
                LOGGER.exception("Failed to write to a file %s.", str(self.path.real))
                if exc:
                    raise
                return False
        return True
    
    @classmethod
    def make(cls, pth):
        pth = Path.make(pth)
        
        if pth.is_dir:
            return Directory(pth)
        
        if pth.extension.lower() in ZipFile.EXTENSIONS:
            return ZipFile(pth)
        
        return File(pth)


class Directory(File):
    """
    Represents a directory.
    """
    
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
    """
    Represents a zipped file.
    
    This is a wrapper around `zipfile
    <http://docs.python.org/2/library/zipfile>`_.  The added value is that it
    offers the same interface as the :class:`Directory` class to iterate
    through it's contents.  This way, zip files can be transparently treated as
    directories containing files (which they basically do).
    """
    
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
        """
        :returns: a list of the zip file entries
        :rype: list of :class:`ZipFileEntry` instances
        """
        return list(self.iter_list())


class ZipFileEntry(object):
    """
    Represents an entry (file) inside a zip archive.
    """
    
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


