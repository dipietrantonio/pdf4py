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

TRAILER_FIELDS = {"Root", "ID", "Size", "Encrypt", "Info", "Prev"}





class XRefTable:

    def __init__(self, previous : 'XRefTable', inUseObjects : 'dict', freeObjects : 'set', compressedObjects : 'dict' = None, sideObjstm = None):
        self.__inUseObjects = inUseObjects
        self.__freeObjects = freeObjects
        self.__compressedObjects = {} if compressedObjects is None else compressedObjects
        self.__previous = previous
        self.__sideObjstm = sideObjstm
        

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



class PDFParser:


    def __init__(self, obj):
        self.__lexer = Lexer(obj)
        self.__parse_xref()
       


    def parse_xref_entry(self, xrefEntry : 'PDFXrefEntity'):
        if isinstance(xrefEntry, XrefInUseEntry):
            logging.debug("Parsing InUseEntry {} ..".format(repr(xrefEntry)))
            self.__lexer.move_at_position(xrefEntry.offset)
            parsedObject = self.__parse_object()
            self.__lexer.move_back()
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
            prevLexer = self.__lexer
            self.__lexer = Lexer(Seekable(stream))
            obj = None
            for i in range(D["N"]):
                n1 = next(self.__lexer).value
                n2 = next(self.__lexer).value
                if not(isinstance(n1, int) and isinstance(n2, int)):
                    raise PDFSyntaxError("Expected integers in object stream.")
                if n1 == xrefEntry.object_number:
                    offset = D["First"] + n2
                    self.__lexer.move_at_position(offset)
                    obj = self.__parse_object()
                    break
            if obj is None:
                raise PDFSyntaxError("Compressed object not found.")
            self.__lexer = prevLexer
            return obj
        else:
            raise ValueError("Argument type not supported.")


    def __parse_xref(self):
        # fist, find xrefstart, starting from end of file
        xrefstartPos = self.__lexer.rfind(b"startxref")
        if xrefstartPos < 0:
            raise PDFSyntaxError("'startxref' keyword not found.")
        xrefPos = next(self.__lexer)
        xrefs = []
        while xrefPos >= 0: # while there are xref to process
            currentLexeme = self.__lexer.move_at_position(xrefPos)
            if currentLexeme.type == LEXEME_KEYWORD and currentLexeme.value == b"xref":
                logging.debug("Parsing an xref table..")
                # then it is a normal xref table
                trailer, xrefData = self.__parse_xref_table()
                xrefs.insert(0, xrefData)
                # Check now if this is a PDF in compatibility mode where there is xref stream
                # reference in the trailer.          
                xrefstmPos = trailer.get("XRefStm")
                if xrefstmPos is not None:
                    logging.debug("Found a xref stream reference in trailer of xref table..")
                    self.__lexer.move_at_position(xrefstmPos)
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


    def __parse_xref_table(self):
        # first, locate the trailer
        next(self.__lexer)
        inUseObjects = dict()
        freeObjects = set()
        while self.__lexer.current_lexeme.type == LEXEME_NUMBER:
            start = self.__lexer.current_lexeme
            if start.type != LEXEME_NUMBER:
                raise PDFSyntaxError("Expected the ID of the fist object in section.")
            start = start.value
            count = next(self.__lexer)
            if count.type != LEXEME_NUMBER:
                raise PDFSyntaxError("Expected the number of elements in the section.")
            count = count.value
            # read all records in subsection
            for i in range(count):
                offsetToken = next(self.__lexer)
                if offsetToken.type != LEXEME_NUMBER:
                    raise PDFSyntaxError("Expected 'offset' value for xref entry.")
                genNumberToken = next(self.__lexer)
                if genNumberToken.type != LEXEME_NUMBER:
                    raise PDFSyntaxError("Expected 'generation_number' value for xref entry.")
                markerToken = next(self.__lexer)
                if markerToken.type != LEXEME_KEYWORD or markerToken.value not in [b'n', b'f']:
                    raise PDFSyntaxError("Expected 'in_use' specifier ('n' or 'f')")
                if start == 0 and i == 0:
                    continue # skip head of the free objects linked list  (will not be used)
                if markerToken.value == b'n':
                    xrefEntry = XrefInUseEntry(offsetToken.value, start + i, genNumberToken.value)
                    logging.debug("xref entry: {}".format(xrefEntry))
                    inUseObjects[(xrefEntry.object_number, xrefEntry.generation_number)] = xrefEntry
                else:
                    xrefEntry = (start + i, genNumberToken.value - 1)
                    freeObjects.add(xrefEntry)
            next(self.__lexer)
        # now there must be the trailer
        if not (self.__lexer.current_lexeme.type == LEXEME_KEYWORD and self.__lexer.current_lexeme.value == b'trailer'):
            raise PDFSyntaxError("Expecting 'trailer' section after 'xref' table.")
        next(self.__lexer)
        trailer = self.__parse_dictionary_or_stream()
        return trailer, (inUseObjects, freeObjects)
    


    def parse_list(self):
        if not self.__lexer.current_lexeme.value == '[':
            raise PDFSyntaxError("Expecting opening square braket to parse list, but not found.")
        next(self.__lexer)
        L = list()
        while True:
            if self.__lexer.current_lexeme.value == ']':
                break
            L.append(self.__parse_object())

        # ok, we successfully parsed a list
        try:
            next(self.__lexer) # remove CLOSE_SQUARE_BRAKET from stream
        except StopIteration:
            logging.debug("Stop iteration reached while parsing a list.")
        return L

    
    def __parse_dictionary_or_stream(self):
        if not self.__lexer.current_lexeme.type == LEXEME_DICT_OPEN:
            raise PDFSyntaxError("Expecting opening token for dictionary, but not found.")
        
        next(self.__lexer)
        D = dict()
        # now process key - value pairs
        while True:
            # get the key
            keyToken = self.__lexer.current_lexeme
            if keyToken.type == LEXEME_DICT_CLOSE:
                break
            elif keyToken.type != LEXEME_NAME:
                raise PDFSyntaxError("Expecting dictionary key, but not found.")
            # now get the value
            next(self.__lexer)
            keyValue = self.__parse_object()    
            D[keyToken.value] = keyValue
        
        try:
            nextLexeme = next(self.__lexer)
        except StopIteration:
            logging.info("__parse_dictionary_or_stream: end of stream reached.")
            logging.info(str(D))
            return D
        
        if not self.__lexer.current_lexeme.type == LEXEME_STREAM:
            return D

        # it is a stream object, lets find out its length
        length = D["Length"]
        if isinstance(length, PDFReference):
            key = (length.object_number, length.generation_number)
            try:
                xrefEntity = self.xrefTable[key]
            except KeyError:
                logging.warning("Reference to non-existing object.")
                # TODO: now what?
                raise PDFSyntaxError("Missing stream 'Length' property.")
            length = self.parse_xref_entry(xrefEntity).value
            if not isinstance(length, int):
                raise PDFSyntaxError("The object referenced by 'Length' is not an integer.")
        # now we can provide this info to reader
        bytesReader = self.__lexer.current_lexeme.value
        def reader():
            data = bytesReader(length)
            return decode(D, {}, data)
        # and move the header to the endstream position
        currentLexeme = self.__lexer.move_at_position(self.__handle.tell() + length)
        if currentLexeme.type != LEXEME_KEYWORD or currentLexeme.value != b"endstream": 
            raise PDFSyntaxError("'stream' not matched with an 'endstream' keyword.")
        next(self.__lexer)
        return PDFStream(D, reader)


    def __parse_object(self):
        """
        Parse a generic PDF object.
        """
        if self.__lexer.current_lexeme.type == LEXEME_SINGLETON and\
                self.__lexer.current_lexeme.value == '[':
            # it is a list of objects, parse it
            return self.parse_list()
        
        elif self.__lexer.current_lexeme.type == LEXEME_DICT_OPEN:
            return self.__parse_dictionary_or_stream()
        
        elif self.__lexer.current_lexeme.type in [LEXEME_STRING_HEXADECIMAL, LEXEME_STRING_LITERAL, LEXEME_NAME]:
            # because those types can be confused or are indistinguishable, we return the lexeme
            s = self.__lexer.current_lexeme
            try:
                next(self.__lexer)
            except StopIteration:
                logging.info("__parse_object: end of stream reached.")
            return s
        elif self.__lexer.current_lexeme.type == LEXEME_BOOLEAN:
            # a boolean token can be represented by Python's native bool type
            s = self.__lexer.current_lexeme.value
            try:
                next(self.__lexer)
            except StopIteration:
                logging.info("__parse_object: end of stream reached.")
            return s
        elif self.__lexer.current_lexeme.type == LEXEME_NUMBER:
            # Here we can parse a single number or a reference to an indirect object
            lex1 = self.__lexer.current_lexeme
            try:
                lex2 = next(self.__lexer)
            except StopIteration:
                logging.info("__parse_object: end of stream reached.")
                return lex1.value
            if lex2.type != LEXEME_NUMBER:
                return lex1.value
            
            try:
                lex3 = next(self.__lexer)
            except StopIteration:
                logging.info("__parse_object: end of stream reached.")
                return lex1.value
        
            if lex3.type == LEXEME_SINGLETON and lex3.value == 'R':
                try:
                    next(self.__lexer)
                except StopIteration:
                    logging.info("__parse_object: end of stream reached.")
                return PDFReference(lex1.value, lex2.value)
            elif lex3.type == LEXEME_OBJ_OPEN:
                next(self.__lexer)
                o = self.__parse_object()
                if not self.__lexer.current_lexeme.type == LEXEME_OBJ_CLOSE:
                    raise PDFSyntaxError("Expecting matching 'endobj' for 'obj', but not found.")
                try:
                    next(self.__lexer)
                except StopIteration:
                    logging.info("__parse_object: end of stream reached.")
                return PDFIndirectObject(lex1.value, lex2.value, o)
            else:
                # it was just a number, return it and put back other stuff in the stack
                self.__lexer.put_back(lex2, lex3)
                return lex1.value
        
        elif self.__lexer.current_lexeme.type == LEXEME_KEYWORD and self.__lexer.current_lexeme.value == b"null":
            try:
                next(self.__lexer)
            except StopIteration:
                logging.info("__parse_object: end of stream reached.")
            return None

        else:
            logging.info("__parse_object: unexpected lexeme encountered ({}).".format(self.__lexer.current_lexeme))
            raise PDFSyntaxError("Unexpected lexeme encountered ({}).".format(self.__lexer.current_lexeme))