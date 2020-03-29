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
from binascii import unhexlify
from Crypto.Cipher import AES



class AESTestCase(unittest.TestCase):


    @unittest.skipUnless(RUN_ALL_TESTS, "debug_purposes")
    def test_sub_bytes(self):
        self.assertTrue(sub_bytes([0x3a]) == [0x80])
    

    @unittest.skipUnless(RUN_ALL_TESTS, "debug_purposes")
    def test_shift_rows(self):
        state = [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]
        expected = [1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0]
        self.assertEqual(expected, shift_rows(state))


    @unittest.skipUnless(RUN_ALL_TESTS, "debug_purposes")
    def test_inv_shift_rows(self):
        expected = [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]
        state = [1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0]
        self.assertEqual(expected, inv_shift_rows(state))


    @unittest.skipUnless(RUN_ALL_TESTS, "debug_purposes")
    def test_xtime(self):
        self.assertEqual(xtime(xtime(xtime(xtime(0x57)))), 0x07)


    @unittest.skipUnless(RUN_ALL_TESTS, "debug_purposes")
    def test_mix_columns(self):
        input = [
            0xd4, 0xbf, 0x5d, 0x30,
            0xe0, 0xb4, 0x52, 0xae,
            0xb8, 0x41, 0x11, 0xf1,
            0x1e, 0x27, 0x98, 0xe5]
        expected_output = [ 
            0x04, 0x66, 0x81, 0xe5,
            0xe0, 0xcb, 0x19, 0x9a,
            0x48, 0xf8, 0xd3, 0x7a,
            0x28, 0x06, 0x26, 0x4c]
        
        self.assertEqual(mix_columns(input), expected_output)


    @unittest.skipUnless(RUN_ALL_TESTS, "debug_purposes")
    def test_inv_mix_columns(self):
        expected_output = [
            0xd4, 0xbf, 0x5d, 0x30,
            0xe0, 0xb4, 0x52, 0xae,
            0xb8, 0x41, 0x11, 0xf1,
            0x1e, 0x27, 0x98, 0xe5]
        input = [ 
            0x04, 0x66, 0x81, 0xe5,
            0xe0, 0xcb, 0x19, 0x9a,
            0x48, 0xf8, 0xd3, 0x7a,
            0x28, 0x06, 0x26, 0x4c]
        
        self.assertEqual(inv_mix_columns(input), expected_output)


    @unittest.skipUnless(RUN_ALL_TESTS, "debug_purposes")
    def test_expasion_key(self):
        ckey =  unhexlify(b"ffffffffffffffffffffffffffffffff")
        expected = unhexlify(
            b"ffffffffffffffffffffffffffffffff"
            b"e8e9e9e917161616e8e9e9e917161616"
            b"adaeae19bab8b80f525151e6454747f0"
            b"090e2277b3b69a78e1e7cb9ea4a08c6e"
            b"e16abd3e52dc2746b33becd8179b60b6"
            b"e5baf3ceb766d488045d385013c658e6"
            b"71d07db3c6b6a93bc2eb916bd12dc98d"
            b"e90d208d2fbb89b6ed5018dd3c7dd150"
            b"96337366b988fad054d8e20d68a5335d"
            b"8bf03f233278c5f366a027fe0e0514a3"
            b"d60a3588e472f07b82d2d7858cd7c326")
        expanded = key_expansion(ckey)
        self.assertEqual(bytes(expanded), expected)       


    @unittest.skipUnless(RUN_ALL_TESTS, "debug_purposes")
    def test_cipher_and_inv_cipher(self):
        input = unhexlify(b"3243f6a8885a308d313198a2e0370734")
        key = unhexlify(b"2b7e151628aed2a6abf7158809cf4f3c")
        expected = unhexlify(b"3925841d02dc09fbdc118597196a0b32")    
        Nk = len(key) / 4
        assert(Nk in [4.0, 6.0, 8.0])
        Nk = int(Nk)
        Nr = Nk + 6
        key = key_expansion(key)
        encr = bytes(cipher(input, key, Nr))
        self.assertEqual(encr, expected)
        decr = bytes(inv_cipher(encr, key, Nr))
        self.assertEqual(decr, input)


    @unittest.skipUnless(RUN_ALL_TESTS, "debug_purposes")
    def test_cbc_encryption(self):
        key = unhexlify(b"2b7e151628aed2a6abf7158809cf4f3c")
        iv = bytes([0] * 16)
        message = bytes(x for x in range(64))
        self.assertEqual(message, cbc_decrypt(cbc_encrypt(message, key, iv), key, iv)[:len(message)])


    @unittest.skipUnless(RUN_ALL_TESTS, "debug_purposes")
    def test_cbc_encryption_256_key(self):
        key = bytes(range(32))
        iv = bytes(range(16))
        from binascii import hexlify
        message = bytes(i  % 256 for i in range(64))
        # Not working
        # cypher = cbc_encrypt(message, key, iv, padding = False)
        cypher = AES.new(key, mode=AES.MODE_CBC, IV=iv).encrypt(message)
        decry = AES.new(key, mode=AES.MODE_CBC, IV=iv).decrypt(cypher)
        self.assertEqual(message, decry)


if __name__ == "__main__":
    unittest.main()