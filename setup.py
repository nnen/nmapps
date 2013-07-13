#!/usr/bin/python
# -*- coding: utf8 -*-

from setuptools import setup
import sys
import os
import os.path as path


os.chdir(path.realpath(path.dirname(__file__)))
sys.path.insert(1, 'src')
import nmapps


setup(
    name             = 'nmapps',
    version          = nmapps.__version__,
    author           = 'Jan Milík',
    author_email     = 'milikjan@fit.cvut.cz',
    description      = 'Personal toolbox for unix programs.',
    long_description = nmapps.__doc__,
    url              = 'http://pypi.python.org/pypi/nmapps',
    
    packages    = ['nmapps', ],
    package_dir = {'': 'src'},
    # py_modules  = ['nmapps'],
    provides    = ['nmapps'],
    keywords    = 'library unix application framework',
    license     = 'Lesser General Public License v3',
    
    #scripts     = ['src/scripts/eggimp.py', ],
    
    entry_points = {
        "console_scripts": ["nmapps = nmapps.tool:main", ],
    },
    
    #data_files  = [('', ['src/__main__.py', ]), ],
    
    test_suite = 'nmapps.tests',
    
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
        'Natural Language :: English',
        # 'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.6',
    ]
)

