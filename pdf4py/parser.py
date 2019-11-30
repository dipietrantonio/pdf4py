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
from contextlib import suppress
from ._lexer import *
from ._decoders import decode
from .exceptions import PDFSyntaxError, PDFUnsupportedError

PDFStream = namedtuple("PDFStream", ["dictionary", "stream"])
PDFReference = namedtuple("PDFReference", ["object_number", "generation_number"])
PDFIndirectObject = namedtuple("PDFIndirectObject", ["object_number", "generation_number", "value"])
XrefInUseEntry = namedtuple("XrefInUseEntry", ["offset", "object_number", "generation_number"])
XrefCompressedEntry = namedtuple("XrefCompressedEntry", ["object_number", "objstm_number", "index"])
    


class XRefTable:
    """
    Implements the functionalities of a Cross Reference Table.

    An instance of `XRefTable` can be iterated over to get all the references to "in use" and "compressed" objects.
    Furthermore it implements the __getitem__ method that is used by the parser to look up objects if required
    during the parsing process.
    """
    def __init__(self, previous : 'XRefTable', inUseObjects : 'dict', freeObjects : 'set',
            compressedObjects : 'dict' = None):
        self.__inUseObjects = inUseObjects
        self.__freeObjects = freeObjects
        self.__compressedObjects = {} if compressedObjects is None else compressedObjects
        self.__previous = previous
        

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
            raise KeyError("Key not found: " + str(key))
        else:
            return self.__previous[key]
    
    
    def __iter__(self):      
        def gen():
            if self.previous is not None:
                for item in iter(self.previous):
                    if isinstance(item, XrefInUseEntry) and (item[1], item[2]) in self.__freeObjects:
                        pass
                    # TODO: understand how to delete compressed object (maybe it is not deleted at all)
                    yield item
            yield from self.__inUseObjects.values()
            yield from self.__compressedObjects.values()

        return gen()

    
    def __support_str_(self):
        """
        Support method to generate a string representation of the table.
        """

        inUseObjs = "\n".join(
            "{:10} {:5} {:10} n".format(x.object_number, x.generation_number, x.offset) for x in sorted(self.__inUseObjects.values())
            )
        freeObjs = "\n".join(
            "{:10} {:5} f".format(x[0], x[1] + 1) for x in sorted(self.__freeObjects)
            )
        compressedObjs = "\n".join(
            "{} {}".format(x[0], x[1]) for x in sorted(self.__compressedObjects.values())
            )
        
        resultingString = "Section\nIn use objects:\n{}\nFree objects:\n{}\nCompressed objects:\n{}".format(
            inUseObjs, freeObjs, compressedObjs)
        
        if self.__previous is not None:
            prevString = self.__previous.__support_str_()
            return prevString + "\n" + resultingString
        else:
            return resultingString


    def __str__(self):
        # TODO: build a better representation
        return self.__support_str_()



