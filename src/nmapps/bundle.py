# src/nmapps/bundle.py

from fs import Path


INIT_FILE = "__init__.py"


class Bundle(object):
    def __init__(self, pth):
        self.path = pth

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, str(self.path), )


class Egg(Bundle):
    @classmethod
    def is_egg(cls, pth):
        pth = Path.make(pth)
        
        if pth.extension.lower() <> "egg":
            return False
        if not pth.is_file:
            return False
        return True


def get_bundle(pth = "."):
    pth = Path.make(pth).real
    
    bundle = Bundle(pth)
    
    for parent in pth.iter_parents():
        if Egg.is_egg(parent):
            return Egg(parent)
        if (parent + INIT_FILE).is_file:
            bundle = Bundle(parent)
    
    return bundle


