class PDFLexicalError(Exception):
    """
    Raised when a lexical error is encountered during input scanning.
    """


class PDFSyntaxError(Exception):
    """
    Raised when the parsed PDF does not conform to syntax rules.
    """


class PDFUnsupportedError(Exception):
    """
    Raised when the parser does not support a PDF feature.
    """

class PDFWrongPasswordError(Exception):
    """
    Raised when the user gives in input a wrong password.
    """


class PDFGenericError(Exception):
    """
    Raised when a generic error happens.
    """
