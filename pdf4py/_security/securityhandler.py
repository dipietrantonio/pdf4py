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
from itertools import takewhile, chain
from hashlib import md5
from binascii import unhexlify
from ..exceptions import PDFUnsupportedError, PDFWrongPasswordError
from .rc4 import rc4
from ..types import PDFHexString, PDFLiteralString


PASSWORD_PADDING = b"\x28\xBF\x4E\x5E\x4E\x75\x8A\x41\x64\x00\x4E\x56\xFF\xFA\x01\x08\x2E\x2E\x00\xB6"\
    b"\xD0\x68\x3E\x80\x2F\x0C\xA9\xFE\x64\x53\x69\x7A"


def compute_encryption_key(password : 'bytes', encryption_dict : 'dict', id_array : 'list'):
    """
    Derives the key to be used with encryption/decryption algorithms from a user-defined password.
    Parameters
    ----------
    password : bytes
        Bytes representation of the password string.
    
    encryption_dict : dict
        The dictionary containing all the information about the encryption procedure.
    
    Returns
    -------
    A bytes sequence representing the encryption key.
    """
    R = encryption_dict["R"]
    O = encryption_dict["O"]
    V = encryption_dict.get("V", 0)
    O = O.value if isinstance(O, PDFLiteralString) else unhexlify(O.value)

    if V == 3:
        raise PDFUnsupportedError("An unknown algorithm has been used to encrypt the document.")

    Length = encryption_dict.get("Length", 40)
    if Length % 8 != 0:
        # TODO: better exception handling
        raise Exception()
    Length = Length // 8
    input_to_md5 = bytearray()
    input_to_md5.extend((password + PASSWORD_PADDING)[:32])
    input_to_md5.extend(O)
    input_to_md5.extend(encryption_dict["P"].to_bytes(4, byteorder='little', signed = True))
    input_to_md5.extend(unhexlify(id_array[0].value))
    if R >= 4 and encryption_dict.get("EncryptMetadata", True):
        input_to_md5.extend(b"\xFF\xFF\xFF\xFF")
    computed_hash = md5(input_to_md5).digest()
    if R >= 3:
        for i in range(50):
            computed_hash = md5(computed_hash[:Length]).digest()
    
    encryption_key = computed_hash[:Length]
    return encryption_key



def authenticate_user_password(password : 'bytes', encryption_dict : 'dict', id_array : 'list'):
    """
    Authenticate the user password.
    Parameters
    ----------
    password : bytes
        The password to be authenticated as user password.
    
    encryption_dict : dict
        The dictionary containing all the information about the encryption procedure.
    id_array : list
        The two elements array ID, contained in the trailer dictionary.
    
    Returns
    -------
    The encryption key if the user password is valid, None otherwise.
    """
    R = encryption_dict["R"]
    U = encryption_dict["U"]
    U = U.value if isinstance(U, PDFLiteralString) else unhexlify(U.value)
    encryption_key = compute_encryption_key(password, encryption_dict, id_array)
    if R == 2:
        cipher = rc4(PASSWORD_PADDING, encryption_key)
    else:
        input_to_md5 = bytearray()
        input_to_md5.extend(PASSWORD_PADDING)
        input_to_md5.extend(unhexlify(id_array[0].value))
        computed_hash = md5(input_to_md5).digest()
        cipher = rc4(computed_hash, encryption_key)
        for counter in range(1, 20):
            cipher = rc4(cipher, bytes(x ^ counter for x in encryption_key))
  
    correct_password = (U[:16] == cipher[:16]) if R >= 3 else (U == cipher)
    return encryption_key if correct_password else None



def authenticate_owner_password(password : 'bytes', encryption_dict : 'dict', id_array : 'list'):
    """
    Authenticate the owner password.
    Parameters
    ----------
    password : bytes
        The password to be authenticated as owner password.
    
    encryption_dict : dict
        The dictionary containing all the information about the encryption procedure.
    id_array : list
        The two elements array ID, contained in the trailer dictionary.
    
    Returns
    -------
    The encryption key if the owner password is valid, None otherwise.
    """
    Length = encryption_dict.get("Length", 40)
    if Length % 8 != 0:
        # TODO: better exception handling
        raise Exception()
    Length = Length // 8
    R = encryption_dict["R"]
    O = encryption_dict["O"]
    O = O.value if isinstance(O, PDFLiteralString) else unhexlify(O.value)
    input_to_md5 = bytearray()
    input_to_md5.extend((password + PASSWORD_PADDING)[:32])
    input_to_md5 = md5(input_to_md5).digest()
    if R >= 3:
        for i in range(50):
            input_to_md5 = md5(input_to_md5).digest()
        
    encryption_key = input_to_md5[:Length]
    if R == 2:
        decrypted = rc4(O, encryption_key)
    else:
        decrypted = O
        for i in range(19, -1, -1):
            decrypted = rc4(decrypted, bytes(x ^ i for x in encryption_key))
    return authenticate_user_password(decrypted, encryption_dict, id_array)



def decrypt(encryption_key: 'bytes', encryption_dict : 'dict', data : 'bytes', identifier : 'tuple'):
    n = len(encryption_key)
    object_number = identifier[0].to_bytes(4, byteorder='little')
    generation_number = identifier[1].to_bytes(4, byteorder='little')
    encryption_key_ext = encryption_key + object_number[:3] + generation_number[:2]
    # TODO: if using aes...
    hashed_value = md5(encryption_key_ext).digest()
    encryption_key = hashed_value[:min([n + 5, 16])]
    
    # TODO: if using aes..
    return rc4(data, encryption_key)



class StandardSecurityHandler:


    def __init__(self, password : 'bytes', encryption_dict : 'dict', id_array : 'list'):
        self.__encryption_dict = encryption_dict
        self.__id_array = id_array
        self.__encryption_key = authenticate_user_password(password, encryption_dict, id_array)
        if self.__encryption_key is None:
            raise PDFWrongPasswordError()
    

    def decrypt(self, data, identifier):
        return decrypt(self.__encryption_key, self.__encryption_dict, data, identifier)
