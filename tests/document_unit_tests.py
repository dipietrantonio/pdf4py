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
            page2 = doc.pages[2]
            self.assertIsInstance(page2, docpkg.Page)
                    
