import unittest
from .context import *
import os


class DocumentPageTreeTestCase(unittest.TestCase):
    """
    This test case comprises tests to verify the implementation of the
    page tree data structure to access PDF pages.
    """

    def test_page_tree_api(self):
        """
        Tests for the correct functioning of the page tree public interface.
        """
        with open(os.path.join(PDFS_FOLDER, "0004.pdf"), 'rb') as fp:
            doc = docpkg.Document(fp)
            self.assertIsInstance(doc.pages, docpkg.PageTree)
            self.assertEqual(len(doc.pages), 701)
            with self.assertRaises(KeyError):
                doc.pages[702]
            with self.assertRaises(KeyError):
                doc.pages[0]
            page2 = doc.pages[2]
            self.assertIsInstance(page2, docpkg.Page)
            self.assertEqual(page2.contents.object_number, 2)
            self.assertEqual(doc[701].contents.object_number, 1478)
            self.assertEqual(doc[700].contents.object_number, 1476)
            self.assertEqual(len(doc.pages), 701)
            self.assertEqual(len(doc), len(doc.pages))



class DocumentPageTestCase(unittest.TestCase):

    def test_basic_properties(self):
        with open(os.path.join(PDFS_FOLDER, "0004.pdf"), 'rb') as fp:
            doc = docpkg.Document(fp)
            test_page = doc[3]
            self.assertIsNone(test_page.last_modified)
            self.assertEqual(test_page.mediabox, [0, 0, 612, 792])
            self.assertEqual(test_page.rotate, 0)
            self.assertEqual(test_page.cropbox, test_page.mediabox)
            self.assertTrue(test_page.resources is not None)
            self.assertTrue(test_page.contents is not None)
        

    def test_inheritance(self):
        with open(os.path.join(PDFS_FOLDER, "0005.pdf"), 'rb') as fp:
            doc = docpkg.Document(fp)
            test_page = doc[1]
            self.assertEqual(test_page.mediabox, [0, 0, 595, 842])
            self.assertEqual(test_page.resources.object_number, 11)