"""
MIT License

Copyright (c) 2019-2020 Cristian Di Pietrantonio (cristiandipietrantonio@gmail.com)

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
from pdf4py._decrypt import authenticate_user_password, decrypt


class RC4TestCase(unittest.TestCase):


    def test_rc4_encrypt(self):

        plain = b"Hello world!"
        expected_ciphertext = b"\x48\x9d\x12\x0b\x4b\x13\x62\xf3\x0d\x5b\x46\x97"
        key = b"123456"
        output = RC4.rc4(plain, key)
        self.assertEqual(output, expected_ciphertext)
        # convert back
        self.assertEqual(plain, RC4.rc4(output, key))



class DecryptFunctionsTestCase(unittest.TestCase):


    def test_authenticate_user_password(self):
        fp = open(os.path.join(PDFS_FOLDER, "0009.pdf"), "rb")
        parser = parpkg.Parser(fp)
        encryption_dict = parser.parse_xref_entry(parser.trailer["Encrypt"]).value
        value = authenticate_user_password(b"", encryption_dict, parser.trailer["ID"])
        self.assertTrue(value is not None)
        s = parser.parse_xref_entry(parpkg.PDFReference(48, 0)).value["URI"].value
        dec = decrypt(s, (48, 0), value, {})
        self.assertEqual(dec, b'http://www.education.gov.yk.ca/')
        fp.close()

    
    def test_autheticate_owner_password(self):
        self.assertFalse(True, "Implement me!")


if __name__ == "__main__":
    unittest.main()