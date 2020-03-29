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


from .parser import *
from ._lexer import Lexer

class ContentStream:

    def __init__(self, obj):

        if isinstance(obj, list):
            pass
        elif isinstance(obj, PDFStream):
            pass
        else:
            raise PDFSyntaxError("A ContentStream must be an array or a stream.")



class Page:

    def __init__(self, page_dict : 'dict', parent : 'Document'):
        # init page here
        if 'Contents' in page_dict:
            self.contents = ContentStream(page_dict['Contents'])
        


class Document:

    def __init__(self, source):
        self._parser = Parser(source)
        self._read_catalog()
    

    def _read_catalog(self):
        catalogRef = self._parser.trailer["Root"]
        self.catalog = self._parser.parse_xref_entry(catalogRef).value
        self.pages = list()
        self.__retrieve_pages(self.catalog["Pages"])
  

    def __retrieve_pages(self, item):
        itemDict = self._parser.parse_xref_entry(item).value
        if itemDict["Type"].value == "Pages":
            for kid in itemDict["Kids"]:
                self.__retrieve_pages(kid)
        else:
            self.pages.append(itemDict)
        