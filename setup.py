#!/usr/bin/python
# -*- coding: utf8 -*-

# from distutils.core import setup
from setuptools import setup
import sys

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
	
	# test_suite = 'test.test_nmevent',
	
	classifiers = [
		'Development Status :: 3 - Alpha',
		'Intended Audience :: Developers',
		'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
		'Natural Language :: English',
		# 'Operating System :: OS Independent',
		'Programming Language :: Python :: 2.6',
	]
)

