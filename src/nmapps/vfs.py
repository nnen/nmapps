#!/usr/bin/python
# -*- coding: utf-8 -*-
"""vfs module.

Author: Jan Milík <milikjan@fit.cvut.cz>
"""


import cStringIO as StringIO
import logging
import urlparse

from . import utils
from . import factory
from . import injection
from . import fs


LOGGER = logging.getLogger(__name__)


#### Path Functions #################################################


SEPARATOR = "/"


def to_path(value):
    if ":" in value:
        raise ValueError
    return str(value).strip().replace("\\", "/")


def normalize_split(*paths):
    absolute = False
    components = []
    
    for path in paths:
        if isinstance(path, basestring):
            path = str(path).strip()
            if path.startswith(SEPARATOR):
                absolute = True
                components = []
        else:
            absolute = absolute or path[0]
            components = path[1]
        
        for component in path.split(SEPARATOR):
            if component in (".", ""):
                pass
            elif component == "..":
                if len(components) < 1:
                    raise ValueError("Too many backreferences in path \"%s\"." % (path, ))
                components.pop()
            else:
                components.append(component)
    
    return absolute, tuple(components)


def normalize(*paths):
    is_absolute, components = normalize_split(*paths)
    result = SEPARATOR.join(components)
    if is_absolute:
        return SEPARATOR + result
    return result
    

def split(path):
    components = tuple(path.split(SEPARATOR))
    if path.startswith(SEPARATOR):
        return True, components[1:]
    return False, components


def is_absolute(path):
    return str(path).strip().startswith(SEPARATOR)


#### IContent #######################################################


class IContent(object):
    def read(self, vfile):
        raise utils.NotSupportedError()
    
    def write(self, vfile, content):
        raise utils.NotSupportedError()
    
    def read_stream(self, vfile):
        return StringIO.StringIO(self.read())
    
    def write_stream(self, vfile):
        class OutStream(StringIO.StringIO):
            def __init__(s, i_content):
                StringIO.__init__(s)
                s.i_content = i_content
            def flush(s):
                StringIO.StringIO.flush(s)
                s.i_content.write(s.getvalue())
            def close(s):
                s.flush()
                StringIO.StringIO.close(s)
        return OutStream(self)


class NullContent(IContent):
    def read(self, vfile):
        return ""
    
    def write(self, vfile, content):
        pass

NULL_CONTENT = NullContent()


class StringContent(IContent):
    def __init__(self, buffer):
        IContent.__init__(self)
        self.buffer = buffer
    
    def read(self, vfile):
        return self.buffer
    
    def write(self, vfile, content):
        self.buffer = content


#### IDirectoryContent ##############################################


class IDirectoryContent(object):
    def list(self, vfile):
        return list(self.list_iter())
    
    def list_iter(self, vfile):
        raise utils.NotSupportedError()


class NullDirContent(IDirectoryContent):
    def list_iter(self):
        if False:
            yield None
        return
    
NULL_DIR_CONTENT = NullDirContent()


#### VirtualFile ####################################################


class VirtualFile(object):
    def __init__(self, fs, root_fs, name, content = None, dir_content = None):
        self.fs = fs
        self.root_fs = root_fs
        self.name = name
        
        self.content     = content or NULL_CONTENT
        self.dir_content = dir_content or NULL_DIR_CONTENT
    
    def __repr__(self):
        return utils.obj_repr(self, self.fs, self.name)
    
    def read(self):
        return self.content.read(self)
    
    def read_stream(self):
        return self.content.read_stream(self)
    
    def write(self, contents):
        return self.content.write(self, contents)
    
    def write_stream(self):
        return self.content.write_stream(self)
    
    def get_child(self, name):
        return self.dir_content.get_child(name)
    
    def list(self):
        return self.dir_content.list()
    
    def list_iter(self):
        for item in self.dir_content.list_iter():
            yield item


class FileProxy(object):
    def __init__(self, root_fs, fs, path, name):
        self.root_fs = root_fs
        self.fs      = fs
        self.path    = path
        self.name    = name


class NullFile(VirtualFile):
    def __init__(self, name, parent = None):
        VirtualFile.__init__(self, name, parent)


