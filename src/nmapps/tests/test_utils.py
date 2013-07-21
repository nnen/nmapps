# src/nmapps/tests/test_usrexcept.py

import unittest

import nmapps.utils as utils


class TestArgsRepr(unittest.TestCase):
    def test_no_arguments(self):
        self.assertEqual(utils.args_repr(), "")
    
    def test_positional(self):
        self.assertEqual(utils.args_repr(1, 2, 3), "1, 2, 3")
        self.assertEqual(utils.args_repr(1, 2, 3, "abc"), "1, 2, 3, 'abc'")
    
    def test_keywords(self):
        self.assertEqual(utils.args_repr(kw1 = 1, kw2 = 2), "kw1 = 1, kw2 = 2")
    
    def test_both(self):
        self.assertEqual(utils.args_repr(1, 2, 3, "abc", kw1 = 1, kw2 = 2),
                         "1, 2, 3, 'abc', kw1 = 1, kw2 = 2")


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


class TestNull(unittest.TestCase):
    def setUp(self):
        self.null_obj = utils.Null()
    
    def test_constructor(self):
        n = utils.Null()
        n = utils.Null("value")
        n = utils.Null("arg1", "arg2", "arg3")
        n = utils.Null("arg1", "arg2", "arg3", kw_arg0 = 0, kw_arg1 = 1)
    
    def test_calling(self):
        self.null_obj()
        self.null_obj("arg")
        self.null_obj("arg0", "arg1")
        self.null_obj("arg0", "arg1", arg0 = "something")

    def test_attributes(self):
        self.null_obj.attr1
        self.null_obj.attr2
        
        self.null_obj.attr1.attr2.attr3
        
        self.null_obj.method()
        self.null_obj.method("value")
        self.null_obj.method1().method2()
        self.null_obj.method1("value").method2(1, 2, 3)
        
        self.null_obj.attr1.method()
        self.null_obj.attr1.method(1, 2, "abc")
        
        self.null_obj.attr1 = "value"
        self.assertFalse(self.null_obj.attr1)
        self.null_obj.attr1.attr2 = "value"
        self.assertFalse(self.null_obj.attr1.attr2)
        
        self.assertFalse(self.null_obj)
    
    def test_length(self):
        self.assertEqual(len(self.null_obj), 0)
    
    def test_iteration(self):
        for item in self.null_obj:
            self.fail("There should be no items in Null object.")
    
    def test_equality(self):
        self.assertEqual(self.null_obj, self.null_obj)
        self.assertEqual(self.null_obj, utils.Null())
        
        self.assertNotEqual(self.null_obj, 1)
        self.assertNotEqual(self.null_obj, "string")
        self.assertNotEqual(self.null_obj, object())
    
    def test_tests(self):
        self.assertFalse(self.null_obj)
        self.assertIsNotNone(self.null_obj)
    
    def test_hash(self):
        a = utils.Null()
        b = utils.Null()
        d = {}
        d[a] = "value"
        
        self.assertIn(a, d)
        self.assertIn(b, d)

    def test_string(self):
        n = utils.Null(1, 2, kwrd = "abc")

        self.assertEqual(repr(self.null_obj), "Null()")
        self.assertEqual(repr(n), "Null()")

        self.assertEqual(str(self.null_obj), "")
        self.assertEqual(str(n), "")


