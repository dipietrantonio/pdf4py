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
import unittest
from pdf4py._decoders import ascii85decode, runlengthdecode
from binascii import hexlify


class DecodersTestCase(unittest.TestCase):


    def test_ascii85_decode(self):
        ascii85msg = '<~6Z6LH+Co%nDe*F#+@/pn8P(m!~>'
        original = 'Code decodes ASCII85'.encode('ascii')
        self.assertEqual(original, ascii85decode(ascii85msg, None))

    
    def test_runlength_decode(self):
        rle = b'\x0bHello world.\x82c'
        decoded = b'Hello world.' + (257 - 130) * b'c'
        self.assertEqual(decoded, runlengthdecode(rle, None))

