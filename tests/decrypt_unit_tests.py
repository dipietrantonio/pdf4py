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
from .context import *
from pdf4py._security.securityhandler import authenticate_user_password, decrypt, sals_stringprep
from binascii import unhexlify



class RC4TestCase(unittest.TestCase):

    @unittest.skipUnless(RUN_ALL_TESTS, "debug_purposes")
    def test_rc4_encrypt(self):
        plain = b"Hello world!"
        expected_ciphertext = b"\x48\x9d\x12\x0b\x4b\x13\x62\xf3\x0d\x5b\x46\x97"
        key = b"123456"
        output = rc4pkg.rc4(plain, key)
        self.assertEqual(output, expected_ciphertext)
        # convert back
        self.assertEqual(plain, rc4pkg.rc4(output, key))



class DecryptFunctionsTestCase(unittest.TestCase):

    @unittest.skipUnless(RUN_ALL_TESTS, "debug_purposes")
    def test_decrypt_empty_password(self):
        fp = open(os.path.join(PDFS_FOLDER, "0009.pdf"), "rb")
        parser = parpkg.Parser(fp)
        encryption_dict = parser.parse_reference(parser.trailer["Encrypt"]).value
        id_array = [unhexlify(x.value) if isinstance(x, parpkg.PDFHexString) else x.value for x in parser.trailer["ID"]]
        value = authenticate_user_password(b"", encryption_dict, id_array)
        self.assertTrue(value is not None)
        s = parser.parse_reference(parpkg.PDFReference(48, 0)).value["URI"].value
        self.assertEqual(s, b'http://www.education.gov.yk.ca/')
        fp.close()


    @unittest.skipUnless(RUN_ALL_TESTS, "debug_purposes")
    def test_decrypt_aes_128(self):
        fp = open(os.path.join(ENCRYPTED_PDFS_FOLDER, "0017.pdf"), "rb")
        parser = parpkg.Parser(fp, b'foo')
        for x in parser.xreftable:
            parser.parse_reference(x)
        fp.close()


    @unittest.skipUnless(RUN_ALL_TESTS, "debug_purposes")
    def test_decrypt_aes_256(self):
        fp = open(os.path.join(ENCRYPTED_PDFS_FOLDER, "0021.pdf"), "rb")
        parser = parpkg.Parser(fp, 'foo')
        producer = parser.parse_reference(parser.xreftable[10, 0]).value['Producer'].value.decode('utf16')
        self.assertIn('LibreOffice', producer)
        fp.close()


    @unittest.skipUnless(RUN_ALL_TESTS, "debug_purposes")
    def test_decrypt_aes_256_m(self):
        fp = open(os.path.join(ENCRYPTED_PDFS_FOLDER, "0020.pdf"), "rb")
        with self.assertRaises(PDFGenericError):
            parser = parpkg.Parser(fp, b'foo')
        fp.close()



class StringPrepTestCase(unittest.TestCase):

    def test(self):
        self.assertEqual(sals_stringprep("I\u00ADX"), "IX")
        self.assertEqual(sals_stringprep("user"), "user")
        self.assertEqual(sals_stringprep("USER"), "USER")
        self.assertEqual(sals_stringprep("\u00AA"), "a")
        self.assertEqual(sals_stringprep("\u2168"), "IX")
        with self.assertRaises(PDFGenericError):
            sals_stringprep("\u0007")
        

if __name__ == "__main__":
    unittest.main()