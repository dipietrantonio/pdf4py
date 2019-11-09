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


import logging
from collections import namedtuple
from functools import partial
from contextlib import suppress
from ._lexer import *
from ._decoders import decode



class PDFSyntaxError(Exception):
    """
    When the parsed PDF does not conform to syntax rules.
    """



class PDFUnexpectedTokenError(PDFSyntaxError):
    """
    When the parser cannot recognise the grammar.
    """



class PDFUnsupportedError(Exception):
    """
    When the parser does not support a PDF feature.
    """



PDFStream = namedtuple("PDFStream", ["dictionary", "stream"])
PDFReference = namedtuple("PDFReference", ["object_number", "generation_number"])
PDFIndirectObject = namedtuple("PDFIndirectObject", ["object_number", "generation_number", "value"])
XrefInUseEntry = namedtuple("XrefInUseEntry", ["offset", "object_number", "generation_number"])
XrefCompressedEntry = namedtuple("XrefCompressedEntry", ["object_number", "objstm_number", "index"])



class BaseParser:


    def __init__(self, obj):
        """
        Initialize the parser by setting the underlying lexical analyzer and load the fist lexeme.
        From now on the following invariant must be kept: before any call the to BaseParser._parse_object
        method, the current_lexeme property of the lexer must be set to the fist unprocessed lexeme in
        the input.
        """
        self._lexer = Lexer(obj)
        with suppress(StopIteration):
            next(self._lexer)
    

    def __next__(self):
        return self._parse_object()


    def __iter__(self):
        return self


    def _raise_syntax_error(self, msg):
        context, errorPosition, relativeErrorPosition = self._lexer.get_context()
        finalMsg = "{}\n\nPosition {}, context:\n\t{}\n\t{}^".format(msg, errorPosition, context,
            " "*relativeErrorPosition)
        raise PDFSyntaxError(finalMsg)


    def _parse_dictionary_or_stream(self): 
        next(self._lexer)
        D = dict()
        # now process key - value pairs
        while True:
            # get the key
            keyToken = self._lexer.current_lexeme
            if isinstance(keyToken, PDFKeyword) and keyToken.value == b">>":
                break
            elif not isinstance(keyToken, PDFName):
                self._raise_syntax_error("Expecting dictionary key, but not found.")
            # now get the value
            next(self._lexer)
            keyValue = self._parse_object()    
            D[keyToken.value] = keyValue
        
        try:
            nextLexeme = next(self._lexer)
        except StopIteration:
            return D
        
        if not isinstance(self._lexer.current_lexeme, PDFStreamReader):
            return D

        # it is a stream object, lets find out its length
        length = D["Length"]
        # check also if there is a specified file where to read
        filePath = D.get("F")
        if filePath is not None:
            raise PDFUnsupportedError("""
                Support for streams having data specified in an external file are not supported yet.
                Please consider sending to the developers the PDF that generated this exception so that
                they can work on supporting this feature. 
                """)
        if isinstance(length, PDFReference):
            key = (length.object_number, length.generation_number)
            try:
                xrefEntity = self.xrefTable[key]
            except KeyError:
                logging.warning("Reference to non-existing object.")
                # TODO: now what?
                self._raise_syntax_error("Missing stream 'Length' property.")
            length = self.parse_xref_entry(xrefEntity).value
            if not isinstance(length, int):
                self._raise_syntax_error("The object referenced by 'Length' is not an integer.")
        # now we can provide this info to reader
        bytesReader = self._lexer.current_lexeme.value
        def reader():
            data = bytesReader(length)
            return decode(D, {}, data)
        # and move the header to the endstream position
        currentLexeme = self._lexer.move_at_position(self._lexer.source.tell() + length)
        if not isinstance(currentLexeme, PDFKeyword) or currentLexeme.value != b"endstream": 
            self._raise_syntax_error("'stream' not matched with an 'endstream' keyword.")
        next(self._lexer)
        return PDFStream(D, reader)


    def _parse_object(self):
        """
        Parse a generic PDF object.
        """
        if isinstance(self._lexer.current_lexeme, PDFSingleton) and self._lexer.current_lexeme.value == OPEN_SQUARE_BRACKET:
            # it is a list of objects
            next(self._lexer)
            L = list()
            while True:
                if isinstance(self._lexer.current_lexeme, PDFSingleton) and self._lexer.current_lexeme.value == CLOSE_SQUARE_BRACKET:
                    break
                L.append(self._parse_object())
            # we have successfully parsed a list
            with suppress(StopIteration):
                next(self._lexer) # remove CLOSE_SQUARE_BRAKET token stream from stream
            return L
        
        elif isinstance(self._lexer.current_lexeme, PDFKeyword):
            keywordVal = self._lexer.current_lexeme.value            
            if keywordVal == b"<<":
                return self._parse_dictionary_or_stream()
            elif keywordVal == b"null":
                with suppress(StopIteration):
                    next(self._lexer)
                return None

        elif self._lexer.current_lexeme.__class__ in [PDFHexString, str, bool, float, PDFName]:
            s = self._lexer.current_lexeme
            with suppress(StopIteration):
                next(self._lexer)
            return s

        elif isinstance(self._lexer.current_lexeme, int):
            # Here we can parse a single number or a reference to an indirect object
            lex1 = self._lexer.current_lexeme
            
            try:
                lex2 = next(self._lexer)
            except StopIteration:
                return lex1

            if not isinstance(lex2, int):
                return lex1
            
            try:
                lex3 = next(self._lexer)
            except StopIteration:
                return lex1
        
            if isinstance(lex3, PDFSingleton) and lex3.value == KEYWORD_REFERENCE:
                with suppress(StopIteration):
                    next(self._lexer)
                return PDFReference(lex1, lex2)
            
            elif isinstance(lex3, PDFKeyword) and lex3.value == b"obj":
                next(self._lexer)
                o = self._parse_object()
                if not isinstance(self._lexer.current_lexeme, PDFKeyword) or self._lexer.current_lexeme.value != b"endobj":
                    self._raise_syntax_error("Expecting matching 'endobj' for 'obj', but not found.")
                with suppress(StopIteration):
                    next(self._lexer)
                return PDFIndirectObject(lex1, lex2, o)
            
            else:
                # it was just a integer number, undo the last next() call and return it
                self._lexer.undo_next(lex2)
                return lex1
        
        # if the execution arrived here, it means that there is a syntax error.
        raise self._raise_syntax_error("Unexpected lexeme encountered ({}).".format(self._lexer.current_lexeme))



