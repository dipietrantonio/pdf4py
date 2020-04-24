import unittest
from .context import *
from pdf4py._decoders import ascii85decode, runlengthdecode, asciihexdecode
from binascii import hexlify


class DecodersTestCase(unittest.TestCase):


    def test_ascii85_decode(self):
        ascii85msg = b'6Z6LH+Co%nDe*F#+@/pn8P(m!~>'
        original = 'Code decodes ASCII85'.encode('ascii')
        self.assertEqual(original, ascii85decode(ascii85msg, None))

    
    def test_runlength_decode(self):
        rle = b'\x0bHello world.\x82c'
        decoded = b'Hello world.' + (257 - 130) * b'c'
        self.assertEqual(decoded, runlengthdecode(rle, None))


    def test_asciihexdecode(self):
        decoded = b"87cURD]i,\"Ebo80~>"
        encoded = b"3837635552445d692c2245626f38307e3e>"
        self.assertEqual(asciihexdecode(encoded, None), decoded)