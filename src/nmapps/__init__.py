#!/usr/bin/python
# -*- coding: utf-8 -*-
"""The nmapps package is a collection of utilities to help write unix
command-line application. 

Author: Jan Milík <milikjan@fit.cvut.cz>
"""


__version__ = "0.3dev"


from app import *
from daemon import *
from fs import *


def main():
    print __doc__


if __name__ == "__main__":
    main()

