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
