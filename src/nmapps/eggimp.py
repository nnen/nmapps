#!/usr/bin/python

import os, os.path
import sys
import re


EGG_PATTERN = re.compile(r"([a-zA-Z0-9_]+)(\-([0-9]+((\.[0-9]+)?\.[0-9]+)?)(\-py([0-9]+\.[0-9]+)))?\.egg")


def get_exe_dir():
    import __main__
    d = getattr(__main__, "__file__", None)
    if d is None:
        return os.path.abspath(os.curdir)
    return os.path.dirname(os.path.abspath(d))


def compare_versions(v1, v2):
    for a, b in list(zip(v1, v2)):
        if a > b:
            return 1
        elif b < a:
            return -1
    
    if len(v1) > len(v2):
        return 1
    elif len(v1) < len(v2):
        return -1
    else:
        return 0


def find_eggs(dir = None):
    if dir is None:
        dir = get_exe_dir()
    
    eggs = (os.path.join(dir, x) for x in os.listdir(dir) if x.endswith(".egg"))
    eggs = [x for x in eggs if os.path.isfile(x)]
    
    return eggs


def add_to_import(index = 1, paths = None):
    if paths is None:
        paths = find_eggs()
    
    for path in reversed(paths):
        sys.path.insert(index, path)


add_to_import()


