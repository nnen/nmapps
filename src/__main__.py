#!/usr/bin/python
# __main__.py

from nmapps.fs import *
from nmapps import bundle


EGGIMP_PATH = "nmapps/eggimp.py"
EGGIMP = Path(EGGIMP_PATH).base


def main():
    egg = bundle.get_bundle()
    f = File("eggimp.py")
    
    if f.exists:
        print "%s already exists, exiting..." % (EGGIMP, )
        return
    
    res = egg.get_resource(EGGIMP_PATH)


if __name__ == "__main__":
    main()

