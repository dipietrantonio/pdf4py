import logging
from contextlib import suppress
from functools import lru_cache, partial
from ._lexer import *
from ._decoders import decode
from ._security.securityhandler import StandardSecurityHandler
from .exceptions import PDFSyntaxError, PDFUnsupportedError



class XRefTable:
    """
    Implements the functionalities of a Cross Reference Table.
    
    The Cross Reference Table (XRefTable) is the index of all the PDF objects in a PDF file. An object
    is uniquely identified with a tuple `(s, g)` where `s` is the sequence number and `g` is the
    generation number. There are mainly two types of entries in such table:

    - `XrefInUseEntry` entries that represent objects that are part of the PDF document's current 
      structure, and
    - `tuple` entries pointing at *free objects*, objects that are no longer used (for example,
      they have been eliminated in a modification of the document).
    - `XrefCompressedEntry` entries that are objects in use but stored in a compressed stream.

    The listed three object types are to be used with the `Parser.parse_reference` class method
    to actually retrieve the associated object.

    There are two main ways to query a `XRefTable` instance:

    - Iterating over the instance itself to get references to *in use* and *compressed* objects
      (but *not* free objects).
    - Accessing a particular entry using the square brackets. A bidimentional index is used, 
      representing the sequence and generation numbers. This is because it implements the __getitem__ 
      method that is used by the parser to look up objects if required during the parsing process.

    """
    def __init__(self, previous : 'XRefTable', inuse_objects : 'dict', free_objects : 'set',
            compressed_objects : 'dict' = None):
        self.__inuse_objects = inuse_objects
        self.__free_objects = free_objects
        self.__compressed_objects = {} if compressed_objects is None else compressed_objects
        self.__previous = previous
        

    @property
    def previous(self):
        """
        Points to the `XRefTable` instance that is associated to the `/Prev` key in the trailer
        dictionary of the current cross-reference table.
        """
        return self.__previous


    def __getitem__(self, key : 'tuple'):
        """
        Returns a cross-reference table entry corresponding to the sequence and generation numbers
        given as input.

        Parameters
        ----------
        key : tuple
            `key = (seq, gen)` is the tuple containing the sequence and generation numbers used
            to identify the object.
        
        Returns
        -------
        
        entry : `XrefInUseEntry` or `XrefCompressedEntry`
            If an in use entry is found,
        or

        None : NoneType
            if the required object has been freed.

        Raises
        ------
        `KeyError` if no entry corresponds to the given key.
        """
        v = self.__inuse_objects.get(key)
        if v is not None:
            return v
        v = self.__compressed_objects.get(key)
        if v is not None:
            return v
        if key in self.__free_objects:
            return None
        if self.__previous is None:
            raise KeyError("Key not found: " + str(key))
        else:
            return self.__previous[key]
    
    
    def __iter__(self):
        """
        Returns
        -------
        gen : generator
            a generator over the in use entries.
        """ 
        def gen():
            if self.previous is not None:
                for item in iter(self.previous):
                    if isinstance(item, XrefInUseEntry) and (item[1], item[2]) in self.__free_objects:
                        pass
                    yield item
            yield from self.__inuse_objects.values()
            yield from self.__compressed_objects.values()
        return gen()

    
    def __support_str_(self):
        """
        Support method to generate a string representation of the table.
        """

        inuse_objs = "\n".join(
            "{:10} {:5} {:10} n".format(x.object_number, x.generation_number, x.offset) for x in sorted(self.__inuse_objects.values())
            )
        free_objs = "\n".join(
            "{:10} {:5} f".format(x[0], x[1] + 1) for x in sorted(self.__free_objects)
            )
        compressed_objs = "\n".join(
            "{} {}".format(x[0], x[1]) for x in sorted(self.__compressed_objects.values())
            )
        
        resulting_string = "Section\nIn use objects:\n{}\nFree objects:\n{}\nCompressed objects:\n{}".format(
            inuse_objs, free_objs, compressed_objs)
        
        if self.__previous is not None:
            prev_string = self.__previous.__support_str_()
            return prev_string + "\n" + resulting_string
        else:
            return resulting_string


    def __str__(self):
        # TODO: build a better representation
        return self.__support_str_()



