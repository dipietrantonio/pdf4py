from .parser import *
from ._lexer import Lexer



class Page:
    """
    A PDF Page.
    """
    def __init__(self, page_dict : 'dict'):
        # init page here
        pass



class PageTree:
    """
    TODO: update it
    Data structure providing a fast way to access page dictionaries within a PDF file.
    
    It implements a tree that has `Page` objects at its leaves whereas internal nodes 
    are `PageTree` instances. Pages can be accessed by index starting from 1.
    
    Parameters
    ----------
    parser : Parser
        The `Parser` instance used to retrieve objects in the document the page tree
        belongs to. It is needed to resolve PDF references.
    
    pages : dict
        A *page tree node* pdf object.
    """
    def __init__(self, parser : 'Parser', pages : 'dict'):
        self._parser = parser
        self._count = pages['Count']
        self._kids = pages['Kids']
    

    def __len__(self):
        return self._count


    def __getitem__(self, n):
        """
        Returns the page number `n`.
        """
        if n > self._count:
            raise KeyError("Page number '{}' is greater than the total number of pages ({})".format(n, self._count))
        inc_page_count = 0
        current_kids = self._kids
        while inc_page_count < n:    
            for i in range(len(current_kids)):
                kid = self._parser.parse_reference(current_kids[i])
                if kid['Type'] == 'Pages':
                    n_children = kid['Count']
                    if isinstance(n_children, PDFReference):
                        n_children = self._parser.parse_reference(n_children)
                    if inc_page_count + n_children >= n:
                        # The searched page is in this subtree
                        current_kids = kid['Kids']
                        if isinstance(current_kids, PDFReference):
                            current_kids = self._parser.parse_reference(current_kids)
                        break
                    else:
                        # not in this subtree but in one of the next ones.
                        inc_page_count += n_children
                elif kid['Type'] == 'Page':
                    inc_page_count += 1
                    if inc_page_count == n:
                        return Page(kid)    
                else:
                    raise PDFSyntaxError("Illegal dictionary type: must be 'Pages' or 'Page', but '{}' found.".format(kid['Type']))


    def __iter__(self):
        pass



class Document:
    """
    Implements an interface with a PDF's Document Structure.
    """
    def __init__(self, source):
        self._parser = Parser(source)
        self._read_catalog()
    

    def _read_catalog(self):
        catalogRef = self._parser.trailer['Root']
        self.catalog = self._parser.parse_reference(catalogRef)
        pages_root = self.catalog['Pages']
        if isinstance(pages_root, PDFReference):
            pages_root = self._parser.parse_reference(pages_root)
        self.__pages = PageTree(self._parser, pages_root)
    

    def __getitem__(self, n):
        return self.__pages[n]
    

    @property
    def pages(self):
        return self.__pages
        