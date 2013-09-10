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


class TestSplitCmd(unittest.TestCase):
    def test_none(self):
        self.assertEqual(len(app.split_cmd(None)), 0)
    
    def test_string_simple(self):
        res = app.split_cmd("some_string")
        self.assertEqual(res[0], "some_string")
    
    def test_string_qualified(self):
        res = app.split_cmd("namespace:command")
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0], "namespace")
        self.assertEqual(res[1], "command")


class TestJoinCmd(unittest.TestCase):
    def _test_string(self, string):
        res = app.join_cmd(string)
        self.assertEqual(res, string)
    
    def test_string(self):
        strings = [
            "simple_string",
            "namespace:command",
            "ctrl:child:cmd",
        ]
        for s in strings:
            self._test_string(s)
    
    def test_empty(self):
        res = app.join_cmd(tuple())
        self.assertEqual(res, "")
    
    def test_tuple(self):
        tuples = [
            (("a", "b", "c"), "a:b:c"), 
            (("namespace", "command"), "namespace:command"),
            (("single", ), "single"),
        ]
        for t, s in tuples:
            self.assertEqual(app.join_cmd(t), s)


class TestCommandApp(unittest.TestCase):
    def test_constructor(self):
        cmdapp = app.CommandApp()
    
    def test_default_cmds(self):
        cmdapp = app.CommandApp()
        cmdapp.execute_command("help")
        cmdapp.execute_command("list")


def main():
    print __doc__


if __name__ == "__main__":
    main()

