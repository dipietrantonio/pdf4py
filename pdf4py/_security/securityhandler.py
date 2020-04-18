from itertools import takewhile, chain
from hashlib import md5, sha256
from binascii import unhexlify
from ..exceptions import *
from .rc4 import rc4
from .aes import cbc_decrypt
from ..types import PDFHexString, PDFLiteralString
import stringprep
import unicodedata

PASSWORD_PADDING = b"\x28\xBF\x4E\x5E\x4E\x75\x8A\x41\x64\x00\x4E\x56\xFF\xFA\x01\x08\x2E\x2E\x00\xB6"\
    b"\xD0\x68\x3E\x80\x2F\x0C\xA9\xFE\x64\x53\x69\x7A"


def sals_stringprep(string):
    """

    TODO: implements bidirectional checks https://tools.ietf.org/html/rfc3454#section-6
    """
    new_string = []
    for x in string:
        if stringprep.in_table_c12(x):
            new_string.append(' ')
        elif stringprep.in_table_b1(x):
            continue
        elif stringprep.in_table_c12(x) or stringprep.in_table_c21_c22(x) or stringprep.in_table_c3(x)\
                or stringprep.in_table_c4(x) or stringprep.in_table_c5(x) or stringprep.in_table_c6(x)\
                or stringprep.in_table_c7(x) or stringprep.in_table_c8(x) or stringprep.in_table_c9(x):
            raise PDFGenericError("Invalid input character in password.")
        else:
            new_string.append(x)
    return unicodedata.normalize('NFKC', "".join(c for c in new_string))



def compute_encryption_key_AESV3(password : 'str', encryption_dict : 'dict'):
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
    U = encryption_dict["U"]
    U = U.value if isinstance(U, PDFLiteralString) else unhexlify(U.value)
    O = encryption_dict["O"]
    O = O.value if isinstance(O, PDFLiteralString) else unhexlify(O.value)

    prepped = sals_stringprep(password)
    truncated = prepped.encode("utf8")[:127]
    digest = sha256(truncated + O[32:32+8] + U).digest()
    from binascii import hexlify
    if digest == O[:32]:
        intermediate = sha256(truncated + O[-8:] + U).digest()
        OE = encryption_dict["OE"]
        OE = OE.value if isinstance(OE, PDFLiteralString) else unhexlify(OE.value)
        file_encryption_key = cbc_decrypt(OE, intermediate, b'\x00'*16, padding = False)
    else:
        digest = sha256(truncated + U[32:32+8]).digest()
        if digest == U[:32]:
            intermediate = sha256(truncated + U[-8:]).digest()
            UE = encryption_dict["UE"]
            UE = UE.value if isinstance(UE, PDFLiteralString) else unhexlify(UE.value)
            file_encryption_key = cbc_decrypt(UE, intermediate, b'\x00'*16, padding = False)
        else:
            raise PDFWrongPasswordError()
    return file_encryption_key



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
        raise PDFGenericError("Invalid key length.")
    Length = Length // 8
    input_to_md5 = bytearray()
    input_to_md5.extend((password + PASSWORD_PADDING)[:32])
    input_to_md5.extend(O)
    input_to_md5.extend(encryption_dict["P"].to_bytes(4, byteorder='little', signed = True))
    input_to_md5.extend(id_array[0])
    if R >= 4 and not encryption_dict.get("EncryptMetadata", True):
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
        input_to_md5.extend(id_array[0])
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



def decrypt(encryption_key: 'bytes', encryption_dict : 'dict', data : 'bytes', identifier : 'tuple', algo = 'rc4'):
    n = len(encryption_key)
    object_number = identifier[0].to_bytes(4, byteorder='little')
    generation_number = identifier[1].to_bytes(4, byteorder='little')
    encryption_key_ext = encryption_key + object_number[:3] + generation_number[:2]
    if algo == 'AES':
        encryption_key_ext += b'\x73\x41\x6C\x54'
    hashed_value = md5(encryption_key_ext).digest()
    encryption_key = hashed_value[:min([n + 5, 16])]
    if algo == 'AES':
        IV, data = data[:16], data[16:]
        return cbc_decrypt(data, encryption_key, IV)
    else:
        return rc4(data, encryption_key)



