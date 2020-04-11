
def rc4(buffer, key):
    """
    Encrypt / decrypt the content of `buffer` using RC4 algorithm.


    Parameters
    ----------
    buffer : bytes
        The bytes sequence to encrypt or decrypt.
    
    key : bytes
        The key to be used to perform the cryptographic operation.


    Returns
    -------
    A bytes sequence representing the transformed input.

    
    More information
    ----------------
    Adapted from http://cypherpunks.venona.com/archive/1994/09/msg00304.html
    """
    # Preparation step
    state = list(range(256))       
    x = 0
    y = 0   
    index1 = 0
    index2 = 0             
    for counter in range(256):
        index2 = (key[index1] + state[counter] + index2) % 256                
        state[counter], state[index2] = state[index2], state[counter]            
        index1 = (index1 + 1) % len(key)  
    
    # encryption / decryption step
    output = [0] * len(buffer)
    for i in range(len(buffer)):
        x = (x + 1) % 256                      
        y = (state[x] + y) % 256               
        state[x], state[y] = state[y], state[x]                          
        xorIndex = (state[x] + state[y]) % 256                 
        output[i] = buffer[i] ^ state[xorIndex]
    
    return bytes(output)
