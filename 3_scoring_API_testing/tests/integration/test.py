import unittest
from os import sys, path
import time
sys.path.append(path.dirname(path.dirname(path.dirname(path.abspath(__file__)))))
from api import store


class TestStore(unittest.TestCase):
    def test_set_ok(self):
        store.cache_set("test", 1.0, 10)
        self.assertEqual(1.0, store.cache_get("test"))

    def test_get_not_ok(self):
        store.cache_set("test", 1.0, 10)
        self.assertNotEqual(2.0, store.cache_get("test"))

    def test_delete(self):
        store.cache_set("test", 1.0, 10)
        store.delete("test")
        self.assertEqual(store.cache_get("test"), None)

    def test_out_of_time(self):
        store.cache_set("test", 1.0, 2)
        time.sleep(2)
        self.assertEqual(store.cache_get("test"), None)


if __name__ == "__main__":
    unittest.main()
