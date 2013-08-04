#!/usr/bin/python
# -*- coding: utf-8 -*-
"""vfs module.

Author: Jan Milík <milikjan@fit.cvut.cz>
"""


import cStringIO as StringIO

from . import utils


class IContent(object):
    def read(self):
        raise NotImplementedError
    
    def write(self):
        raise NotImplementedError
    
    def read_stream(self):
        return StringIO.StringIO(self.read())
    
    def write_stream(self):
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
    def read(self):
        return ""
    
    def write(self, contents):
        # Do nothing.
        pass

NULL_CONTENT = NullContent()


class StringContent(IContent):
    def __init__(self, buffer):
        IContent.__init__(self)
        self.buffer = buffer
    
    def read(self):
        return self.buffer
    
    def write(self, contents):
        self.buffer = contents


class IDirectoryContent(object):
    def list(self):
        return list(self.list_iter())
    
    def list_iter(self):
        raise NotImplementedError
    
    def get_child(self, name):
        raise KeyError
    
    def mount(self, name, vfile):
        raise NotImplementedError

    def unmount(self, name):
        raise NotImplementedError


class NullDirContent(IDirectoryContent):
    def list_iter(self):
        if False:
            yield None
        return

    def mount(self, name, vfile):
        pass # Do nothing, Jon Snow

NULL_DIR_CONTENT = NullDirContent()


class DirContentBase(IDirectoryContent):
    def __init__(self):
        IDirectoryContent.__init__(self)
        self.mount_points = {}
        self.fallback = None
    
    def list_iter(self):
        visited = set()
        
        if self.mount_points:
            for name, child in self.moun_points.iteritems():
                visited.add(name)
                yield child
        
        if self.fallback:
            for child in self.fallback.list_iter():
                if not child.name in visited:
                    visited.add(child.name)
                    yield child
    
    def get_child(self, name):
        if self.mount_points:
            try:
                return self.mount_points[name]
            except KeyError:
                pass
        
        if self.fallback:
            return self.fallback.get_child(name)


class VirtualFile(object):
    def __init__(self, name, parent = None, content = None, dir_content = None):
        self.name = name
        self.parent = None
        
        self.content = content or NULL_CONTENT
        self.dir_content = dir_content or NULL_DIR_CONTENT
    
    def __repr__(self):
        return utils.obj_repr(self, self.name)
    
    def read(self):
        return self.content.read()
    
    def write(self, contents):
        self.content.write(contents)
    
    def get_child(self, name):
        return self.dir_content.get_child(name)
    
    def list(self):
        return self.dir_content.list()
    
    def list_iter(self):
        for item in self.dir_content.list_iter():
            yield item


class NullFile(VirtualFile):
    def __init__(self, name, parent = None):
        VirtualFile.__init__(self, name, parent)


def main():
    print __doc__


if __name__ == "__main__":
    main()

