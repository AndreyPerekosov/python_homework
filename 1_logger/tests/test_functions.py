import unittest
import os
import shutil
from datetime import datetime as dt

# adding absolute path to sys.path for possibility import tested functions from ../service

if __name__ == '__main__' and __package__ is None:
    from os import sys, path
    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from src.service import service as sr


def template_generate(start, ext):
    """
    The function generates list of test files for SearchLastFileTest class
    """

    dt_template = dt.now()
    dates = []

    for index in range(1, 10):
        date = dt_template.replace(month=index)
        dates.append(date.strftime("%Y%m%d"))
    files = []

    for date in dates:
        files.append(f"{start}{date}{ext}")

    return files


class SearchLastFileTest(unittest.TestCase):

    _dir = "./log"
    _file_prt = {"start": "nginx-access-ui.log-", "ext": ".gz"}
    _file_pattern = r'nginx-access-ui\.log-[0-9]{8}\.(gz|plain)'

    def setUp(self):

        os.makedirs(self._dir)
        files = template_generate(self._file_prt["start"],
                                  self._file_prt["ext"])
        for file in files:
            path = os.path.join(self._dir, file)
            with open(path, "w") as file:
                pass
        self.fixture = os.path.join(self._dir, files[-1])

    def tearDown(self):
        shutil.rmtree(self._dir)

    def testEqual(self):
        srch_file = sr.search_last_file(self._file_pattern, self._dir)
        self.failUnlessEqual(srch_file.path, self.fixture)


class ParserTest(unittest.TestCase):

    _path = ("test.gz")

    def setUp(self):
        self.fixture = ("/api/v2/banner/25019354", 0.390)

    def testEqual(self):
        generator = sr.parser(self._path, "gz", [0])
        test_string = next(generator)
        self.failUnlessEqual(test_string, self.fixture)


if __name__ == '__main__':
    unittest.main()
