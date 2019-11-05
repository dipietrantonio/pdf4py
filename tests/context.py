import os
import sys
BASE_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PDFS_FOLDER = os.path.join(BASE_FOLDER, "tests", "pdfs")
sys.path.insert(0, BASE_FOLDER)

import pdfpy._lexer as lexpkg
import pdfpy.parser as parpkg

