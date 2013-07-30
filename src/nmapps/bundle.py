# src/nmapps/bundle.py

import sys

from fs import Path


INIT_FILE = "__init__.py"
MAIN_FILE = "__main__.py"
EGG_INFO_DIR = "EGG-INFO"
PKG_INFO_FILE = "PKG-INFO"


class Bundle(object):
    """Represents an abstraction over eggs, packages and modules."""
    
    def __init__(self, pth):
        self.path = pth
    
    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, str(self.path), )
    
    @classmethod
    def from_path(cls, pth = "."):
        pth = Path.make(pth).real
        
        # If the path itself is an egg, return an EGG bundle.
        if Egg.is_egg(pth):
            return Egg(pth)
        
        # If the path is a project file or a directory containing project file,
        # return a project.
        if pth.is_file and pth.base == Project.PROJECT_FILE:
            return Project(pth)
        if pth.is_dir and (pth + Project.PROJECT_FILE).is_file:
            return Project(pth + Project.PROJECT_FILE)
        
        # If the directory part of the path contains __init__.py file, assume
        # this is a package, otherwise it is a module (for now).
        in_package = False
        if (pth.dir + INIT_FILE).is_file:
            bundle_path = pth.dir
            in_package = True
        else:
            bundle_path = pth
        
        # Iterate over the parent directories from the innermost to outermost.
        for parent in pth.iter_parents():
            # If the parent is an egg, return an EGG bundle.
            if Egg.is_egg(parent):
                return Egg(parent)
            
            # Otherwise, if we're still in a package, check for __init__.py
            # file and remember the package path if there is one.
            if (parent + Project.PROJECT_FILE).is_file:
                bundle_path = parent + Project.PROJECT_FILE
            if in_package and (parent + INIT_FILE).is_file:
                bundle_path = parent
            else:
                in_package = False
        
        # By now, bundle_path is a directory only if it contains __init__.py as
        # wall as all subdirectories all the way back to the original path.
        # So, if bundle_path is a directory, the bundle is a package, otherwise
        # it is a module.
        if bundle_path.is_file and bundle_path.base == Project.PROJECT_FILE:
            return Project(bundle_path)
        if bundle_path.is_dir:
            return Package(bundle_path)
        return Module(bundle_path)


get_bundle = Bundle.from_path


class Module(Bundle):
    pass


class Package(Bundle):
    pass


class Egg(Bundle):
    @classmethod
    def is_egg(cls, pth):
        pth = Path.make(pth)
        
        if pth.is_file and pth.extension.lower() == "egg":
            return True
        
        if pth.is_dir:
            if ((pth + EGG_INFO_DIR) + PKG_INFO_FILE).is_file:
                return True
        
        return False


class Project(Bundle):
    PROJECT_FILE = "project.py"
    SETUP_FILE   = "setup.py"
    SOURCE_DIR   = "src"
    BUILD_DIR    = "build"
    DOC_DIR      = "doc"


def main(argv = None):
    argv = argv or []
    
    path = "."
    if len(argv) > 1:
        path = argv[1]
    path = Path(path).real
    
    bundle = get_bundle(path)
    
    print "Path: %s" % (path, )
    print "Bundle: %r" % (bundle, )


if __name__ == "__main__":
    main(sys.argv)


