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

logging.basicConfig(level=logging.DEBUG)

class ParseALatexPDFTest(unittest.TestCase):


    def test_read_header(self):
        self.assertTrue(False, "Impement me!")
    
    
    def test(self):
        with open(os.path.join(PDFS_FOLDER, "0000.pdf"), "rb") as fp:
            parser = parpkg.Parser(fp)
            for pdfXrefEntry in parser.xRefTable:
                parser.parse_xref_entry(pdfXrefEntry)

        self.assertFalse(True, "Implement me!")


if __name__ == "__main__":
    unittest.main()