# src/nmapps/tests/test_usrexcept.py

import unittest

import nmapps.utils as utils


class TestPrefixDict(unittest.TestCase):
    def test_setitem(self):
        prefd = utils.PrefixDict()
        prefd["hello"] = 0
        prefd["hell"]  = 1
        prefd["abc"]   = 2
    
    def test_getitem(self):
        prefd = utils.PrefixDict()
        prefd["hello"] = 0
        prefd["hell"]  = 1
        prefd["abc"]   = 2

        self.assertEqual(1, len(prefd["hello"]))
        self.assertEqual(2, len(prefd["hell"]))
        self.assertEqual(2, len(prefd["hel"]))
        self.assertEqual(2, len(prefd["he"]))
        self.assertEqual(2, len(prefd["h"]))
        self.assertEqual(1, len(prefd["abc"]))
        self.assertEqual(1, len(prefd["ab"]))
        self.assertEqual(1, len(prefd["a"]))
        
        self.assertIn("hello", prefd)
        self.assertIn("hell",  prefd)
        self.assertIn("hel",   prefd)
        self.assertIn("he",    prefd)
        self.assertIn("h",     prefd)
        self.assertIn("abc",   prefd)
        self.assertIn("ab",    prefd)
        self.assertIn("a",     prefd)


class TestUserException(unittest.TestCase):
    def test_inner_exception(self):
        class A(Exception):
            pass
        
        try:
            try:
                raise A()
            except A as a:
                raise utils.UserException(inner = a)
        except utils.UserException as e:
            self.assertIsNotNone(e.inner_exception)
            self.assertIsNotNone(e.inner_exception.exc_info)
            self.assertIsNotNone(e.inner_exception.exc_info[2])


