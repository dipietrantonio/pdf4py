from .context import *
import unittest
import logging
from binascii import unhexlify



def parse_object(parser, obj, visited):
    if isinstance(obj, parpkg.PDFStream):
        obj.stream()
        parse_object(parser, obj.dictionary, visited)
    elif isinstance(obj, parpkg.PDFHexString):
        unhexlify(obj.value)
    elif isinstance(obj, list):
        for x in obj:
            parse_object(parser, x, visited)
    elif isinstance(obj, dict):
        for k in obj:
            parse_object(parser, obj[k], visited)
    elif isinstance(obj, parpkg.PDFReference) and obj not in visited:
        visited.add(obj)
        x = parser.parse_reference(obj)
        parse_object(parser, x, visited)



def parse_file(filename):
    visited_references = set()
    with open(filename, "rb") as fp:
        parser = parpkg.Parser(fp)
        for pdfXrefEntry in parser.xreftable:
            x = parser.parse_reference(pdfXrefEntry)
            parse_object(parser, x, visited_references)
        


class ParseALatexPDFTest(unittest.TestCase):


    def test_read_header(self):
        with open(os.path.join(PDFS_FOLDER, "0000.pdf"), "rb") as fp:
            parser = parpkg.Parser(fp)
            self.assertEqual(parser.version, "PDF-1.4")
    

    def test_simple(self):
        parse_file(os.path.join(PDFS_FOLDER, "0000.pdf"))


    def test_more_complex_file(self):
        parse_file(os.path.join(PDFS_FOLDER, "0008.pdf"))


    def test_more_complex_file_2(self):
        parse_file(os.path.join(PDFS_FOLDER, "0009.pdf"))



class ParseEncryptedPDFTestCase(unittest.TestCase):
    

    def test_read(self):
        ENC_FILE = os.path.join(PDFS_FOLDER, "0009.pdf")
        fp = open(ENC_FILE, "rb")
        parser = parpkg.Parser(fp)
        self.assertIn("Encrypt", parser.trailer)
        enc_dict = parser.trailer["Encrypt"]
        if isinstance(enc_dict, parpkg.PDFReference):
            enc_dict = parser.parse_reference(enc_dict)
        self.assertIsInstance(enc_dict, dict)
        doc_info = parser.parse_reference(parser.xreftable[(6, 0)])
        self.assertIsInstance(doc_info, dict)
        self.assertIn(b'Acrobat', doc_info["Creator"].value)
        fp.close()



class ParseAllPDFs(unittest.TestCase):

    @unittest.skipUnless(RUN_ALL_TESTS, "debug_purposes")
    def test_all_pdfs(self):
        for pdfPath in os.listdir(PDFS_FOLDER):
            parse_file(os.path.join(PDFS_FOLDER, pdfPath))



class DocumentTestCase(unittest.TestCase):


    def test_print_document_catalog(self):
        with open(os.path.join(PDFS_FOLDER, "0000.pdf"), "rb") as fp:
            myPdfDoc = docpkg.Document(fp)
            self.assertEqual(len(myPdfDoc.pages), 10)


if __name__ == "__main__":
    unittest.main()