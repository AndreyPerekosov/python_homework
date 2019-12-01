import unittest
import functools

from os import sys, path
sys.path.append(path.dirname(path.dirname(path.dirname(path.abspath(__file__)))))
from api import api


def fields_test_cases(cases):
    def decorator(func):
        @functools.wraps(func)
        def wraper(*args):
            for cl, values in cases:
                for value in values:
                    new_args = args + (cl,) + (value if isinstance(value, tuple) else (value,))
                    try:
                        func(*new_args)
                    except api.ValidationError as e:
                        print("Error in field %s with value %s - %s" % (cl, value, e))
                        raise e
        return wraper
    return decorator


class TestSuite(unittest.TestCase):

    def setUp(self):
        self.context = {}
        self.headers = {}
        self.store = None

    def get_response(self, request):
        return api.method_handler({"body": request, "headers": self.headers}, self.context, self.store)

    def test_empty_request(self):
        _, code = self.get_response({})
        self.assertEqual(api.INVALID_REQUEST, code)


class TestCharField(unittest.TestCase):
    @fields_test_cases([(api.CharField, ("", None,))])
    def test_set_ok_blank(self, *args):
        inst = args[0](nullable=True)
        inst.value = args[1]
        self.assertTrue(inst.validate(inst.value))

    @fields_test_cases([(api.CharField, ("test",))])
    def test_set_ok_filled(self, *args):
        inst = args[0](nullable=False)
        inst.value = args[1]
        self.assertTrue(inst.validate(inst.value))

    @fields_test_cases([(api.CharField, ("", None, 123))])
    def test_set_not_ok(self, *args):
        inst = args[0](nullable=False)
        self.assertRaises(Exception, inst.validate, args[1])


class TestArgumentsField(unittest.TestCase):
    @fields_test_cases([(api.ArgumentsField, ({}, None))])
    def test_set_ok_blank(self, *args):
        inst = args[0](nullable=True)
        inst.value = args[1]
        self.assertTrue(inst.validate(inst.value))

    @fields_test_cases([(api.ArgumentsField, ({1: 2},))])
    def test_set_ok_filled(self, *args):
        inst = args[0](nullable=False)
        inst.value = args[1]
        self.assertTrue(inst.validate(inst.value))

    @fields_test_cases([(api.ArgumentsField, ({}, None, ))])
    def test_set_not_ok(self, *args):
        inst = args[0](nullable=False)
        self.assertRaises(Exception, inst.validate, args[1])


class TestEmailField(unittest.TestCase):
    @fields_test_cases([(api.EmailField, ("", ))])
    def test_set_ok_blank(self, *args):
        inst = args[0](nullable=True)
        inst.value = args[1]
        self.assertTrue(inst.validate(inst.value))

    @fields_test_cases([(api.EmailField, ("test@ts.com",))])
    def test_set_ok_filled(self, *args):
        inst = args[0](nullable=False)
        inst.value = args[1]
        self.assertTrue(inst.validate(inst.value))

    @fields_test_cases([(api.EmailField, ("", None, "testts.com", 123))])
    def test_set_not_ok(self, *args):
        inst = args[0](nullable=False)
        self.assertRaises(Exception, inst.validate, args[1])


class TestPhoneField(unittest.TestCase):
    @fields_test_cases([(api.PhoneField, ("", None))])
    def test_set_ok_blank(self, *args):
        inst = args[0](nullable=True)
        inst.value = args[1]
        self.assertTrue(inst.validate(inst.value))

    @fields_test_cases([(api.PhoneField, (79857778767, "79167894534",))])
    def test_set_ok_filled(self, *args):
        inst = args[0](nullable=False)
        inst.value = args[1]
        self.assertTrue(inst.validate(inst.value))

    @fields_test_cases([(api.PhoneField, ("", None, "test", 798577, "7916789",))])
    def test_set_not_ok(self, *args):
        inst = args[0](nullable=False)
        self.assertRaises(Exception, inst.validate, args[1])


class TestDateField(unittest.TestCase):
    @fields_test_cases([(api.DateField, ("", None))])
    def test_set_ok_blank(self, *args):
        inst = args[0](nullable=True)
        inst.value = args[1]
        self.assertTrue(inst.validate(inst.value))

    @fields_test_cases([(api.DateField, ("01.01.2000",))])
    def test_set_ok_filled(self, *args):
        inst = args[0](nullable=False)
        inst.value = args[1]
        self.assertTrue(inst.validate(inst.value))

    @fields_test_cases([(api.DateField, ("", None, "01.01.20",))])
    def test_set_not_ok(self, *args):
        inst = args[0](nullable=False)
        self.assertRaises(Exception, inst.validate, args[1])


class TestBirthDayField(unittest.TestCase):
    @fields_test_cases([(api.BirthDayField, ("", None))])
    def test_set_ok_blank(self, *args):
        inst = args[0](nullable=True)
        inst.value = args[1]
        self.assertTrue(inst.validate(inst.value))

    @fields_test_cases([(api.BirthDayField, ("24.09.2010",))])
    def test_set_ok_filled(self, *args):
        inst = args[0](nullable=False)
        inst.value = args[1]
        self.assertTrue(inst.validate(inst.value))

    @fields_test_cases([(api.BirthDayField, ("24.2010", "01.01.1900", None, "",))])
    def test_set_not_ok(self, *args):
        inst = args[0](nullable=False)
        self.assertRaises(Exception, inst.validate, args[1])


class TestGenderField(unittest.TestCase):
    @fields_test_cases([(api.GenderField, ("", None))])
    def test_set_ok_blank(self, *args):
        inst = args[0](nullable=True)
        inst.value = args[1]
        self.assertTrue(inst.validate(inst.value))

    @fields_test_cases([(api.GenderField, (0, 1, 2,))])
    def test_set_ok_filled(self, *args):
        inst = args[0](nullable=False)
        inst.value = args[1]
        self.assertTrue(inst.validate(inst.value))

    @fields_test_cases([(api.GenderField, (3, 4, "", None))])
    def test_set_not_ok(self, *args):
        inst = args[0](nullable=False)
        self.assertRaises(Exception, inst.validate, args[1])


class TestClientIDsField(unittest.TestCase):
    @fields_test_cases([(api.ClientIDsField, (None, []))])
    def test_set_ok_blank(self, *args):
        inst = args[0](nullable=True)
        inst.value = args[1]
        self.assertTrue(inst.validate(inst.value))

    @fields_test_cases([(api.ClientIDsField, ([1, 2, 4],))])
    def test_set_ok_filled(self, *args):
        inst = args[0](nullable=False)
        inst.value = args[1]
        self.assertTrue(inst.validate(inst.value))

    @fields_test_cases([(api.ClientIDsField, ([], None, ["tes", "test", ""]))])
    def test_set_not_ok(self, *args):
        inst = args[0](nullable=False)
        self.assertRaises(Exception, inst.validate, args[1])


if __name__ == "__main__":
    unittest.main()
