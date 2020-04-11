"""
MIT License

Copyright (c) 2019 Cristian Di Pietrantonio (cristiandipietrantonio[AT]gmail.com)

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