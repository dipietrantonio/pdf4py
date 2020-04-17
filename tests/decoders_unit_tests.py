import unittest
from .context import *
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