TRAILER_FIELDS = {"Root", "ID", "Size", "Encrypt", "Info", "Prev"}



class XRefTable:

    def __init__(self, previous : 'XRefTable', inUseObjects : 'dict', freeObjects : 'set',
            compressedObjects : 'dict' = None, sideObjStm = None):
        
        self.__inUseObjects = inUseObjects
        self.__freeObjects = freeObjects
        self.__compressedObjects = {} if compressedObjects is None else compressedObjects
        self.__previous = previous
        self.__sideObjStm = sideObjStm
        

    @property
    def previous(self):
        return self.__previous


    def __getitem__(self, key):
        v = self.__inUseObjects.get(key)
        if v is not None:
            return v
        v = self.__compressedObjects.get(key)
        if v is not None:
            return v
        if key in self.__freeObjects:
            return None
        if self.__sideObjStm is not None:
            pass # TODO do something
        if self.__previous is None:
            logging.debug("Key not found: " + str(key))
            raise KeyError()
        else:
            return self.__previous[key]
        

    def active_keys(self):
        if not hasattr(self, "__activeKeys"):
            mykeys = list(self.__inUseObjects) + list(self.__compressedObjects)
            if self.__previous is not None:
                prevkeys = self.__previous.active_keys()
                for k in prevkeys:
                    if k not in self.__freeObjects:
                        mykeys.append(k)
            self.__activeKeys = mykeys
        return self.__activeKeys



