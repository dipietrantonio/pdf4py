"""
Here are defined constants and functions to deal with the input byte stream
and to support the identification of meaningful class of characters in it.
"""
# Defines a constant for each relevant character
LINE_FEED = ord('\n')
HORIZONTAL_TAB = ord('\t')
FORM_FEED = ord('\f')
BACKSPACE = ord('\b')
CARRIAGE_RETURN = ord('\r')
OPEN_PARENTHESIS = ord('(')
CLOSE_PARENTHESIS = ord(')')
OPEN_ANGLE_BRACKET = ord('<')
CLOSE_ANGLE_BRACKET = ord('>')
OPEN_SQUARE_BRACKET = ord('[')
CLOSE_SQUARE_BRACKET = ord(']')
FORWARD_SLASH = ord('/')
BACK_SLASH = ord("\\")
OPEN_CURLY_BRACKET = ord('{')
CLOSE_CURLY_BRACKET = ord('}')
PERCENTAGE = ord('%')
POINT = ord('.')
PLUS = ord('+')
MINUS = ord('-')
KEYWORD_REFERENCE = ord('R')
FREE_ENTRY_KEYWORD = ord('f')
INUSE_ENTRY_KEYWORD = ord('n')
CHARACTER_X = ord('x')
NUMBER_SIGN = ord('#')


# singletons are lexemes composed by only one character.
SINGLETONS = {
    OPEN_CURLY_BRACKET, CLOSE_CURLY_BRACKET, OPEN_SQUARE_BRACKET, CLOSE_SQUARE_BRACKET
}

# used to determine if a character is a regular character
DELIMITERS = {OPEN_CURLY_BRACKET, CLOSE_CURLY_BRACKET, OPEN_SQUARE_BRACKET, CLOSE_SQUARE_BRACKET, 
    OPEN_PARENTHESIS, CLOSE_PARENTHESIS, FORWARD_SLASH, ord('<'), ord('>'), PERCENTAGE}

# the order is important here! For example, you don't want "n" to comes before "null", otherwise the
# latter will never be matched.
KEYWORDS = [
    b"endobj", b"obj", b"trailer",  b"xref", b"startxref", b"endstream"
]


is_digit = lambda x : x >= 48 and x < 58
is_hex_digit = lambda x: (x >= 48 and x < 58) or (x >= 65 and x < 71) or (x >= 97 and x < 103)


def hex_to_number(x):
    if x >= 48 and x < 58:
        return x - 48
    elif x >= 65 and x < 71:
        return x - 55
    elif x >= 97 and x < 103:
        return x - 87
    else:
        raise ValueError("'{}' is not a hexadecimal string.".format(chr(x)))


STRING_ESCAPE_SEQUENCES = {
    ord("n") : LINE_FEED,
    ord("r") : CARRIAGE_RETURN,
    ord("b") : BACKSPACE,
    ord("t") : HORIZONTAL_TAB,
    ord("f") : FORM_FEED
}


BLANKS = {0x00, 0x09, 0x0A, 0x0C, 0x0D, 0x20}
