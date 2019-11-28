"""
MIT License

Copyright (c) 2019 Cristian Di Pietrantonio (cristiandipietrantonio@gmail.com)

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

# logging.basicConfig(level=logging.DEBUG)



class ParseAnnexHSamplesTest(unittest.TestCase):
    pass



class ParseALatexPDFTest(unittest.TestCase):


    @unittest.skipUnless(RUN_ALL_TESTS, "debug_purposes")
    def test_read_header(self):
        with open(os.path.join(PDFS_FOLDER, "0000.pdf"), "rb") as fp:
            parser = parpkg.Parser(fp)
            self.assertEqual(parser.version, "PDF-1.4")
    

    @unittest.skipUnless(RUN_ALL_TESTS, "debug_purposes")
    def test_simple(self):
        with open(os.path.join(PDFS_FOLDER, "0000.pdf"), "rb") as fp:
            parser = parpkg.Parser(fp)
            for pdfXrefEntry in parser.xRefTable:
                entity = parser.parse_xref_entry(pdfXrefEntry)



class ParseAllPDFs(unittest.TestCase):


    @unittest.skipUnless(RUN_ALL_TESTS, "debug_purposes")
    def test_all_pdfs(self):

        for pdfPath in os.listdir(PDFS_FOLDER):
            with open(os.path.join(PDFS_FOLDER, pdfPath), "rb") as fp:
                parser = parpkg.Parser(fp)
                for pdfXrefEntry in parser.xRefTable:
                    x = parser.parse_xref_entry(pdfXrefEntry)
                    if isinstance(x, parpkg.PDFIndirectObject):
                        x = x.value
                    if isinstance(x, parpkg.PDFStream):
                        x.stream()



class DocumentTestCase(unittest.TestCase):

    @unittest.skipUnless(RUN_ALL_TESTS, "debug_purposes")
    def test_print_document_catalog(self):
        with open(os.path.join(PDFS_FOLDER, "0000.pdf"), "rb") as fp:
            myPdfDoc = docpkg.Document(fp)
            self.assertEqual(len(myPdfDoc.pages), 10)

if __name__ == "__main__":
    unittest.main()