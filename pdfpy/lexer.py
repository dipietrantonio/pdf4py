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


from collections import namedtuple

class LexerError(Exception):
    """
    LexerError
    """

BLANKS = {0x00, 0x09, 0x0A, 0x0C, 0x0D, 0x20}
LINE_FEED = 10
CARRIAGE_RETURN = 13
OPEN_PARENTHESIS = 40
CLOSE_PARENTHESIS = 41
OPEN_ANGLE_BRACKET = 60
CLOSE_ANGLE_BRACKET = 62
OPEN_SQUARE_BRACKET = 91
CLOSE_SQUARE_BRACKET = 93
FORWARD_SLASH = 47
OPEN_CURLY_BRACKET = 123
CLOSE_CURLY_BRAKET = 125
PERCENTAGE = 37
POINT = 46
PLUS = 43
MINUS = 45
KEYWORD_REFERENCE = 82


DELIMITERS = {
    OPEN_PARENTHESIS, CLOSE_PARENTHESIS, OPEN_ANGLE_BRACKET, CLOSE_ANGLE_BRACKET,
    OPEN_SQUARE_BRACKET, CLOSE_SQUARE_BRACKET, FORWARD_SLASH, PERCENTAGE,
    OPEN_CURLY_BRACKET, CLOSE_CURLY_BRAKET
}

SINGLETONS = {
    OPEN_CURLY_BRACKET, CLOSE_CURLY_BRAKET, OPEN_SQUARE_BRACKET, CLOSE_SQUARE_BRACKET, KEYWORD_REFERENCE
}

KEYWORDS = [
    b"trailer", b"xref", b"null", b"startxref", b"endstream", b"n", b'f' # the order is important here!
]

Lexeme = namedtuple("Lexeme", ["type", "value"])

is_digit = lambda x : x >= 48 and x < 58


# lets define lexeme types
LEXEME_STRING = object()
LEXEME_NAME = object()
LEXEME_NUMBER = object()
LEXEME_KEYWORD = object()
LEXEME_SINGLETON = object()
LEXEME_BOOLEAN = object()
LEXEME_DICT_OPEN = object()
LEXEME_DICT_CLOSE = object()
LEXEME_STREAM = object()
LEXEME_NULL = object()
LEXEME_OBJ_OPEN = object()
LEXEME_OBJ_CLOSE = object()



