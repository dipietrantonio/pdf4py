import unittest
from context import *


# array of pdf sentences used to test the Lexer class
pdfParts = [
    b"% comment ( /% ) blah blah blah", # this is just a comment
    b"346% comment ( /% ) blah blah blah\n123", # corresponds to tokens "abc" and "123"
    b"                                       ~", # Invalid string
    b"true false", # booleans
    b"123 43445 +17 -98 0", # Integers
    b"34.5 -3.62 +123.6 4. -.002 0.0", # floats
    b"""
    ( This is a string )
    (Strings may contain newlines\n and such.)
    (Strings may contain balanced parentheses ( ) and\n special characters ( * ! & } ^ % and so on).)
    (The following is an empty string.)
    ()
    (It has zero (0) length.)
    """, # string examples 1
    b"(These \\ntwo strings \\nare the same.) (These \ntwo strings \nare the same.)", # strings with back slash
    rb"(\a backslash is ignored)",  
    rb"(This string contains \245two octal characters\307.)", # test octal strings
    rb"(\0053) (\053) (\53)", # test octal strings 2
    
]



class LexerUnitTest(unittest.TestCase):
    """
    Tests the Lexer class.
    """

    def test_lexer_creation(self):
        with open("tests/pdfs/0000.pdf", "rb") as fp:
            lex = lexpkg.Lexer(fp)
            self.assertIs(lex.current_lexeme, None)



    def test_read_only_comment_source(self):
        lex = lexpkg.Lexer(pdfParts[0])
        try:
            a = next(lex)
        except StopIteration:
            """
            Ok, comments are properly skipped and EOF is reached.
            """
    

    def test_tokens_mixed_with_comment(self):
        lex = lexpkg.Lexer(pdfParts[1])
        a = next(lex)
        self.assertEqual(a, 346)
        b = next(lex)
        self.assertEqual(b, 123)
    
    
    def test_invalid_input_and_context_print(self):
        lex = lexpkg.Lexer(pdfParts[2], 31)
        try:
            a = next(lex)
        except lexpkg.PDFLexicalError as e:
            msg = str(e)
            self.assertIn("40", msg)
    

    def test_boolean_parsing(self):
        lex = lexpkg.Lexer(pdfParts[3], 31)
        t, f = next(lex), next(lex)
        self.assertEqual(t, True)
        self.assertEqual(f, False)


    def test_integer_parsing(self):
        lex = lexpkg.Lexer(pdfParts[4])
        self.assertEqual([123, 43445, +17, -98, 0], list(lex))


    def test_real_parsing(self):
        lex = lexpkg.Lexer(pdfParts[5])
        self.assertEqual([34.5, -3.62, +123.6, 4., -.002, 0.0], list(lex))


    def test_parse_string_literal(self):
        lex = lexpkg.Lexer(pdfParts[6])
        strings = [" This is a string ",
            "Strings may contain newlines\n and such.",
            "Strings may contain balanced parentheses ( ) and\n special characters ( * ! & } ^ % and so on).",
            "The following is an empty string.",
            "",
            "It has zero (0) length."]
        self.assertEqual(strings, list(lex))
        # Test backslashes
        lex = lexpkg.Lexer(pdfParts[7])
        a, b = next(lex), next(lex)
        self.assertEqual(a, b)
        lex = lexpkg.Lexer(pdfParts[8])
        self.assertEqual("a backslash is ignored", next(lex))
        # Test octal characters
        lex = lexpkg.Lexer(pdfParts[9])
        self.assertEqual('This string contains ¥two octal charactersÇ.', next(lex))
        lex = lexpkg.Lexer(pdfParts[10])
        self.assertEqual('\0053', next(lex))
        self.assertEqual(next(lex), next(lex))
        
        
        
if __name__ == "__main__":
    unittest.main()

