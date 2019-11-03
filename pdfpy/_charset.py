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
BACK_SLASH = 92
OPEN_CURLY_BRACKET = 123
CLOSE_CURLY_BRAKET = 125
PERCENTAGE = 37
POINT = 46
PLUS = 43
MINUS = 45
KEYWORD_REFERENCE = 82
CHARACTER_X = 120


DELIMITERS = {
    OPEN_PARENTHESIS, CLOSE_PARENTHESIS, OPEN_ANGLE_BRACKET, CLOSE_ANGLE_BRACKET,
    OPEN_SQUARE_BRACKET, CLOSE_SQUARE_BRACKET, FORWARD_SLASH, PERCENTAGE,
    OPEN_CURLY_BRACKET, CLOSE_CURLY_BRAKET
}


SINGLETONS = {
    OPEN_CURLY_BRACKET, CLOSE_CURLY_BRAKET, OPEN_SQUARE_BRACKET, CLOSE_SQUARE_BRACKET, KEYWORD_REFERENCE
}


KEYWORDS = [
    b"trailer", b"xref", b"null", b"startxref", b"endstream", b"n", b"f" # the order is important here!
]


is_digit = lambda x : x >= 48 and x < 58
is_hex_digit = lambda x: (x >= 48 and x < 58) or (x >= 65 and x < 71) or (x >= 97 and x < 103)

STRING_ESCAPE_SEQUENCES = {"n" : "\n", "r" : "\r", "b" : "\b", "t" : "\t", "f" : "\f"}
