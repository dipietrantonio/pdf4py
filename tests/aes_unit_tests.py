import unittest
from .context import *
from binascii import unhexlify



class AESTestCase(unittest.TestCase):


    def test_sub_bytes(self):
        self.assertTrue(sub_bytes([0x3a]) == [0x80])
    

    def test_shift_rows(self):
        state = [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]
        expected = [1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0]
        self.assertEqual(expected, shift_rows(state))


    def test_inv_shift_rows(self):
        expected = [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]
        state = [1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0]
        self.assertEqual(expected, inv_shift_rows(state))


    def test_xtime(self):
        self.assertEqual(xtime(xtime(xtime(xtime(0x57)))), 0x07)


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


    def test_expasion_key_128(self):
        ckey = unhexlify(b"2b7e151628aed2a6abf7158809cf4f3c")
        expected = unhexlify(
            b"2b7e151628aed2a6abf7158809cf4f3c"
            b"a0fafe1788542cb123a339392a6c7605"
            b"f2c295f27a96b9435935807a7359f67f"
            b"3d80477d4716fe3e1e237e446d7a883b"
            b"ef44a541a8525b7fb671253bdb0bad00"
            b"d4d1c6f87c839d87caf2b8bc11f915bc"
            b"6d88a37a110b3efddbf98641ca0093fd"
            b"4e54f70e5f5fc9f384a64fb24ea6dc4f"
            b"ead27321b58dbad2312bf5607f8d292f"
            b"ac7766f319fadc2128d12941575c006e"
            b"d014f9a8c9ee2589e13f0cc8b6630ca6"
            )
        self.assertEqual(bytes(key_expansion(ckey)), expected)

    
    def test_expasion_key_196(self):
        ckey =     unhexlify(b"000102030405060708090a0b0c0d0e0f1011121314151617")
        expected = unhexlify(
            b"000102030405060708090a0b0c0d0e0f"
            b"10111213141516175846f2f95c43f4fe"
            b"544afef55847f0fa4856e2e95c43f4fe"
            b"40f949b31cbabd4d48f043b810b7b342"
            b"58e151ab04a2a5557effb5416245080c"
            b"2ab54bb43a02f8f662e3a95d66410c08"
            b"f501857297448d7ebdf1c6ca87f33e3c"
            b"e510976183519b6934157c9ea351f1e0"
            b"1ea0372a995309167c439e77ff12051e"
            b"dd7e0e887e2fff68608fc842f9dcc154"
            b"859f5f237a8d5a3dc0c02952beefd63a"
            b"de601e7827bcdf2ca223800fd8aeda32"
            b"a4970a331a78dc09c418c271e3a41d5d"
        )
        self.assertEqual(bytes(key_expansion(ckey)), expected)


    def test_expasion_key_256(self):
        ckey =     unhexlify(b"000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f")
        expected = unhexlify(
            b"000102030405060708090a0b0c0d0e0f"
            b"101112131415161718191a1b1c1d1e1f"
            b"a573c29fa176c498a97fce93a572c09c"
            b"1651a8cd0244beda1a5da4c10640bade"
            b"ae87dff00ff11b68a68ed5fb03fc1567"
            b"6de1f1486fa54f9275f8eb5373b8518d"
            b"c656827fc9a799176f294cec6cd5598b"
            b"3de23a75524775e727bf9eb45407cf39"
            b"0bdc905fc27b0948ad5245a4c1871c2f"
            b"45f5a66017b2d387300d4d33640a820a"
            b"7ccff71cbeb4fe5413e6bbf0d261a7df"
            b"f01afafee7a82979d7a5644ab3afe640"
            b"2541fe719bf500258813bbd55a721c0a"
            b"4e5a6699a9f24fe07e572baacdf8cdea"
            b"24fc79ccbf0979e9371ac23c6d68de36"
        )
        self.assertEqual(bytes(key_expansion(ckey)), expected)

    

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



    def test_cbc_encryption(self):
        key = unhexlify(b"2b7e151628aed2a6abf7158809cf4f3c")
        iv = bytes([0] * 16)
        message = bytes(x for x in range(64))
        self.assertEqual(message, cbc_decrypt(cbc_encrypt(message, key, iv), key, iv)[:len(message)])


    def test_cbc_encryption_256_key(self):
        key = bytes(range(32))
        iv = bytes(range(16))
        from binascii import hexlify
        message = bytes(i  % 256 for i in range(64))
        # Not working
        cypher = cbc_encrypt(message, key, iv, padding = False)
        decry = cbc_decrypt(cypher, key, iv, padding = False)
        self.assertEqual(message, decry)


if __name__ == "__main__":
    unittest.main()