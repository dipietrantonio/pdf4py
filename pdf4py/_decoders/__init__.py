"""
MIT License

Copyright (c) 2019 Cristian Di Pietrantonio (cristiandipietrantonio@gmail.com)

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
import zlib
from math import floor
from binascii import unhexlify
from ..exceptions import PDFUnsupportedError
from .._charset import BLANKS

decoders = {}


def register(filterName):
    def wrapper(func):
        decoders[filterName] = func
    return wrapper



def tiff_predictor(data, width, bits_per_component, colors):
    if bits_per_component < 8:
        raise PDFUnsupportedError("The value '{}' for 'BitsPerComponent' parameter of 'FlateDecode' is not supported.".format(bits_per_component))
    output = bytearray(len(data))
    bpp = int(bits_per_component / 8 * colors)
    width *= bpp
    for i in range(0, len(data), width):
        output[i:i + bpp] = data[i:i + bpp]
        for j in range(bpp, width):
            output[i + j] = output[i + j - bpp] + data[i + j] 
    return output



def paeth_predictor(a, b, c):
    p = a + b - c
    pa = abs(p - a)
    pb = abs(p - b)
    pc = abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    elif pb <= pc:
        return b
    else:
        return c



def png_filter(data, width, bits_per_component, colors):
    """
    For more information
    https://www.w3.org/TR/PNG-Filters.html
    """
    if bits_per_component < 8:
        raise PDFUnsupportedError("The value '{}' for 'BitsPerComponent' parameter of 'FlateDecode' is not supported.".format(bits_per_component))
    output = bytearray()
    bpp = int(bits_per_component / 8 * colors)
    width *= bpp
    previous_scanline = b'\x00' * width
    for row_index in range(0, len(data), width + 1):
        filter_type = data[row_index]
        current_scanline = data[row_index + 1:row_index + 1 + width]    
        if filter_type == 0:
            unfiltered = current_scanline
        elif filter_type == 1:
            unfiltered = current_scanline[0:bpp] + bytes((current_scanline[i] + current_scanline[i - bpp]) & 255 for i in range(bpp, width))
        elif filter_type == 2:
            unfiltered = bytes((current_scanline[i] + previous_scanline[i]) & 255 for i in range(width))
        elif filter_type == 3:
            # TODO: test this
            unfiltered = [0] * width
            for i in range(width):
                raw = 0 if i < bpp else unfiltered[i - bpp]
                unfiltered[i] = (current_scanline[i] + floor((raw + previous_scanline[i]) / 2)) & 255
        elif filter_type == 4:
            unfiltered = [0] * width
            for i in range(width):
                a = 0 if i < bpp else unfiltered[i - bpp]
                b = previous_scanline[i]
                c = 0 if i < bpp else previous_scanline[i - bpp]
                unfiltered[i] = (current_scanline[i] + paeth_predictor(a, b, c)) & 255
        else:
            raise PDFUnsupportedError("Unsupported png predictor type: {}".format(filter_type))
        
        output.extend(unfiltered)
        previous_scanline = unfiltered

    return bytes(output)


@register("FlateDecode")
def flate_decode(data, params):
    data = zlib.decompress(data)
    predictor = params.get('Predictor', 1)
    if predictor == 1:
        return data
    columns = params.get('Columns', 1)
    colors = params.get('Colors', 1)
    bits_per_component = params.get('BitsPerComponent', 8)
    
    if predictor == 2:
        print(params)
        return tiff_predictor(data, columns, bits_per_component, colors)
    elif predictor >= 10:
        return png_filter(data, columns, bits_per_component, colors)
    return data


@register("ASCIIHexDecode")
def asciihexdecode(data, params):
    # TODO: test it
    EOD = data.find(ord('>'))
    if EOD != len(data) - 1:
        # TODO: better message
        raise Exception("Badly encoded data.")
    data = [x for x in data if x not in BLANKS]
    if len(data) % 2 == 1:
        data.append(ord('0'))
    return unhexlify(data)


@register("JPXDecode")
def jpx_decode(data, params):
    return data


@register("DCTDecode")
def dct_decode(data, params):
    return data


def decode(D : 'dict', sec : 'dict', data):
    filtersChain = D.get('Filter')
    if filtersChain is not None:
        if isinstance(filtersChain, list):
            filtersChain = tuple(x.value for x in filtersChain)
        else:
            filtersChain = (filtersChain.value,)
        filterParams = D.get('DecodeParms', {})
        for filterSpecifier in reversed(filtersChain):
            decoder = decoders.get(filterSpecifier)
            if decoder is None:
                raise PDFUnsupportedError("Filter '{}' is not supported.".format(filterSpecifier))
            data = decoder(data, filterParams)    
    return data