class StandardSecurityHandler:


    def __init__(self, password : 'bytes or str', encryption_dict : 'dict', id_array : 'list'):
        self.__encryption_dict = encryption_dict
        self.__V = self.__encryption_dict['V']
        if self.__V not in list(range(6)):
            raise PDFGenericError("The 'V' entry in the Encrypt dictionary is given an illegal value: '{}'".format(self.__V))
        if self.__V == 5:
            password = str() if password is None else password
            if not isinstance(password, str):
                raise PDFGenericError('The password must be a str object.')
            self.__encryption_key = compute_encryption_key_AESV3(password, encryption_dict)
        else:
            password = bytes() if password is None else password
            self.__id_array = [unhexlify(x.value) if isinstance(x, PDFHexString) else x.value for x in id_array]
            self.__encryption_key = authenticate_user_password(password, encryption_dict, self.__id_array)
            if self.__encryption_key is None:
                self.__encryption_key = authenticate_owner_password(password, encryption_dict, self.__id_array)    
                if self.__encryption_key is None:
                    raise PDFWrongPasswordError()



    def decrypt_string(self, data, identifier):
        if self.__V >= 4:
            crypt_filter_name = self.__encryption_dict.get('StrF')
            if crypt_filter_name is None:
                raise PDFSyntaxError("No 'StrF' entry found in 'Encrypt' dictionary (but V = 4).")
            elif crypt_filter_name == 'Identity':
                return data
            else:
                CF = self.__encryption_dict.get('CF')
                if CF is None:
                    raise PDFSyntaxError("No 'CF' entry in 'Encrypt' dictionary (but V = 4)")
                crypt_filter = CF[crypt_filter_name]

                CFM = crypt_filter.get('CFM', 'None')
                if CFM == 'None':
                    raise PDFUnsupportedError("Crypt filter with CFM = None is not supported.")
                elif CFM == 'V2':
                    return decrypt(self.__encryption_key, self.__encryption_dict, data, identifier)
                elif CFM == 'AESV2':
                    return decrypt(self.__encryption_key, self.__encryption_dict, data, identifier, 'AES')
                elif CFM == 'AESV3':
                    return cbc_decrypt(data[16:], self.__encryption_key, data[:16])
                else:
                    raise PDFSyntaxError('Unexpected value for CFM: "{}"'.format(CFM))
        else:
            return decrypt(self.__encryption_key, self.__encryption_dict, data, identifier)

    
    def decrypt_stream(self, data, D, identifier):
        if self.__V == 4:
            filters = D.get('Filters')
            if isinstance(filters, list):
                filters = filters[-1]
            if filters is None or filters != 'Crypt':
                crypt_filter_name = self.__encryption_dict.get('StmF')
                if crypt_filter_name is None:
                    raise PDFSyntaxError("No 'StmF' entry found in 'Encrypt' dictionary (but V = 4).")
            else:
                params = D.get('DecodeParams', {})
                crypt_filter_name = params.get('Name', 'Identity')
            if crypt_filter_name == 'Identity':
                return data
            else:
                CF = self.__encryption_dict.get('CF')
                if CF is None:
                    raise PDFSyntaxError("No 'CF' entry in 'Encrypt' dictionary (but V = 4)")
                crypt_filter = CF[crypt_filter_name]
                CFM = crypt_filter.get('CFM', 'None')
                if CFM == 'None':
                    raise PDFUnsupportedError("Crypt filter with CFM = None is not supported.")
                elif CFM == 'V2':
                    return decrypt(self.__encryption_key, self.__encryption_dict, data, identifier)
                elif CFM == 'AESV2':
                    return decrypt(self.__encryption_key, self.__encryption_dict, data, identifier, 'AES')
                elif CFM == 'AESV3':
                    return cbc_decrypt(data[16:], self.__encryption_key, data[:16])
                else:
                    raise PDFSyntaxError('Unexpected value for CFM: "{}"'.format(CFM))

        else:
            return decrypt(self.__encryption_key, self.__encryption_dict, data, identifier)

        