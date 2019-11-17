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
                    new_args = args + (cl,) + (value,)
                    func(*new_args)
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


class TestFields(unittest.TestCase):
    @fields_test_cases([(api.CharField, ("", "test", None)),
                        (api.ArgumentsField, ({}, {1: 2})),
                        (api.EmailField, ("test@ts.com", "")),
                        (api.PhoneField, (79857778767, "79167894534", "")),
                        (api.DateField, ("", "01.01.2000")),
                        (api.BirthDayField, ("24.09.2010", "")),
                        (api.GenderField, (0, 1, 2, None)),
                        (api.ClientIDsField, ([], None, [1, 2, 4])),
                        ])
    def test_set_ok_empty(self, *args):
        inst = args[0](nullable=True)
        inst.value = args[1]
        self.assertTrue(inst.validate(inst.value))

    @fields_test_cases([(api.CharField, ("", None, 123)),
                        (api.ArgumentsField, ((), None)),
                        (api.EmailField, ("testts.com", "", None)),
                        (api.PhoneField, (798577, "7916789", "", None)),
                        (api.DateField, ("", "01.01.20", None)),
                        (api.BirthDayField, ("24.2010", "", "01.01.1900", None)),
                        (api.GenderField, (3, 4, "", None)),
                        (api.ClientIDsField, ([], None, ["tes", "test", ""])),
                        ])
    def test_set_not_ok(self, *args):
        inst = args[0](nullable = False)
        self.assertRaises(Exception, inst.validate, args[1])


if __name__ == "__main__":
    unittest.main()
