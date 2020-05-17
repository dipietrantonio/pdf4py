import unittest
from pdf4py.datastructures import parse_date
from datetime import datetime, timezone, timedelta

class StringTestCase(unittest.TestCase):
    """
    Gonna leave this one for last.
    """



class DateTestCase(unittest.TestCase):

    def test_date_one(self):
        encoded = "D:199812231952-08'00"
        result = datetime(1998, 12, 23, 19, 52, tzinfo = timezone(-timedelta(hours=8)))
        self.assertEqual(parse_date(encoded), result)





if __name__ == "__main__":
    unittest.main()