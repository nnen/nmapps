#!/usr/bin/python
# -*- coding: utf-8 -*-
"""nmapps.tests.test_app module.

Author: Jan Milík <milikjan@fit.cvut.cz>
"""


import unittest

import nmapps.app as app


class TestAppBase(unittest.TestCase):
    def test_constructor(self):
        app_inst = app.AppBase()


class TestCommandApp(unittest.TestCase):
    def test_constructor(self):
        cmdapp = app.CommandApp()


def main():
    print __doc__


if __name__ == "__main__":
    main()