#### FileSystem #####################################################


class FileSystem(object):
    def __init__(self, url):
        #VirtualFile.__init__("root", None, NullContent(), DirContentBase())
        self.url          = url
        self.mount_points = {}
    
    def get_file(self, path, root_fs = None):
        fs, local_path = self.get_mounted_fs(path)
        return fs.get_file_unmounted(path, root_fs)
    
    def get_file_unmounted(self, path, root_fs = None):
        raise NotImplementedError
    
    def read(self, path):
        f = self.get_file(path)
        return f.read()
    
    def read_stream(self, path):
        f = self.get_file(path)
        return f.read_stream()
    
    def write(self, path, content):
        f = self.get_file(path)
        return f.write(content)
    
    def write_stream(self, path):
        f = self.get_file(path)
        return f.write_stream(content)
    
    def make_dirs(self, path):
        fs, local_path = self.get_mounted_fs(path)
        return self.make_dirs_unmounted(local_path)
    
    def make_dirs_unmounted(self, path):
        raise NotImplementedError
    
    def list_dir(self, path):
        return list(self.iter_dir(path))
    
    def iter_dir(self, path):
        raise NotImplementedError
    
    def mount(self, path, fs):
        absolute, components = normalize_split(path)
        self.mount_points[components] = fs
    
    def unmount(self, path):
        absolute, components = normalize_split(path)
        del self.mount_points[components]
    
    def get_mounted_fs(self, path):
        absolute, components = normalize_split(path)
        
        for i in range(len(components) + 1):
            prefix = components[:i]
            try:
                child_fs = self.mount_points[prefix]
                return child_fs.get_mounted_fs(components[i:])
            except KeyError:
                pass
        
        return self, path
    
    @classmethod
    def from_url(cls, url):
        return factory.create(FSFactory.INJECTION_KEY, url)


class FSFactory(factory.Factory):
    INJECTION_KEY = "nmapps.vfs.FSFactory"
    SCHEMES = ()
    
    def create(self, url, *args, **kwargs):
        parsed_url = urlparse.urlparse(url)
        if parsed_url.scheme not in self.SCHEMES:
            raise factory.FactoryException("Unsupported scheme: %s." % (parsed_url.scheme, ))
        try:
            create_meth = getattr(self, "create_scheme_%s" % (parsed_url.scheme, ))
        except AttributeError:
            raise factory.FactoryException("Unsupported scheme: %s." % (parsed_url.scheme, ))
        return create_meth(parsed_url, *args, **kwargs)


#### OSFileSystem ###################################################


class OSFileSystem(FileSystem):
    def __init__(self, url):
        FileSystem.__init__(self, url)
        self.path = fs.Path.make(url.path).abs
    
    def get_file_unmounted(self, path, root_fs = None):
        return OSFile(self, root_fs or self, path)


@injection.factory(FSFactory.INJECTION_KEY, "osfs")
class OSFSFactory(FSFactory):
    SCHEMES = ("file", )
    
    def create_scheme_file(self, url, *args, **kwargs):
        return OSFileSystem(url)


class OSFileContent(IContent):
    def read(self, vfile):
        return vfile.file.read()
    
    def write(self, vfile, content):
        return vfile.file.write(content)
    
    def read_stream(self, vfile):
        return vfile.file.open(mode = "r")
    
    def write_stream(self, vfile):
        return vfile.file.open(mode = "w")


class OSDirContent(IDirectoryContent):
    def list_iter(self, vfile):
        for p in vfile.os_path.iter_dir():
            pass


class OSFile(VirtualFile):
    @property
    def file(self):
        if self._file is None:
            self._file = fs.File(self.os_path)
        return self._file
    
    @property
    def os_path(self):
        return fs.Path.join(self.fs.path, *self.path[1])
    
    def __init__(self, fs, root_fs, path):
        path = normalize_split(path)
        
        VirtualFile.__init__(self, fs, root_fs, path[1][-1], OSFileContent(), OSDirContent())
        self.path = path
        
        self._file = None


#### MODULE #########################################################


def main():
    print __doc__


if __name__ == "__main__":
    main()

