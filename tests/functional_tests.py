from .context import *
import unittest


class ParseALatexPDFTest(unittest.TestCase):

    def test(self):
        with open(os.path.join(PDFS_FOLDER, "0000.pdf"), "rb") as fp:
            parser = parpkg.PDFParser(fp)
            for pdfXrefEntry in parser.xrefTable:
                parser.parse_xref_entry(pdfXrefEntry)

        self.assertFalse(True, "Implement me!")


if __name__ == "__main__":
    unittest.main()