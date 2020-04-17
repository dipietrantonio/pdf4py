import os
import sys
import logging

BASE_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PDFS_FOLDER = os.path.join(BASE_FOLDER, "tests", "pdfs")
ENCRYPTED_PDFS_FOLDER = os.path.join(BASE_FOLDER, "tests", "encrypted_pdfs")
sys.path.insert(0, BASE_FOLDER)
logging.basicConfig(level=logging.INFO)

import pdf4py._lexer as lexpkg
import pdf4py.parser as parpkg
import pdf4py._document as docpkg
import pdf4py._security.rc4 as rc4pkg
from pdf4py._security.aes import *
from pdf4py._decoders import tiff_predictor
from pdf4py.exceptions import *

RUN_ALL_TESTS = True if os.environ.get("RUN_ALL_TESTS", "True") == "True" else False