class BasicParser:


    def __init__(self, source, stream_reader = None, content_stream_mode = False):
        """
        Initialize the parser by setting the underlying lexical analyzer and load the fist lexeme.
        From now on the following invariant must be kept: before any call the to BaseParser._parse_object
        method, the current_lexeme property of the lexer must be set to the fist unprocessed lexeme in
        the input.
        """
        # read the header
        self._lexer = Lexer(source)
        self._stream_reader = stream_reader
        self.__ended = False
        self.__content_stream_mode = content_stream_mode
        try:
            next(self._lexer)
        except StopIteration:
            logging.debug("File is empty.")
            self.__ended = True
        

    def _raise_syntax_error(self, msg):
        context, errorPosition, relativeErrorPosition = self._lexer.get_context()
        finalMsg = "{}\n\nPosition {}, context:\n\t{}\n\t{}^".format(msg, errorPosition, context,
            " "*relativeErrorPosition)
        raise PDFSyntaxError(finalMsg)
    

    def __iter__(self):
        return self


    def __next__(self):
        return self.parse_object()


    def parse_object(self):
        """
        Parse a generic PDF object.
        """
        if self.__ended:
            raise StopIteration()

        if isinstance(self._lexer.current_lexeme, PDFSingleton) and self._lexer.current_lexeme.value == OPEN_SQUARE_BRACKET:
            # it is a list of objects
            next(self._lexer)
            L = list()
            while True:
                if isinstance(self._lexer.current_lexeme, PDFSingleton) and self._lexer.current_lexeme.value == CLOSE_SQUARE_BRACKET:
                    break
                L.append(self.parse_object())
            # we have successfully parsed a list
            # remove CLOSE_SQUARE_BRAKET token stream from stream
            try:
                next(self._lexer)
            except StopIteration:
                self.__ended = True
            return L
        
        elif isinstance(self._lexer.current_lexeme, PDFDictDelimiter) and self._lexer.current_lexeme.value == b"<<":
            next(self._lexer)
            D = dict()
            # now process key - value pairs
            while True:
                # get the key
                keyToken = self._lexer.current_lexeme
                if isinstance(keyToken, PDFDictDelimiter) and keyToken.value == b">>":
                    break
                elif not isinstance(keyToken, PDFName):
                    self._raise_syntax_error("Expecting dictionary key, '{}' found instead.".format(keyToken))
                
                # now get the value
                next(self._lexer)
                keyValue = self.parse_object()    
                D[keyToken.value] = keyValue
            
            try:
                nextLexeme = next(self._lexer)
            except StopIteration:
                self.__ended = True
                return D
            
            if not isinstance(self._lexer.current_lexeme, PDFStreamReader):
                return D
        
            if self._stream_reader is None:
                raise Exception("Cannot parse a stream with BasicParser without providing a stream_reader callable.")
        
            # now we can provide this info to reader
            bytesReader = self._lexer.current_lexeme.value
            length, reader = self._stream_reader(D, bytesReader)

            # and move the header to the endstream position
            currentLexeme = self._lexer.move_at_position(self._lexer.source.tell() + length)
            if not isinstance(currentLexeme, PDFKeyword) or currentLexeme.value != b"endstream": 
                self._raise_syntax_error("'stream' not matched with an 'endstream' keyword.")
            next(self._lexer)
            return PDFStream(D, reader)
  
        elif self._lexer.current_lexeme is None:
            try:
                next(self._lexer)
            except StopIteration:
                self.__ended = True
            return None

        elif self._lexer.current_lexeme.__class__ in [PDFHexString, str, bool, float, PDFName]:
            s = self._lexer.current_lexeme
            try:
                next(self._lexer)
            except StopIteration:
                self.__ended = True
            return s

        elif isinstance(self._lexer.current_lexeme, int):
            # Here we can parse a single number or a reference to an indirect object
            lex1 = self._lexer.current_lexeme
            
            try:
                lex2 = next(self._lexer)
            except StopIteration:
                self.__ended = True
                return lex1

            if not isinstance(lex2, int):
                return lex1
            
            try:
                lex3 = next(self._lexer)
            except StopIteration:
                self.__ended = True
                return lex1
        
            if isinstance(lex3, PDFOperator) and lex3.value == "R":
                try:
                    next(self._lexer)
                except StopIteration:
                    self.__ended = True
                return PDFReference(lex1, lex2)
            
            elif isinstance(lex3, PDFKeyword) and lex3.value == b"obj":
                next(self._lexer)
                o = self.parse_object()
                if not isinstance(self._lexer.current_lexeme, PDFKeyword) or self._lexer.current_lexeme.value != b"endobj":
                    self._raise_syntax_error("Expecting matching 'endobj' for 'obj', but not found.")
                try:
                    next(self._lexer)
                except StopIteration:
                    self.__ended = True
                return PDFIndirectObject(lex1, lex2, o)
            
            else:
                # it was just a integer number, undo the last next() call and return it
                self._lexer.undo_next(lex2)
                return lex1
        
        elif isinstance(self._lexer.current_lexeme, PDFOperator) and self.__content_stream_mode:
                val = self._lexer.current_lexeme
                try:
                    next(self._lexer)
                except StopIteration:
                    self.__ended = True
                return val

        # if the execution arrived here, it means that there is a syntax error.
        raise self._raise_syntax_error("Unexpected lexeme encountered ({}).".format(self._lexer.current_lexeme))



