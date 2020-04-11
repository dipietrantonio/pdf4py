"""
MIT License

Copyright (c) 2019-2020 Cristian Di Pietrantonio (cristiandipietrantonio[AT]gmail.com)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from .context import *
import unittest
import logging


def parse_file(filename):
    with open(filename, "rb") as fp:
        parser = parpkg.Parser(fp)
        for pdfXrefEntry in parser.xreftable:
            x = parser.parse_reference(pdfXrefEntry)
            if isinstance(x, parpkg.PDFIndirectObject):
                x = x.value
            if isinstance(x, parpkg.PDFStream):
                try:
                    x.stream()
                except Exception:
                    raise


class ParseALatexPDFTest(unittest.TestCase):


    @unittest.skipUnless(RUN_ALL_TESTS, "debug_purposes")
    def test_read_header(self):
        with open(os.path.join(PDFS_FOLDER, "0000.pdf"), "rb") as fp:
            parser = parpkg.Parser(fp)
            self.assertEqual(parser.version, "PDF-1.4")
    

    @unittest.skipUnless(RUN_ALL_TESTS, "debug_purposes")
    def test_simple(self):
        parse_file(os.path.join(PDFS_FOLDER, "0000.pdf"))


    @unittest.skipUnless(RUN_ALL_TESTS, "debug_purposes")
    def test_more_complex_file(self):
        parse_file(os.path.join(PDFS_FOLDER, "0008.pdf"))


    @unittest.skipUnless(RUN_ALL_TESTS, "debug_purposes")
    def test_more_complex_file(self):
        parse_file(os.path.join(PDFS_FOLDER, "0009.pdf"))



class ParseEncryptedPDFTestCase(unittest.TestCase):
    
    @unittest.skipUnless(RUN_ALL_TESTS, "debug_purposes")
    def test_read(self):
        ENC_FILE = os.path.join(PDFS_FOLDER, "0009.pdf")
        fp = open(ENC_FILE, "rb")
        parser = parpkg.Parser(fp)
        self.assertIn("Encrypt", parser.trailer)
        enc_dict = parser.trailer["Encrypt"]
        if isinstance(enc_dict, parpkg.PDFReference):
            enc_dict = parser.parse_reference(enc_dict).value
        self.assertIsInstance(enc_dict, dict)
        doc_info = parser.parse_reference(parser.xreftable[(6, 0)]).value
        self.assertIsInstance(doc_info, dict)
        self.assertIn(b'Acrobat', doc_info["Creator"].value)
        fp.close()



class ParseAllPDFs(unittest.TestCase):

    @unittest.skipUnless(RUN_ALL_TESTS, "debug_purposes")
    def test_all_pdfs(self):
        for pdfPath in os.listdir(PDFS_FOLDER):
            parse_file(os.path.join(PDFS_FOLDER, pdfPath))


class DocumentTestCase(unittest.TestCase):

    @unittest.skipUnless(RUN_ALL_TESTS, "debug_purposes")
    def test_print_document_catalog(self):
        with open(os.path.join(PDFS_FOLDER, "0000.pdf"), "rb") as fp:
            myPdfDoc = docpkg.Document(fp)
            self.assertEqual(len(myPdfDoc.pages), 10)

if __name__ == "__main__":
    unittest.main()