"""
Defines custom Python classes used transversely within the library.

Amongst these definition are found Python representations for PDF Objects
(section 7.3 of the Standard), Lexer's output tokens, and XRefTable entry types. 
"""
from collections import namedtuple



PDFHexString = namedtuple("PDFHexString", ["value"])
"""
Represents the PDF Object 'Hexadecimal string'.

An hexadecimal string is used mainly to encode a small quantity of binary data.
The sequence of hexadecimal digits are not decoded from ascii but stored directly
as bytes in `value` attribute. This is so because you tipically want to pass that
value to the `binascii.unhexlify` function.
"""


PDFLiteralString = namedtuple("PDFLiteralString", ["value"])
"""
Represents the PDF Object 'Literal string'.

A literal string is a sequence of ASCII characters. This is in theory,
in practice there are so many PDF writers that store non ASCII strings using
this object type that is best to leave the associated value in bytes and
pass to the user the duty of choosing the right decoding scheme.
"""


PDFOperator = namedtuple("PDFOperator", ["value"])
"""
Represents an operator appearing in a ContentStream.
"""


PDFStream = namedtuple("PDFStream", ["dictionary", "stream"])
"""
Represents a PDF stream.

The attribute `dictionary` points to the stream dictionary. The attribute `stream`
is a callable object requiring no arguments that when called returns the stream 
content bytes. The content is read from the source only when `stream` is called,
following the lazy loading philosophy around which pdf4py is built around.
"""


PDFReference = namedtuple("PDFReference", ["object_number", "generation_number"])
"""
Represent a PDF reference to a PDF Indirect object.
"""


PDFIndirectObject = namedtuple("PDFIndirectObject", ["object_number", "generation_number", "value"])
"""
Represents a PDF indirect object.

Attribute `value` contains the PDF object the indirect object structure wraps.
"""


XrefInUseEntry = namedtuple("XrefInUseEntry", ["offset", "object_number", "generation_number"])
"""
Represents an entry in the Cross Reference Table pointing to an object that
currently contributes to the final PDF render (as opposite to removed, i.e.
*free*, objects).
"""


XrefCompressedEntry = namedtuple("XrefCompressedEntry", ["object_number", "objstm_number", "index"])
"""
Represents an entry in the Cross Reference Table pointing to an object that 
currently contributes to the final PDF render, but stored in a compressed 
object stream to reduce the size of the PDF file.
"""


PDFKeyword = namedtuple("PDFKeyword", ["value"])
"""
[Internal] Represents a keyword in the PDF grammar, for example ``xref``.
"""


PDFSingleton = namedtuple("PDFSingleton", ["value"])
"""
[Internal] Represents a singleton in the PDF greammar, for example ``{``.
"""


PDFStreamReader = namedtuple("PDFStreamReader", ["value"])
"""
[Internal] A wrapper around a function ``f(length)`` returned by `Lexer` to `Parser` when parsing 
a PDF stream object.``
"""


PDFDictDelimiter = namedtuple("PDFDictDelimiter", ["value"])
"""
[Internal] Represents tokens ``<<`` and ``>>``.
"""