class Parser:
    """
    A parser is a software that checks whether the stream of lexemes extracted from the input forms
    valid sentences according to the target language. In practice, `Parser` uses the Lexer to extract
    simple, atomic, elements like PDF strings, names, numbers and keywords; in addition, it is able
    to recognize when these elements must be put together to form more complex data structures like
    arrays, dictionaries and streams.
    """
    TRAILER_FIELDS = {"Root", "ID", "Size", "Encrypt", "Info", "Prev"}


    def __init__(self, source):
        """
        Initialize the parser by setting the underlying lexical analyzer and load the fist lexeme.
        From now on the following invariant must be kept: before any call the to BaseParser._parse_object
        method, the current_lexeme property of the lexer must be set to the fist unprocessed lexeme in
        the input.
        """
        # read the header
        self._basic_parser = BasicParser(source, self._stream_reader)
        self._read_header()
        self.__parse_xref_table()
        

    def _read_header(self):
        logging.debug("Reading the header..")
        self._basic_parser._lexer.source.seek(0, 0)
        buff = bytearray()
        c = self._basic_parser._lexer.source.read(1)[0]
        while(c != LINE_FEED and c != CARRIAGE_RETURN):
            buff.append(c)
            c = self._basic_parser._lexer.source.read(1)[0]
        try:
            self.version = buff.decode()[1:]
        except UnicodeDecodeError:
            self.version = buff.decode("utf8")
        logging.debug("_reading_header finished.")
    

    def parse_xref_entry(self, xrefEntry):
        # TODO: find proper name to this method
        logging.debug("parse_xref_entry with input: " + str(xrefEntry))
        if isinstance(xrefEntry, PDFReference):
            logging.debug("It is a PDFReference")
            xrefEntry = self.xRefTable[xrefEntry]
        
        if isinstance(xrefEntry, XrefInUseEntry):
            logging.debug("it is an XrefInUSeEntry")
            self._basic_parser._lexer.move_at_position(xrefEntry.offset)
            parsedObject = self._basic_parser.parse_object()
            self._basic_parser._lexer.move_back()
            logging.debug("pasing the XrefInUseEntry finished.")
            return parsedObject
        
        elif isinstance(xrefEntry, XrefCompressedEntry):
            # now parse the object stream containing the object the entry refers to
            logging.debug("It is a Xref Compressed Entry.")
            streamToken = self.parse_xref_entry(PDFReference(xrefEntry.objstm_number, 0))
            logging.debug("Stream token: " + str(streamToken))
            D, streamReader = streamToken.value
            stream = streamReader()
            logging.debug("Stream got: " + str(stream))
            prevBasicParser = self._basic_parser
            self._basic_parser = BasicParser(stream, stream_reader=self._stream_reader)
            obj = None
            for i in range(D["N"]):
                n1 = self._basic_parser.parse_object()
                n2 = self._basic_parser.parse_object()
                if not(isinstance(n1, int) and isinstance(n2, int)):
                    self._basic_parser._raise_syntax_error("Expected integers in object stream.")
                if n1 == xrefEntry.object_number:
                    offset = D["First"] + n2
                    self._basic_parser._lexer.move_at_position(offset)
                    obj = self._basic_parser.parse_object()
                    break
            if obj is None:
                self._basic_parser._raise_syntax_error("Compressed object not found.")
            self._basic_parser = prevBasicParser
            logging.debug("setting back the parser.")
            return obj
        else:
            raise ValueError("Argument type not supported.")


    def __parse_xref_table(self):
        # fist, find xrefstart, starting from end of file
        xrefstartPos = self._basic_parser._lexer.rfind(b"startxref")
        if xrefstartPos < 0:
            self._basic_parser._raise_syntax_error("'startxref' keyword not found.")
        # get the position of the latest xref section
        xrefPos = next(self._basic_parser._lexer)
        # the following list will hold all the xref sections found in the PDF file.
        xrefs = []
        self.trailer = dict()
        while xrefPos >= 0: # while there are xref to process
            currentLexeme = self._basic_parser._lexer.move_at_position(xrefPos)
            if isinstance(currentLexeme, PDFKeyword) and currentLexeme.value == b"xref":
                logging.debug("Parsing an xref table..")
                # then it is a classic xref table, as opposed to xref streams
                trailer, xrefData = self.__parse_xref_section()
                xrefs.insert(0, xrefData)
                # Check now if this is a PDF in compatibility mode where there is xref stream
                # reference in the trailer.          
                xrefstmPos = trailer.get("XRefStm")
                if xrefstmPos is not None:
                    logging.debug("Found a xref stream reference in trailer of xref table..")
                    self._basic_parser._lexer.move_at_position(xrefstmPos)
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
                self.trailer.update(trailer)

        # now build a hierarchy of XrefTable instances
        self.xRefTable = None
        for xrefData in xrefs:
            self.xRefTable = XRefTable(self.xRefTable, *xrefData)


    def __parse_xref_stream(self):
        """
        Beginning with PDF 1.5, cross-reference information may be stored in a cross-reference stream instead of in a
        cross-reference table. Cross-reference streams provide the following advantages:
            - A more compact representation of cross-reference information
            - The ability to access compressed objects that are stored in object streams (see 7.5.7, "Object Streams")
              and to allow new cross-reference entry types to be added in the future
        """
        logging.debug("Parsing a xref stream..")
        o = self._basic_parser.parse_object()
        if not isinstance(o, PDFIndirectObject):
            self._basic_parser._raise_syntax_error("Expecting a 'xref' rection, but it has not been found.")
        if not isinstance(o.value, PDFStream):
            self._basic_parser._raise_syntax_error("Expecting a stream containing 'xref' information, but not found.")
        objStmDict, objStm = o.value
        if objStmDict['Type'].value != 'XRef':
            self._basic_parser._raise_syntax_error("Expecting a stream containing 'xref' information, but not found.")
        trailer = {k : objStmDict[k] for k in objStmDict if k in self.TRAILER_FIELDS}
        # read the raw stream content
        xrefData = objStm()
        logging.debug("xref stream: " + str(xrefData))
        # current position inside xrefData
        pos = 0
        # retrieves info about xref stream layout
        # TODO: support extends keyword
        if "Extends" in objStmDict:
            logging.warning("""
            'Extends' keyword found in a object stream dictionary, but it is not supported yet.
            Consider sending the file you are parsing to the developers of the library."""
            )
        size = objStmDict["Size"]
        index = objStmDict.get("Index", [0, size])
        # An array of integers representing the size of the fields in a single cross-reference entry.
        w = [x for x in objStmDict["W"]]
        # where data will be saved
        inUseObjects = dict()
        freeObjects = set()
        compressedObjects = dict()
        # start parsing
        for i in range(0, len(index) - 1, 2):
            start, count = index[i], index[i+1]
            # for each section..
            for j in range(count):
                # skip object 0, we will not used it
                if start == 0 and j == 0:
                    pos += sum(w)
                    continue
                # parse the current record in an array of three elements
                vals = [None] * 3
                for k in range(3):
                    if w[k] > 0:
                        vals[k] = sum([x << (w[k] - l - 1)*8 for l, x in enumerate(xrefData[pos:pos+w[k]])])
                        pos += w[k]
                
                # set default values, based on the record type
                if vals[0] is None:
                    vals[0] = 1
                if vals[0] == 1 and vals[2] is None:
                    vals[2] = 0
                
                # transform the record into a higher level object
                if vals[0] == 0:
                    # type 0 is assigned to free objects. We will not keep the linked list structure (which is
                    # redundant in our setting)
                    entry = (start + j, vals[2])
                    freeObjects.add(entry)
                elif vals[0] == 1:
                    # In use object
                    entry = XrefInUseEntry(vals[1], start + j, vals[2])
                    logging.debug("XrefInUseEntry: {}".format(entry))
                    inUseObjects[(entry.object_number, entry.generation_number)] = entry
                else:
                    # it is a compressed object
                    entry = XrefCompressedEntry(start + j, vals[1], vals[2])
                    logging.debug("XrefCompressedEntry: {}".format(entry))
                    compressedObjects[(entry.object_number, 0)] = entry
        logging.debug("Ended parsing xref stream.")
        return trailer, (inUseObjects, freeObjects, compressedObjects)


    def __parse_xref_section(self):
        # first, locate the trailer
        next(self._basic_parser._lexer)
        inUseObjects = dict()
        freeObjects = set()
        while isinstance(self._basic_parser._lexer.current_lexeme, int):
            start = self._basic_parser._lexer.current_lexeme
            if not isinstance(start, int):
                self._basic_parser._raise_syntax_error("Expected the ID of the fist object in section.")
            count = next(self._basic_parser._lexer)
            if not isinstance(count, int):
                self._basic_parser._raise_syntax_error("Expected the number of elements in the section.")
            # read all records in subsection
            for i in range(count):
                offsetToken = next(self._basic_parser._lexer)
                if not isinstance(offsetToken, int):
                    self._basic_parser._raise_syntax_error("Expected 'offset' value for xref entry.")
                genNumberToken = next(self._basic_parser._lexer)
                if not isinstance(genNumberToken, int):
                    self._basic_parser._raise_syntax_error("Expected 'generation_number' value for xref entry.")
                markerToken = next(self._basic_parser._lexer)
                if not isinstance(markerToken, PDFOperator) or markerToken.value not in ["n", "f"]:
                    self._basic_parser._raise_syntax_error("Expected 'in_use' specifier ('n' or 'f')")
                if start == 0 and i == 0:
                    continue # skip head of the free objects linked list  (will not be used)
                if markerToken.value == "n":
                    xrefEntry = XrefInUseEntry(offsetToken, start + i, genNumberToken)
                    logging.debug("xref entry: {}".format(xrefEntry))
                    inUseObjects[(xrefEntry.object_number, xrefEntry.generation_number)] = xrefEntry
                else:
                    xrefEntry = (start + i, genNumberToken - 1)
                    freeObjects.add(xrefEntry)
            next(self._basic_parser._lexer)
        # now there must be the trailer
        if not isinstance(self._basic_parser._lexer.current_lexeme, PDFKeyword) or self._basic_parser._lexer.current_lexeme.value != b'trailer':
            self._basic_parser._raise_syntax_error("Expecting 'trailer' section after 'xref' table.")
        next(self._basic_parser._lexer)
        trailer = self._basic_parser.parse_object()
        return trailer, (inUseObjects, freeObjects)
    

    def _stream_reader(self, D : 'dict', reader):
        filePath = D.get("F")
        if filePath is not None:
            raise PDFUnsupportedError("""
                Support for streams having data specified in an external file are not supported yet.
                Please consider sending to the developers the PDF that generated this exception so that
                they can work on supporting this feature. 
                """)
        
        # it is a stream object, lets find out its length
        length = D.get("Length")
        if length is None:
            self._basic_parser._raise_syntax_error("Stream dictionary lacks of 'Length' entry.")
        
        if isinstance(length, PDFReference):
            key = (length.object_number, length.generation_number)
            try:
                xrefEntity = self.xRefTable[key]
            except KeyError:
                logging.warning("Reference to non-existing object.")
                # TODO: now what?
                self._basic_parser._raise_syntax_error("Missing stream 'Length' property.")
            length = self.parse_xref_entry(xrefEntity).value

        if not isinstance(length, int):
            self._basic_parser._raise_syntax_error("The object referenced by 'Length' is not an integer.")
        
        def completeReader():
            data = reader(length)
            if isinstance(data, memoryview):
                data = bytes(data)
            return decode(D, {}, data)
        
        return length, completeReader
             
