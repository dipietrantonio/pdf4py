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
        self.catalog = self._parser.parse_reference(catalogRef)
        self.pages = list()
        self.__retrieve_pages(self.catalog["Pages"])
  

    def __retrieve_pages(self, item):
        itemDict = self._parser.parse_reference(item)
        if itemDict["Type"] == "Pages":
            for kid in itemDict["Kids"]:
                self.__retrieve_pages(kid)
        else:
            self.pages.append(itemDict)
        