class Parser(BaseParser):


    def __init__(self, obj):
        super().__init__(obj)
        self.__parse_xref_table()


    def parse_xref_entry(self, xrefEntry : 'PDFXrefEntity'):
        if isinstance(xrefEntry, XrefInUseEntry):
            logging.debug("Parsing InUseEntry {} ..".format(repr(xrefEntry)))
            self._lexer.move_at_position(xrefEntry.offset)
            parsedObject = self.__parse_object()
            self._lexer.move_back()
            return parsedObject
        elif isinstance(xrefEntry, XrefCompressedEntry):
            # now parse the object stream containing the object the entry refers to
            logging.debug("Parsing Compressed Entry {} ..".format(repr(xrefEntry)))
            try:
                objStmRef = self.xrefTable[(xrefEntry.objstm_number, 0)]
            except KeyError:
                raise PDFSyntaxError("Couldn't find the object stream in the xref table.")
            D, streamReader = self.parse_xref_entry(objStmRef).value
            stream = streamReader()
            prevLexer = self._lexer
            self._lexer = Lexer(Seekable(stream))
            obj = None
            for i in range(D["N"]):
                n1 = next(self._lexer).value
                n2 = next(self._lexer).value
                if not(isinstance(n1, int) and isinstance(n2, int)):
                    raise PDFSyntaxError("Expected integers in object stream.")
                if n1 == xrefEntry.object_number:
                    offset = D["First"] + n2
                    self._lexer.move_at_position(offset)
                    obj = self.__parse_object()
                    break
            if obj is None:
                raise PDFSyntaxError("Compressed object not found.")
            self._lexer = prevLexer
            return obj
        else:
            raise ValueError("Argument type not supported.")


    def __parse_xref_table(self):
        # fist, find xrefstart, starting from end of file
        xrefstartPos = self._lexer.rfind(b"startxref")
        if xrefstartPos < 0:
            raise PDFSyntaxError("'startxref' keyword not found.")
        xrefPos = next(self._lexer)
        xrefs = []
        while xrefPos >= 0: # while there are xref to process
            currentLexeme = self._lexer.move_at_position(xrefPos)
            if isinstance(currentLexeme, PDFKeyword) and currentLexeme.value == b"xref":
                logging.debug("Parsing an xref table..")
                # then it is a normal xref table
                trailer, xrefData = self.__parse_xref_section()
                xrefs.insert(0, xrefData)
                # Check now if this is a PDF in compatibility mode where there is xref stream
                # reference in the trailer.          
                xrefstmPos = trailer.get("XRefStm")
                if xrefstmPos is not None:
                    logging.debug("Found a xref stream reference in trailer of xref table..")
                    self._lexer.move_at_position(xrefstmPos)
                    _, xrefDataStream = self.__parse_xref_stream()
                    xrefs.insert(0, xrefDataStream)
            else:
                # it can only be a xref stream
                logging.debug("Parsing an xref stream..")
                trailer, xrefData = self.__parse_xref_stream()
                xrefs.insert(0, xrefData)
                
            # now process them
            if "Prev" in trailer:
                xrefPos = trailer["Prev"]
                del trailer["Prev"]
            else:
                xrefPos = -1
                self.__dict__.update(trailer)

        # now build a hierarchy of XrefTable instances
        self.xrefTable = None
        for xrefData in xrefs:
            self.xrefTable = XRefTable(self.xrefTable, *xrefData)
    


    def __parse_xref_stream(self):
        o = self.__parse_object()
        if not isinstance(o, PDFIndirectObject):
            raise PDFSyntaxError("Expecting a 'xref' rection, but it has not been found.")
        # TODO parse stream
        if not isinstance(o.value, PDFStream):
            raise PDFSyntaxError("Expecting a stream containing 'xref' information, but not found.")
        objStmDict, objStm = o.value
        if objStmDict['Type'].value != 'XRef':
            raise PDFSyntaxError("Expecting a stream containing 'xref' information, but not found.")
        trailer = {k : objStmDict[k] for k in objStmDict if k in TRAILER_FIELDS}
        xrefData = objStm()
        pos = 0 # current position inside xrefData
        # lets read the data
        size = objStmDict["Size"]
        index = objStmDict.get("Index", [0, size])
        w = [x for x in objStmDict["W"]]
        inUseObjects = dict()
        freeObjects = set()
        compressedObjects = dict()
        for i in range(0, len(index) - 1, 2):
            start, count = index[i], index[i+1]
            for j in range(count):
                # parse the record of values
                # skip object 0
                if start == 0 and j == 0:
                    pos += sum(w)
                    continue

                vals = [None] * 3
                for k in range(3):
                    if w[k] > 0:
                        vals[k] = sum([x << (w[k] - l - 1)*8 for l, x in enumerate(xrefData[pos:pos+w[k]])])
                        pos += w[k]
                
                # set default values
                if vals[0] is None:
                    vals[0] = 1
                if vals[0] == 1 and vals[2] is None:
                    vals[2] = 0
                
                # process data
                if vals[0] == 0:
                    entry = (start + j, vals[2])
                    freeObjects.add(entry)
                elif vals[0] == 1:
                    entry = XrefInUseEntry(vals[1], start + j, vals[2])
                    inUseObjects[(entry.object_number, entry.generation_number)] = entry
                else:
                    entry = XrefCompressedEntry(start + j, vals[1], vals[2])
                    compressedObjects[(entry.object_number, 0)] = entry
        return trailer, (inUseObjects, freeObjects, compressedObjects)


    def __parse_xref_section(self):
        # first, locate the trailer
        next(self._lexer)
        inUseObjects = dict()
        freeObjects = set()
        while isinstance(self._lexer.current_lexeme, int):
            start = self._lexer.current_lexeme
            if not isinstance(start, int):
                raise PDFSyntaxError("Expected the ID of the fist object in section.")
            count = next(self._lexer)
            if not isinstance(count, int):
                raise PDFSyntaxError("Expected the number of elements in the section.")
            # read all records in subsection
            for i in range(count):
                offsetToken = next(self._lexer)
                if not isinstance(offsetToken, int):
                    raise PDFSyntaxError("Expected 'offset' value for xref entry.")
                genNumberToken = next(self._lexer)
                if not isinstance(genNumberToken, int):
                    raise PDFSyntaxError("Expected 'generation_number' value for xref entry.")
                markerToken = next(self._lexer)
                if not isinstance(markerToken, PDFSingleton) or markerToken.value not in [INUSE_ENTRY_KEYWORD, FREE_ENTRY_KEYWORD]:
                    raise PDFSyntaxError("Expected 'in_use' specifier ('n' or 'f')")
                if start == 0 and i == 0:
                    continue # skip head of the free objects linked list  (will not be used)
                if markerToken.value == b'n':
                    xrefEntry = XrefInUseEntry(offsetToken, start + i, genNumberToken)
                    logging.debug("xref entry: {}".format(xrefEntry))
                    inUseObjects[(xrefEntry.object_number, xrefEntry.generation_number)] = xrefEntry
                else:
                    xrefEntry = (start + i, genNumberToken - 1)
                    freeObjects.add(xrefEntry)
            next(self._lexer)
        # now there must be the trailer
        if not isinstance(self._lexer.current_lexeme, PDFKeyword) or self._lexer.current_lexeme.value != b'trailer':
            raise PDFSyntaxError("Expecting 'trailer' section after 'xref' table.")
        next(self._lexer)
        trailer = self._parse_dictionary_or_stream()
        return trailer, (inUseObjects, freeObjects)