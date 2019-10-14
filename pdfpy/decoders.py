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


decoders = {}


def register(filterName):
    def wrapper(func):
        decoders[filterName] = func
    return wrapper


@register("FlateDecode")
def flate_decode(data):
    return zlib.decompress(data)


def decode(D : 'dict', sec : 'dict', data):
    filtersChain = D['Filter']
    if isinstance(filtersChain, list):
        filtersChain = tuple(x.value for x in filtersChain)
    else:
        filtersChain = (filtersChain,)
    filterParams = D.get('FilterParams')
    for filterSpecifier in reversed(filtersChain):
        decoder = decoders[filterSpecifier]
        data = decoder(data)
    
    return data

