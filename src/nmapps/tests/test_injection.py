# src/nmapps/tests/test_injection.py


import unittest
import sys
import logging

logging.basicConfig(level = logging.DEBUG, filename = "test_injection.log")

import nmapps.injection as injection


class TestPackage(unittest.TestCase):
    def setUp(self):
        injection.clear()
    
    def tearDown(self):
        injection.clear()
    
    def test_select_unset(self):
        """Selecting unset dependencies by name."""
        injection.select("unset-dependency", "named-alternative")
        
        value = object()
        
        injection.set("unset-dependency", value, name = "named-alternative")
        injection.set("unset-dependency", object())
        
        self.assertIs(injection.get("unset-dependency"), value)
    
    def test_select_fallback(self):
        """If a named alternative is selected, but not set, the manager falls
        back to the last alternative set."""
        
        injection.select("dependency", "named-alternative")
        
        injection.set("dependency", object())
        injection.set("dependency", object())
        
        self.assertIsNotNone(injection.get("dependency"))
    
    def test_get_unknown(self):
        """Retrieving unset dependencies raises exception."""
        with self.assertRaises(injection.DependencyException):
            unknown = injection.get("unknown-dependency")
    
    def test_typical_usage(self):
        """Test the typical usage as shown in the package docs."""
        # Notice that ImportantClass doesn't ever mention the DefaultDelegate
        # class.
        class ImportantClass(object):
            def do_stuff(self):
                delegate_cls = injection.get("mypackage.ImportantClass.delegate")
                if not delegate_cls:
                    raise Exception
                return delegate_cls().do_stuff()
        
        # And the DefaultDelegate class can provide its services without mentioning
        # the ImportantClass.
        @injection.provide("mypackage.ImportantClass.delegate", "default")
        class DefaultDelegate(object):
            def do_stuff(self):
                return "Hello World!"
        
        # Yet, by default, the work together. 
        obj = ImportantClass()
        result = obj.do_stuff()
        self.assertEqual(result, "Hello World!")


class TestDefaultDependencyManager(unittest.TestCase):
    """Tests the nmapps.injection.DefaultDependencyManager class."""
    
    def setUp(self):
        self.manager = injection.DefaultDependencyManager()

    def tearDown(self):
        self.manager = None
    
    def test_get_unknown(self):
        """Retrieving unset dependencies raises exception."""
        
        with self.assertRaises(injection.DependencyException):
            unknown = self.manager.get("unknown-dependency")
    
    def test_select_unset(self):
        """Selecting unset dependencies by name."""
        
        self.manager.select("unset-dependency", "named-alternative")
        
        # Selecting named alternative shouldn't actually set the value of the
        # dependency
        with self.assertRaises(injection.DependencyException):
            value = self.manager.get("unset-dependency")
        
        dependency = object()
        self.manager.set("unset-dependency", dependency, name = "named-alternative")
        
        alternative = object()
        self.manager.set("unset-dependency", alternative, name = "other-name") 
        
        alternative = object()
        self.manager.set("unset-dependency", alternative) 
        
        # After selecting a named alternative and subsequently providing value
        # for that alternative, it should be obtainable simply by providing the
        # dependency key.
        self.assertIs(self.manager.get("unset-dependency"), dependency)
    
    def test_select_unset_b(self):
        """If a named alternative is selected, but not set, the manager falls
        back to the last alternative set."""
        
        self.manager.select("dependency", "named-alternative")
        
        self.manager.set("dependency", object())
        self.manager.set("dependency", object())
        
        value = object()
        self.manager.set("dependency", value)
        
        dependency = self.manager.get("dependency")
        
        self.assertIsNotNone(dependency)
        self.assertIs(dependency, value)


