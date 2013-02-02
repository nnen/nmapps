# src/nmapps/tests/test_usrexcept.py

import unittest

import nmapps.utils as utils


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