class SequentialParser:
    """
    Implements a parser that is able to parse a PDF objects by scanning the input bytes sequence.
    
    In other words, objects are extracted in the order they appear in the stream. For this
    reason it is used to parse *Content Streams*.

    Note that this class is not able to parse a complete PDF file since the process requires
    random access in the file to retrieve information when required (for example to resolve a 
    reference pointing at the Integer holding the length of a stream). However, this class is
    used in defining the more powerful `Parser`.

    The constructor that must be used by users takes a positional argument, `source`, being
    the source bytes stream. It can by a `byte`, `bytearray` or a file pointer opened in
    binary mode. Other keyword arguments are used internally in pdf4y, specifically by 
    the `Parser` class.
    """


    def __init__(self, source, **kwargs):
        """
        Initialize the parser by setting the underlying lexical analyzer and load the fist lexeme.
        From now on the following invariant must be kept: before any call the to 
        `SequentialParser.parse_object` class method, the `current_lexeme` property of the
        lexer must be set to the fist unprocessed lexeme in the input.
        """
        # read the header
        self._lexer = Lexer(source)
        self._stream_reader = kwargs.get('stream_reader', None)
        self._security_handler = None
        self.__ended = False
        self.__content_stream_mode = kwargs.get('content_stream_mode', True)
        try:
            next(self._lexer)
        except StopIteration:
            logging.debug("File is empty.")
            self.__ended = True
        

    def _raise_syntax_error(self, msg : 'str'):
        """
        Raises an exception with a message containing the string `msg` accompanied with
        the context of where the associated exception has happened (the Lexer's head current position).
        """
        context, error_position, relative_error_position = self._lexer.get_context()
        final_msg = "{}\n\nPosition {}, context:\n\t{}\n\t{}^".format(msg, error_position, context,
            " "*relative_error_position)
        raise PDFSyntaxError(final_msg)
    

    def __iter__(self):
        return self


    def __next__(self):
        """
        Returns the next PDF object.
        """
        return self.parse_object()


    def parse_object(self, obj_num : 'tuple' = None):
        """
        Parse the next PDF object from the token stream.

        Parameters
        ----------
        obj_num : tuple
            Tuple `(seq, gen)`, `seq` and `gen` being the sequence and the generation number
            of the object that is going to be parsed respectively. These values are known when the
            parsing action is instructed after a XRefTable lookup. This parameter is used only by
            the `Parser` class when the PDF is encrypted.
        
        Returns
        -------
        obj : one of the PDF types defined in module `types`
            The parsed PDF object.
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
                L.append(self.parse_object(obj_num))
            # we have successfully parsed a list
            # remove CLOSE_SQUARE_BRACKET token stream from stream
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
                elif not isinstance(keyToken, str):
                    self._raise_syntax_error("Expecting dictionary key, '{}' found instead.".format(keyToken))
                
                # now get the value
                next(self._lexer)
                keyValue = self.parse_object(obj_num)    
                D[keyToken] = keyValue
            
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
            length, reader = self._stream_reader(D, bytesReader, obj_num)

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
    
        elif isinstance(self._lexer.current_lexeme, (PDFHexString, PDFLiteralString, bool, float, str)):
            s = self._lexer.current_lexeme
            try:
                next(self._lexer)
            except StopIteration:
                self.__ended = True

            if isinstance(s, (PDFHexString, PDFLiteralString)) and obj_num is not None and self._security_handler is not None:
                s = s.__class__(self._security_handler.decrypt_string(s.value, obj_num))
                
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
                o = self.parse_object(obj_num)
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
    Parse a PDF document to retrieve PDF objects composing it.

    The constructor takes as argument an object `source`, the sequence of bytes the PDF document 
    is encoded into. It can be of type `bytes`, `bytearray` or file pointer opened for reading
    in binary mode. Optionally, the second argument is the password to be provided if the document
    is protected through encryption (if encrypted with AESV3, the password is of type `str`, else `bytes`).
    For example,

    ::

        >>> from pdf4py.parser import Parser
        >>> with open('path/to/file.pdf', 'rb') as fp:
        >>>     parser = Parser(fp)
    
    
    Creates a new instance of `Parser`. The constructor reads the Cross Reference Table of the
    PDF document to retrieve the list of PDF objects that are present and parsable in the document.
    The Cross Reference Table is then available as attribute of the newly created `Parser`
    instance. For more information about the cross reference table, see the `XRefTable`
    documentation.

    After the instantiation, `parser` will have a `XRefTable` instance associated to the attribute
    `xreftable`. To retrieve PDF objects pass entries in the table to the `Parser.parse_reference`
    method.
    """
    TRAILER_FIELDS = {"Root", "ID", "Size", "Encrypt", "Info", "Prev"}


    def __init__(self, source, password = None):
        self._basic_parser = SequentialParser(source, stream_reader = self._stream_reader, content_stream_mode = False)
        self._read_header()
        self.__parse_xref_table()
        encryption_dict = self.trailer.get("Encrypt")
        if encryption_dict is not None:
            if isinstance(encryption_dict, PDFReference):
                encryption_dict = self.parse_reference(encryption_dict)
            self._security_handler = StandardSecurityHandler(password, encryption_dict, self.trailer.get("ID"))
        else:
            self._security_handler = None
        self._basic_parser._security_handler = self._security_handler


    def _read_header(self):
        """
        Reads the PDF header to retrive the standard used.
        """
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
        logging.debug("_read_header finished.")
    

    @lru_cache(maxsize=256)
    def parse_reference(self, reference):
        """
        Parse and retrieve the PDF object `xref_entry` points to.

        Notes
        -----
        PDF objects are not parsed when an instance of `Parser` is being created. Instead,
        parsing occurs when this method is called. To avoid that the same object is being
        parsed too many times, a LRU cache is being used to keep in memory the last 256
        parsed objects.

        Parameters
        ----------
        reference : XrefInUseEntry or XrefCompressedEntry or PDFReference
            An entry in the XRefTable or a PDFReference object pointing to a PDFObject within
            the file that has to be parsed.

        Returns
        -------
        obj : one of the types used to represent a PDF object.
            The parsed PDF object.
        
        Raises
        ------
        `ValueError` if `reference` object type is not a valid one.
        """
        logging.debug("parse_reference with input: " + str(reference))
        if isinstance(reference, PDFReference):
            logging.debug("It is a PDFReference")
            reference = self.xreftable[reference]
        
        if isinstance(reference, XrefInUseEntry):
            logging.debug("it is an XrefInUSeEntry")
            self.__current_obj_num = (reference.object_number, reference.generation_number)
            self._basic_parser._lexer.move_at_position(reference.offset)
            parsedObject = self._basic_parser.parse_object(self.__current_obj_num).value
            self._basic_parser._lexer.move_back()
            logging.debug("pasing the XrefInUseEntry finished.")
            return parsedObject
        
        elif isinstance(reference, XrefCompressedEntry):
            # now parse the object stream containing the object the entry refers to
            logging.debug("It is a Xref Compressed Entry.")
            stream_token = self.parse_reference(PDFReference(reference.objstm_number, 0))
            logging.debug("Stream token: " + str(stream_token))
            D, stream_reader = stream_token
            stream = stream_reader()
            logging.debug("Stream got: " + str(stream))
            prev_basic_parser = self._basic_parser
            self._basic_parser = SequentialParser(stream, stream_reader = self._stream_reader, content_stream_mode = False)
            obj = None
            for i in range(D["N"]):
                n1 = self._basic_parser.parse_object()
                n2 = self._basic_parser.parse_object()
                if not(isinstance(n1, int) and isinstance(n2, int)):
                    self._basic_parser._raise_syntax_error("Expected integers in object stream.")
                if n1 == reference.object_number:
                    offset = D["First"] + n2
                    self._basic_parser._lexer.move_at_position(offset)
                    obj = self._basic_parser.parse_object(self.__current_obj_num)
                    break
            if obj is None:
                self._basic_parser._raise_syntax_error("Compressed object not found.")
            self._basic_parser = prev_basic_parser
            logging.debug("setting back the parser.")
            return obj
        else:
            raise ValueError("Argument type not supported.")


    def __parse_xref_table(self):
        # fist, find xrefstart, starting from end of file
        xrefstartpos = self._basic_parser._lexer.rfind(b"startxref")
        if xrefstartpos < 0:
            self._basic_parser._raise_syntax_error("'startxref' keyword not found.")
        # get the position of the latest xref section
        xrefpos = next(self._basic_parser._lexer)
        # the following list will hold all the xref sections found in the PDF file.
        xrefs = []
        self.trailer = dict()
        while xrefpos >= 0: # while there are xref to process
            current_lexeme = self._basic_parser._lexer.move_at_position(xrefpos)
            if isinstance(current_lexeme, PDFKeyword) and current_lexeme.value == b"xref":
                logging.debug("Parsing an xref table..")
                # then it is a classic xref table, as opposed to xref streams
                trailer, xref_data = self.__parse_xref_section()
                xrefs.insert(0, xref_data)
                # Check now if this is a PDF in compatibility mode where there is xref stream
                # reference in the trailer.          
                xrefstm_pos = trailer.get("XRefStm")
                if xrefstm_pos is not None:
                    logging.debug("Found a xref stream reference in trailer of xref table..")
                    self._basic_parser._lexer.move_at_position(xrefstm_pos)
                    _, xref_data_stream = self.__parse_xref_stream()
                    xrefs.insert(0, xref_data_stream)
            else:
                # it can only be a xref stream
                logging.debug("Parsing an xref stream..")
                trailer, xref_data = self.__parse_xref_stream()
                xrefs.insert(0, xref_data)
                
            # now process them
            if "Prev" in trailer:
                xrefpos = trailer["Prev"]
                del trailer["Prev"]
            else:
                xrefpos = -1
            self.trailer.update(trailer)

        # now build a hierarchy of XrefTable instances
        self.xreftable = None
        for xref_data in xrefs:
            self.xreftable = XRefTable(self.xreftable, *xref_data)


    def __parse_xref_stream(self):
        """
        Beginning with PDF 1.5, cross-reference information may be stored in a cross-reference
        stream instead of in a cross-reference table. Cross-reference streams provide the 
        following advantages:
        
        - A more compact representation of cross-reference information,
        - The ability to access compressed objects that are stored in object streams 
            (see 7.5.7, "Object Streams") and to allow new cross-reference entry types to be added
            in the future
        """
        logging.debug("Parsing a xref stream..")
        o = self._basic_parser.parse_object()
        if not isinstance(o, PDFIndirectObject):
            self._basic_parser._raise_syntax_error("Expecting a 'xref' rection, but it has not been found.")
        if not isinstance(o.value, PDFStream):
            self._basic_parser._raise_syntax_error("Expecting a stream containing 'xref' information, but not found.")
        objstm_dict, objstm = o.value
        if objstm_dict['Type'] != 'XRef':
            self._basic_parser._raise_syntax_error("Expecting a stream containing 'xref' information, but not found.")
        trailer = {k : objstm_dict[k] for k in objstm_dict if k in self.TRAILER_FIELDS}
        # read the raw stream content
        xrefdata = objstm()
        logging.debug("xref stream: " + str(xrefdata))
        # current position inside xrefData
        pos = 0
        # retrieves info about xref stream layout
        # TODO: support extends keyword
        if "Extends" in objstm_dict:
            logging.warning("""
            'Extends' keyword found in a object stream dictionary, but it is not supported yet.
            Consider sending the file you are parsing to the developers of the library."""
            )
        size = objstm_dict["Size"]
        index = objstm_dict.get("Index", [0, size])
        # An array of integers representing the size of the fields in a single cross-reference entry.
        w = [x for x in objstm_dict["W"]]
        # where data will be saved
        inuse_objects = dict()
        free_objects = set()
        compressed_objects = dict()
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
                        vals[k] = sum([x << (w[k] - l - 1)*8 for l, x in enumerate(xrefdata[pos:pos+w[k]])])
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
                    free_objects.add(entry)
                elif vals[0] == 1:
                    # In use object
                    entry = XrefInUseEntry(vals[1], start + j, vals[2])
                    logging.debug("XrefInUseEntry: {}".format(entry))
                    inuse_objects[(entry.object_number, entry.generation_number)] = entry
                else:
                    # it is a compressed object
                    entry = XrefCompressedEntry(start + j, vals[1], vals[2])
                    logging.debug("XrefCompressedEntry: {}".format(entry))
                    compressed_objects[(entry.object_number, 0)] = entry
        logging.debug("Ended parsing xref stream.")
        return trailer, (inuse_objects, free_objects, compressed_objects)


    def __parse_xref_section(self):
        # first, locate the trailer
        next(self._basic_parser._lexer)
        inuse_objects = dict()
        free_objects = set()
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
                gennumber_token = next(self._basic_parser._lexer)
                if not isinstance(gennumber_token, int):
                    self._basic_parser._raise_syntax_error("Expected 'generation_number' value for xref entry.")
                marker_token = next(self._basic_parser._lexer)
                if not isinstance(marker_token, PDFOperator) or marker_token.value not in ["n", "f"]:
                    self._basic_parser._raise_syntax_error("Expected 'in_use' specifier ('n' or 'f')")
                if start == 0 and i == 0:
                    continue # skip head of the free objects linked list  (will not be used)
                if marker_token.value == "n":
                    xrefentry = XrefInUseEntry(offsetToken, start + i, gennumber_token)
                    logging.debug("xref entry: {}".format(xrefentry))
                    inuse_objects[(xrefentry.object_number, xrefentry.generation_number)] = xrefentry
                else:
                    xrefentry = (start + i, gennumber_token - 1)
                    free_objects.add(xrefentry)
            next(self._basic_parser._lexer)
        # now there must be the trailer
        if not isinstance(self._basic_parser._lexer.current_lexeme, PDFKeyword) or self._basic_parser._lexer.current_lexeme.value != b'trailer':
            self._basic_parser._raise_syntax_error("Expecting 'trailer' section after 'xref' table.")
        next(self._basic_parser._lexer)
        trailer = self._basic_parser.parse_object()
        return trailer, (inuse_objects, free_objects)
    

    def _stream_reader(self, D : 'dict', reader, obj_num : 'tuple' = None):
        file_path = D.get("F")
        if file_path is not None:
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
                xrefentity = self.xreftable[key]
            except KeyError:
                logging.warning("Reference to non-existing object.")
                # TODO: now what?
                self._basic_parser._raise_syntax_error("Missing stream 'Length' property.")
            length = self.parse_reference(xrefentity)

        if not isinstance(length, int):
            self._basic_parser._raise_syntax_error("The object referenced by 'Length' is not an integer.")

        def complete_reader():
            data = reader(length)
            # TODO: improve this
            if isinstance(data, memoryview):
                data = bytes(data)
            if D.get('Type') != 'XRef' and self._security_handler is not None:
                try:
                    data = self._security_handler.decrypt_stream(data, D, obj_num)
                except Exception as e:
                    self._basic_parser._raise_syntax_error("Error while decrypting data: " + str(e))
            try:
                return decode(D, data)
            except Exception as e:
                self._basic_parser._raise_syntax_error("Error while decoding data: " + str(e))
            
        return length, complete_reader
             
