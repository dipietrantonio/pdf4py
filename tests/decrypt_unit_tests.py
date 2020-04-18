import unittest
from .context import *
from pdf4py._security.securityhandler import authenticate_user_password, decrypt, sals_stringprep
from binascii import unhexlify



class RC4TestCase(unittest.TestCase):


    def test_rc4_encrypt(self):
        plain = b"Hello world!"
        expected_ciphertext = b"\x48\x9d\x12\x0b\x4b\x13\x62\xf3\x0d\x5b\x46\x97"
        key = b"123456"
        output = rc4pkg.rc4(plain, key)
        self.assertEqual(output, expected_ciphertext)
        # convert back
        self.assertEqual(plain, rc4pkg.rc4(output, key))



class DecryptFunctionsTestCase(unittest.TestCase):


    def test_decrypt_empty_password(self):
        fp = open(os.path.join(PDFS_FOLDER, "0009.pdf"), "rb")
        parser = parpkg.Parser(fp)
        encryption_dict = parser.parse_reference(parser.trailer["Encrypt"])
        id_array = [unhexlify(x.value) if isinstance(x, parpkg.PDFHexString) else x.value for x in parser.trailer["ID"]]
        value = authenticate_user_password(b"", encryption_dict, id_array)
        self.assertTrue(value is not None)
        s = parser.parse_reference(parpkg.PDFReference(48, 0))["URI"].value
        self.assertEqual(s, b'http://www.education.gov.yk.ca/')
        fp.close()


    def test_decrypt_aes_128(self):
        fp = open(os.path.join(ENCRYPTED_PDFS_FOLDER, "0017.pdf"), "rb")
        parser = parpkg.Parser(fp, b'foo')
        for x in parser.xreftable:
            parser.parse_reference(x)
        fp.close()


    def test_decrypt_aes_256(self):
        fp = open(os.path.join(ENCRYPTED_PDFS_FOLDER, "0021.pdf"), "rb")
        parser = parpkg.Parser(fp, 'foo')
        producer = parser.parse_reference(parser.xreftable[10, 0])['Producer'].value.decode('utf16')
        self.assertIn('LibreOffice', producer)
        fp.close()


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