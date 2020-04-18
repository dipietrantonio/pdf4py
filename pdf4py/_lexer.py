import logging
from ._charset import *
from .types import *
import _io
from .exceptions import PDFLexicalError


class Seekable:
    """
    Wrapper class to give a seek/tell/read interface to bytes and bytearray objects.
    """

    def __init__(self, obj):
        if not(isinstance(obj, bytes) or isinstance(obj, bytearray)):
            raise ValueError("'obj' must be of type 'bytes' or 'bytearray'.")
        self.__source = memoryview(obj)
        self.__pos = 0
        self.__len = len(obj)
    

    def read(self, n = 0):
        if self.__pos == self.__len:
            return b''
        if n == 1:
            val = [self.__source[self.__pos]]
        else:
            if n <= 0:
                n = self.__len
            val = self.__source[self.__pos : self.__pos + n]
            n = len(val)
        self.__pos += n
        return val
    


    def seek(self, off, whence):
        if whence == 0:
            self.__pos = off
        elif whence == 1:
            self.__pos += off
        else:
            self.__pos = self.__len + off
        
        if self.__pos < 0:
            self.__pos = 0
        if self.__pos > self.__len:
            self.__pos = self.__len
    

    def tell(self):
        return self.__pos



class Lexer:
    """
    A lexical analyzer, in short lexer, is a software that takes as input a sequence of characters 
    and transforms it in a sequence of meaningful atomic language symbols, called lexemes, defined 
    in the associated language grammar. In our case, the input is a sequence of bytes read from a 
    file and the output is a sequence composed by simple PDF objects, such as strings, names, 
    numbers, booleans, and other symbols that are used to define more complex objects, namely 
    dictionaries, arrays and streams.

    The Lexer class implements the __next__ and __iter__ dunder methods to iterate over the lexemes 
    that are present in the input bytes sequence. It also give to the user methods to move around
    the input sequence to allow lazy parsing (i.e. to parse only the required lexemes). 
    """

    def __init__(self, source, contextSize = 200):
        """
        Creates a new instance of a PDF lexical analyzer associated to the given source sequence of
        bytes.


        Parameters
        ----------
        source : (read/tell/seek)-supporting type, bytes or bytearray
            The source from where bytes are read.
        
        contextSize : int
            The size of the context that will be collected if `get_context` is called.
        """

        if isinstance(source, bytes) or isinstance(source, bytearray):
            self.__source = Seekable(source)
        elif isinstance(source, _io.BufferedReader):
            self.__source = source
        else:
            raise ValueError("The parser is given an invalid source of bytes.")
        
        cpos = self.__source.tell()
        self.__source.seek(0, 2)
        self.__length = self.__source.tell()
        self.__source.seek(cpos, 0)
        self.__head = self.__source.read(1)
        if self.__head == b"":
            self.__head = ord(' ')
            self.__ended = True
        else:
            self.__ended = False
            self.__head = self.__head[0]

        self.__lexemesBuffer = list()
        self.__movesHistory = list()
        self.__contextSize = contextSize
        self.__current_lexeme = None
    

    @property
    def source(self):
        return self.__source


    @property
    def current_lexeme(self):
        """
        Returns
        -------
        lex : a Python object
            The last parsed lexeme.
        """
        return self.__current_lexeme
    

    def rfind(self, keyword : 'bytes'):
        """
        Searches a sequence of bytes starting from the end of the input bytes sequence.


        Parameters
        ----------
        keyword : bytes
            The sequence of bytes to search for.
        

        Returns
        -------
        pos : int
            The starting position of the sequence if found, `-1` otherwise.
        """
        revKeyword = bytes(reversed(keyword))
        buff = bytearray()
        count = 1
        while bytes(buff) != revKeyword:
            buff.clear()
            while count <= self.__length:
                self.__source.seek(self.__length - count, 0)
                c = self.__source.read(1)[0]
                count += 1
                if c not in [CARRIAGE_RETURN, LINE_FEED]:
                    buff.append(c)
                else:
                    break
            if c in [CARRIAGE_RETURN, LINE_FEED]:
                c = None
                continue
            if count > self.__length:
                return -1
        pos = self.__source.tell()
        self.__advance()
        self.__next__()
        return pos


    def get_context(self):
        """
        Returns the bytes near the Lexer's current head position.

        Notes
        -----
        Given a context size of `C` bytes, and the current head position `P`, the function returns the 
        bytes sequence starting from the byte at position `max(P - C // 2, 0)` whose length is at most
        `C`.


        Returns
        -------
        context : bytes
            A bytes sequence representing the content around the Lexer's head position.

        errorPosition : int
            Position in the input stream where the error occurred.
        
        errorRelativePosition : int
            Position in the context sequence where the error occurred.
        """
        # collect the context in which the error occurred
        errorPosition = self.__source.tell()
        contextSideSize = self.__contextSize // 2
        contextStart = errorPosition - contextSideSize
        if contextStart < 0:
            contextSideSize = contextSideSize + contextStart
            contextStart = 0
        self.__source.seek(contextStart, 0)
        context = self.__source.read(self.__contextSize)
        if isinstance(context, memoryview):
            context = bytes(context)
        # escaped occurrences occupy 2 spaces instead of one, when printed as bytes.
        escapedOccurrences = sum(context[:contextSideSize].count(x) for x in STRING_ESCAPE_SEQUENCES.values())
        errorRelativePosition = contextSideSize + escapedOccurrences + 1
        self.__source.seek(errorPosition, 0)
        return context, errorPosition, errorRelativePosition

        
    def __raise_lexer_error(self, msg):
        """
        Called when a lexical error is encountered during the input tokenization, for example when an
        unrecognized character is found.

        This function collects also the input sequence around the position where the error happened, 
        enriching the original error message given as input, so that the exception carries a more 
        informative error message for the user.

        Parameters
        ----------
        msg : str
            A description of the lexical error.
        
        Raises
        ------
        PDFLexicalError
        """
        # collect the context in which the error occurred
        context, errorPosition, relativeErrorPosition = self.get_context()
        finalMsg = "{}\n\nPosition {}, context:\n\t{}\n\t{}^".format(msg, errorPosition, context,
            " "*relativeErrorPosition)
        raise PDFLexicalError(finalMsg)


    def move_at_position(self, pos):
        """
        Moves the Lexer's head to the new position `pos` and extracts the lexeme starting at that
        position, Also, saves the current position and lexeme into a stack so that they can be
        restored in future.


        Parameters
        ----------
        pos : int
            The position where to move to.
        

        Returns
        -------
        lex : A Python object
            The lexeme extracted starting from position `pos`.
        """
        previousLexeme = self.current_lexeme
        previousPosition = self.__source.tell()
        self.__movesHistory.append((previousLexeme, previousPosition))
        self.__source.seek(pos, 0)
        self.__advance()
        return self.__next__()


    def move_back(self):
        """
        Moves the Lexer's head back to the position it was before the last `move_at_position`
        method call.
        """
        if len(self.__movesHistory) == 0:
            raise Exception("No move in history")
        prevLex, prevPos = self.__movesHistory.pop()
        self.__current_lexeme = prevLex
        self.__source.seek(prevPos - 1, 0)
        self.__advance()


    def __advance(self, k = 1):
        """
        Advance the Lexer's head of `k` positions.

        Parameters
        ----------
        k : int
            Number of position the Lexer's head must be moved.
        """
        if self.__ended:
            raise StopIteration()
        self.__head = self.__source.read(k)
        if len(self.__head) < k:
            self.__head = ord(' ')
            self.__ended = True
        else:
            self.__head = self.__head[-1]


    def __remove_blanks(self):
        """
        Removes all the characters that are ignored in the PDF grammar starting from the current
        position until the next meaningful character position.
        """
        while True:
            if self.__head in BLANKS:
                self.__advance()
            elif self.__head == PERCENTAGE: # comment starts
                while self.__head != LINE_FEED:
                    self.__advance()
                self.__advance()
            else:
                break


    def __peek(self, k = 1):
        """
        Takes a look at the byte at position `currentPos + k` without modifying the Lexer's head
        position.


        Parameters
        ----------
        k : int
            Offset from the current position to the position to peek at.
        

        Returns
        -------
        current_byte : int
            The peeked byte
        """
        k -= 1
        currentPos = self.__source.tell()
        if currentPos + k >= self.__length:
            return None
        else:
            self.__source.seek(k, 1)
            v = self.__source.read(1)
            self.__source.seek(currentPos, 0)
            return v[0]
    

    def __extract_string_literal(self):
        """
        Extracts a string literal from the input bytes sequence.

        Returns
        -------
        successful : bool
            `successful` is set to `True` if the method executes without
            errors, `False` otherwise.
        """
        self.__advance()
        openParentheses = 1
        buffer = bytearray()
        while openParentheses > 0:
            if self.__head == OPEN_PARENTHESIS:
                openParentheses += 1
            elif self.__head == CLOSE_PARENTHESIS:
                openParentheses -= 1
            elif self.__head == BACK_SLASH:
                # parse special content (escaped sequence)
                self.__advance()
                if not is_digit(self.__head):
                    # then it must be one of the blanks like: \n, \r, \t etc..
                    buffer.append(STRING_ESCAPE_SEQUENCES.get(self.__head, self.__head))
                    self.__advance()
                    continue
                else:
                    # otherwise it is an octal number
                    digits = bytearray()
                    while is_digit(self.__head) and len(digits) < 3:
                        digits.append(self.__head)
                        self.__advance()
                    charCode = sum(int(x) << 3*(len(digits) -i - 1) for i, x in enumerate(digits.decode('ascii')))
                    buffer.append(charCode)
                    continue
            buffer.append(self.__head)
            self.__advance()
        buffer.pop()
        return PDFLiteralString(bytes(buffer))
        

    def __extract_hexadecimal_string(self):
        """
        Extracts a hexadecimal digits sequence from the input bytes sequence.


        Returns
        -------
        successful : bool
            `successful` is set to `True` if the method executes without
            errors, `False` otherwise.
        """
        self.__advance()
        buffer = bytearray()
        while True:
            if self.__head in BLANKS:
                self.__advance()
                continue
            if not is_hex_digit(self.__head):
                break
            buffer.append(self.__head)
            self.__advance()
        if self.__head != CLOSE_ANGLE_BRACKET:
            self.__raise_lexer_error("Expected '>' to end hexadecimal string.")
        self.__advance()
        return PDFHexString(bytes(buffer))

            
    def __extract_name_or_operator(self):
        """
        Extracts a PDF name object from the input bytes sequence.


        Returns
        -------
        successful : bool
            `successful` is set to `True` if the method executes without
            errors, `False` otherwise.
        """
        buffer = bytearray()
        while ord('!') <= self.__head and self.__head <= ord('~') and self.__head not in DELIMITERS:
            if self.__head == NUMBER_SIGN:
                self.__advance()
                try:
                    hexDigit1 = hex_to_number(self.__head)
                    self.__advance()
                    hexDigit2 = hex_to_number(self.__head)
                    hexNum = (hexDigit1 << 4) + hexDigit2
                    buffer.append(hexNum)
                except ValueError:
                    self.__raise_lexer_error("'{}' is not an hexadecimal digit.".format(self.__head))
            else:
                buffer.append(self.__head)
            self.__advance()
        return buffer.decode('utf8')


    def __extract_number(self, startsWithNumber):
        """
        Extracts an integer or real value from the input bytes sequence.


        Returns
        -------
        successful : bool
            `successful` is set to `True` if the method executes without
            errors, `False` otherwise.
        """
        buff = bytearray()
        if self.__head == PLUS or self.__head == MINUS:
            buff.append(self.__head)
            self.__advance()
        
        while is_digit(self.__head):
            buff.append(self.__head)
            self.__advance()
        
        if self.__head == POINT:
            buff.append(POINT)
            self.__advance()
        else:
            if not startsWithNumber and len(buff) == 1:
                self.__raise_lexer_error("unexpected bytes sequence encountered.")
            else:
                return int(buff.decode('utf-8'))
        
        while is_digit(self.__head):
            buff.append(self.__head)
            self.__advance()
        
        if not startsWithNumber and len(buff) == 1:
            self.__raise_lexer_error("unexpected bytes sequence encountered.")
        else:
            return float(buff.decode('utf-8'))
        
    
    def __extract_literal(self, lit):
        """
        Extracts the specified sequence of bytes starting from the current position.


        Parameters
        ----------
        lit : bytes
            The sequence of bytes to be extracted from the input bytes sequence.
        

        Returns
        -------
        successful : bool
            `successful` is set to `True` if the method executes without
            errors, `False` otherwise.
        """
        diff = False
        for i, l in enumerate(lit):
            p = self.__peek(i)
            if p != l:
                diff = True
                break
        if not diff:
            # ok, we matched it
            self.__advance(len(lit))
            return True
        else:
            return False


    def __extract_keyword(self):
        """
        Extracts one of the PDF language keywords.


        Returns
        -------
        successful : bool
            `successful` is set to `True` if the method executes without
            errors, `False` otherwise.
        """
        for k in KEYWORDS:
            if self.__extract_literal(k):
                self.__current_lexeme = PDFKeyword(k)
                return True
        else:
            return False


    def __extract_stream_reader(self):
        """
        Extracts the stream keyword and defines a function that will read the stream content once its
        length is known.

        
        Returns
        -------
        A PDFStreamReader object, containing a callable that will return the stream content when called.
        """
        # check whether there are the optional \r\n
        if self.__head == CARRIAGE_RETURN:
            self.__advance()
            if self.__head != LINE_FEED:
                self.__raise_lexer_error("Carriage return not followed by a line feed after 'stream' keyword.")
        streamPos = self.__source.tell()
        # build a closure to read the stream later
        def read_stream(length):
            oldEnded = self.__ended
            self.__ended = False
            oldPos = self.__source.tell()
            self.__source.seek(streamPos, 0)
            data = self.__source.read(length)
            self.__advance()
            # now need to match endstream, or line feed + endstream
            if self.__head == LINE_FEED:
                self.__advance()
            self.__source.seek(oldPos, 0)
            self.__ended = oldEnded
            return data

        return PDFStreamReader(read_stream)
        

    def __iter__(self):
        """
        Makes a Lexer Analyzer instance an iterable object.

        Usually this is a bad idea, but here can be ok.
        """
        return self
    

    def __next__(self):
        """
        Returns the next lexeme in the input bytes sequence. Also, set current_lexeme property 
        to the parsed lexeme.

        The Lexical Analyzer is an iterator over the sequence of lexemes present in the input
        bytes sequence. For this reason the user can use the built-in `next` function to get
        the next lexeme in the sequence. StopIteration is raised when the end of the bytes 
        sequence is reached.
        

        Returns
        -------
        lex : str, int, float, bool, function, PDFOperator, PDFKeyword, PDFHexString, PDFSingleton.
            The next lexeme from the byte sequence.

        Raises
        ------
        `StopIteration` on End-Of-Sequence, `PDFLexicalError` when an unexpected input byte is
        encountered.
        """

        if len(self.__lexemesBuffer) > 0:
            self.__current_lexeme = self.__lexemesBuffer.pop()
            return self.__current_lexeme

        self.__remove_blanks()
        # now try to parse lexical entities
        if self.__head == OPEN_PARENTHESIS:
            self.__current_lexeme = self.__extract_string_literal()
    
        elif self.__head == OPEN_ANGLE_BRACKET and self.__peek() != OPEN_ANGLE_BRACKET:
            # If the next bytes had been another OPEN_ANGLE_BRACKET then we would have gotten
            # a "dictionary starts here" mark 
            self.__current_lexeme = self.__extract_hexadecimal_string()

        elif self.__head == FORWARD_SLASH:
            self.__advance()
            item = self.__extract_name_or_operator()
            self.__current_lexeme = item 
        
        elif is_digit(self.__head):
            self.__current_lexeme = self.__extract_number(startsWithNumber=True)

        elif self.__head in [PLUS, MINUS, POINT]:
            self.__current_lexeme = self.__extract_number(startsWithNumber=False)

        elif self.__extract_literal(b"true"):
            self.__current_lexeme = True
        
        elif self.__extract_literal(b"false"):
            self.__current_lexeme = False
        
        elif self.__extract_literal(b"stream"):
            self.__current_lexeme = self.__extract_stream_reader()

        elif self.__extract_literal(b"<<"):
            self.__current_lexeme = PDFDictDelimiter(b"<<")
        
        elif self.__extract_literal(b">>"):
            self.__current_lexeme = PDFDictDelimiter(b">>")
        
        elif self.__extract_literal(b"null"):
            self.__current_lexeme = None
        
        elif self.__extract_keyword():
            # self.__current_lexeme is set inside the called function
            pass
        
        elif self.__head in SINGLETONS:
            self.__current_lexeme = PDFSingleton(self.__head)
            self.__advance()
        
        elif ord('!') <= self.__head and self.__head <= ord('~') and self.__head not in DELIMITERS:
            item = self.__extract_name_or_operator()
            self.__current_lexeme = PDFOperator(item)
            
        else:
            # If the input bytes sequence prefix doesn't match anything known, then...
            raise self.__raise_lexer_error("Invalid characters sequence in input stream: '{}'.".format(chr(self.__head)))

        return self.__current_lexeme


    def undo_next(self, item):
        """
        Reverts the Lexer's head position the one before the last call to __next__.

        Sometimes it is useful for the Lexer user to undo the calls to __next__ because it
        may not be able to handle the particular extracted lexeme sequence (which maybe has
        to be handled by another actor). While parsing a PDF, this may happen when 2 integers
        have been extracted from the input and the third lexeme will decide if an indirect 
        reference has been parsed (meaning the third lexeme is 'R') or just three integers.
        In the latter case, we want to return just an integer, so the third one is put in a
        buffer, the second one is set as the current lexeme (after having parsed the first
        number), and the first number is returned. For more information look at the parser
        module.
        """
        self.__lexemesBuffer.append(self.__current_lexeme)
        self.__current_lexeme = item