class Seekable:

    def __init__(self, obj):
        if not(isinstance(obj, bytes) or isinstance(obj, bytearray)):
            raise ValueError("'obj' must be 'bytes' or 'bytearray' type.")
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

    def __init__(self, source : 'Seekable'):
        self.__source = source
        cpos = source.tell()
        source.seek(0, 2)
        self.__length = source.tell()
        source.seek(cpos, 0)
        self.__current = self.__source.read(1)[0]
        self.__lexemesBuffer = list()
        self.__movesHistory = list()
        self.__ended = False
        self.__currentLexeme = None
    

    @property
    def current_lexeme(self):
        if self.__ended:
            raise StopIteration()
        return self.__currentLexeme
    

    def seekable_rfind(self, keyword : 'bytes'):
        revKeyword = bytes(reversed(keyword))
        buff = bytearray()
        count = 1
        while bytes(buff) != revKeyword:
            buff.clear()
            while count <= self.__length:
                self.__source.seek(self.__length - count, 0)
                c = self.__source.read(1)
                count += 1
                if c[0] not in [CARRIAGE_RETURN, LINE_FEED]:
                    buff.extend(c)
                else:
                    break
            if count > self.__length and c[0] not in [CARRIAGE_RETURN, LINE_FEED]:
                return -1
        pos = self.__source.tell()
        self.__advance()
        self.__next__()
        return pos

    
    def move_at_position(self, pos):
        previousLexeme = self.current_lexeme
        previousPosition = self.__source.tell()
        self.__movesHistory.append((previousLexeme, previousPosition))
        self.__source.seek(pos, 0)
        self.__advance()
        return self.__next__()


    def move_back(self):
        if len(self.__movesHistory) == 0:
            raise Exception("No move in history")
        prevLex, prevPos = self.__movesHistory.pop()
        self.__currentLexeme = prevLex
        self.__source.seek(prevPos - 1, 0)
        self.__advance()


    def __advance(self):
        if self.__ended:
            raise StopIteration()
        self.__current = self.__source.read(1)
        if self.__current == b'':
            self.__current = b' '[0]
            self.__ended = True
        else:
            self.__current = self.__current[0]
        

    def __read_chunk(self, size):
        if self.__ended:
            raise StopIteration()
        endPos = self.__source.tell() + size
        if endPos <= self.__length:
            data = self.__source.read(size)
            return data
        else:
            return None


    def __remove_blanks(self):
        while True:
            if self.__current in BLANKS:
                self.__advance()
            elif self.__current == PERCENTAGE: # comment starts
                while self.__current != LINE_FEED:
                    self.__advance()
                self.__advance()
            else:
                break


    def __peek(self, k = 1):
        k -= 1
        currentPos = self.__source.tell()
        if currentPos + k >= self.__length:
            return None
        else:
            self.__source.seek(k, 1)
            v = self.__source.read(1)
            self.__source.seek(currentPos, 0)
            return v[0]
    

    def __parse_string(self):
        if self.__current == OPEN_PARENTHESIS:
            openParentheses = 1
            buffer = bytearray()
            while openParentheses > 0:
                self.__advance()
                if self.__current == OPEN_PARENTHESIS:
                    openParentheses += 1
                elif self.__current == CLOSE_PARENTHESIS:
                    openParentheses -= 1
                buffer.append(self.__current)
            self.__advance()
            buffer.pop()
            # TODO: implement fully the specification
            return Lexeme(LEXEME_STRING, buffer.decode('utf-8'))
        else:
            buffer = bytearray()
            while self.__current != CLOSE_ANGLE_BRACKET:
                # TODO: check validity of value
                self.__advance()
                if self.__current in BLANKS: continue
                buffer.append(self.__current)
            buffer.pop()
            self.__advance()
            # TODO: convert hex to char
            return Lexeme(LEXEME_STRING, buffer.decode('utf-8'))


    def __parse_name(self):
        buffer = bytearray()
        self.__advance()
        while not(self.__current in BLANKS or self.__current in DELIMITERS):
            buffer.append(self.__current)
            self.__advance()
        
        if len(buffer) == 0:
            buffer.append(FORWARD_SLASH)
        return Lexeme(LEXEME_NAME, buffer.decode('ascii'))


    def __parse_number(self):
        buff = bytearray()
        if self.__current == PLUS or self.__current == MINUS:
            buff.append(self.__current)
            self.__advance()
        
        while is_digit(self.__current):
            buff.append(self.__current)
            self.__advance()
        
        if self.__current == POINT:
            buff.append(POINT)
            self.__advance()
        else:
            return Lexeme(LEXEME_NUMBER, int(buff.decode('ascii')))
        
        while is_digit(self.__current):
            buff.append(self.__current)
            self.__advance()

        return Lexeme(LEXEME_NUMBER, float(buff.decode('ascii')))

    
    def __parse_litteral(self, lit):
        for i, l in enumerate(lit):
            if self.__peek(i) != l: break
        if i == len(lit) - 1:
            # ok, we matched it
            for i in range(len(lit)):
                self.__advance()
            return True
        else:
            return False


    def __match_keyword(self):
        for k in KEYWORDS:
            if self.__parse_litteral(k):
                return Lexeme(LEXEME_KEYWORD, k)
        else:
            return False


    def put_back(self, current, lexeme):
        self.__lexemesBuffer.append(lexeme)
        self.__currentLexeme = current


    def __next__(self):

        if len(self.__lexemesBuffer) > 0:
            self.__currentLexeme = self.__lexemesBuffer.pop()
            return self.__currentLexeme

        self.__remove_blanks()
        # now try to parse lexical entities
        if self.__current == OPEN_PARENTHESIS or (
                self.__current == OPEN_ANGLE_BRACKET and self.__peek() != OPEN_ANGLE_BRACKET):
            self.__currentLexeme = self.__parse_string()
        elif self.__current == FORWARD_SLASH:
            self.__currentLexeme = self.__parse_name()
        elif is_digit(self.__current) or self.__current in [PLUS, MINUS, POINT]:
            self.__currentLexeme = self.__parse_number() 
        elif self.__parse_litteral(b"true"):
            self.__currentLexeme = Lexeme(LEXEME_BOOLEAN, True)
        elif self.__parse_litteral(b"false"):
            self.__currentLexeme = Lexeme(LEXEME_BOOLEAN, False)
        elif self.__current == OPEN_ANGLE_BRACKET and self.__peek() == OPEN_ANGLE_BRACKET:
            self.__advance()
            self.__advance()
            self.__currentLexeme = Lexeme(LEXEME_DICT_OPEN, b"<<")
        elif self.__current == CLOSE_ANGLE_BRACKET and self.__peek() == CLOSE_ANGLE_BRACKET:
            self.__advance()
            self.__advance()
            self.__currentLexeme = Lexeme(LEXEME_DICT_CLOSE, b">>")        
        elif self.__current in SINGLETONS:
            self.__currentLexeme = Lexeme(LEXEME_SINGLETON, bytearray((self.__current,)).decode('ascii'))
            self.__advance()
        elif self.__parse_litteral(b"stream"):
            # check whether there are the optional \r\n
            if self.__current == CARRIAGE_RETURN:
                self.__advance()
                if self.__current != LINE_FEED:
                     raise LexerError("Carriage return not followed by a line feed after 'stream' keyword.")
            
            streamPos = self.__source.tell()
            # build a closure to read the stream later
            def read_stream(length):
                oldPos = self.__source.tell()
                self.__source.seek(streamPos, 0)
                data = self.__source.read(length)
                self.__advance()
                # now need to match endstream, or line feed + endstream
                if self.__current == LINE_FEED:
                    self.__advance()
                self.__source.seek(oldPos, 0)
                return data
                
            self.__currentLexeme = Lexeme(LEXEME_STREAM, read_stream)
        
        elif self.__parse_litteral(b"obj"):
            self.__currentLexeme = Lexeme(LEXEME_OBJ_OPEN, b"obj")
        
        elif self.__parse_litteral(b"endobj"):
            self.__currentLexeme = Lexeme(LEXEME_OBJ_CLOSE, b"endobj")
        else:
            match = self.__match_keyword()
            if match == False:
                raise LexerError("Invalid characters sequence in input stream.")
            else:
                self.__currentLexeme = match
        return self.__currentLexeme