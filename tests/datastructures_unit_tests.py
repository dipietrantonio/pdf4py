import unittest
from datetime import datetime, timezone, timedelta
from .context import *
import os


class StringTestCase(unittest.TestCase):
    """
    Gonna leave this one for last.
    """



class DateTestCase(unittest.TestCase):

    def test_date_one(self):
        encoded = "D:199812231952-08'00"
        result = datetime(1998, 12, 23, 19, 52, tzinfo = timezone(-timedelta(hours=8)))
        self.assertEqual(dsmod.parse_date(encoded), result)



class NameTreeTestCase(unittest.TestCase):

    def test_root_with_only_values(self):
        with open(os.path.join(PDFS_FOLDER, "0004.pdf"), "rb") as fp:
            p = parpkg.Parser(fp)
            root = p.parse_reference(p.trailer['Root'])
            nt_ref = p.parse_reference(p.parse_reference(root['Names'])['AP'])
            nt = dsmod.NameTree(p, nt_ref)
            val = nt[typesmod.PDFLiteralString(b'\xfe\xff\x00~\x00i\x00c\x00o\x00n\x00+\x00C\x00o\x00m\x00m\x00e\x00n\x00t\x00+\x002\x005\x005\x00:\x002\x005\x005\x00:\x000\x00-\x00E\x00N\x00U\x00-\x000')]
            self.assertEqual(val, parpkg.PDFReference(object_number=1483, generation_number=0))
            with self.assertRaises(KeyError):
                nt[typesmod.PDFLiteralString(b"unexisting string")]


    def test_methods_and_ref_as_key(self):
        with open(os.path.join(PDFS_FOLDER, "0004.pdf"), "rb") as fp:
            p = parpkg.Parser(fp)
            root = p.parse_reference(p.trailer['Root'])
            nt_ref = p.parse_reference(p.parse_reference(root['Names'])['IDS'])
            nt = dsmod.NameTree(p, nt_ref)
            val = nt[typesmod.PDFLiteralString(value=b'P2=\xf2w\xee\x13\xf8\xfey\xb63\x91\x94\xbct')]
            self.assertEqual(val, parpkg.PDFReference(object_number=1614, generation_number=0))
            self.assertIsNone(nt.get(typesmod.PDFLiteralString(b"unexisting string")))
            self.assertFalse(nt.get(typesmod.PDFLiteralString(b"unexisting string")))
            


class NumberTreeTestCase(unittest.TestCase):


    def test_root_with_only_values(self):
        with open(os.path.join(PDFS_FOLDER, "0008.pdf"), "rb") as fp:
            p = parpkg.Parser(fp)
            root = p.parse_reference(p.trailer['Root'])
            nt_ref = p.parse_reference(root['PageLabels'])
            nt = dsmod.NumberTree(p, nt_ref)
            val = nt[0]
            self.assertEqual(val, PDFReference(object_number=106, generation_number=0))
            with self.assertRaises(KeyError):
                nt[1]



if __name__ == "__main__":
    unittest.main()