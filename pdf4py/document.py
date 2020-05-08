from .parser import *
from ._lexer import Lexer
from .exceptions import PDFGenericError, PDFSyntaxError


class Page:
    """
    A PDF Page.
    """
    def __init__(self, page_dict : 'dict'):
        diff = {'Resources', 'MediaBox'}.difference(set(page_dict))
        if len(diff) > 0:
            raise PDFSyntaxError("The requested page does not contain '{}' keyword(s)".format(', '.join(diff)))
        self._mediabox = page_dict['MediaBox']
        self._resources = page_dict['Resources']
        self._rotate = page_dict.get('Rotate')
        self._cropbox = page_dict.get('CropBox')
        self._bleedbox = page_dict.get('BleedBox')
        self._trimbox = page_dict.get('TrimBox')
        self._contents = page_dict.get('Contents')
        self._pieceinfo = page_dict.get('PieceInfo')
        self._last_modified = page_dict.get('LastModified')
        if self._last_modified is None and self._pieceinfo is not None:
            raise PDFSyntaxError("Attribute 'LastModified' is missing for the selected Page, but 'PieceInfo' is present.")

    @property
    def pieceinfo(self):
        return self._pieceinfo

    @property
    def last_modified(self):
        return self._last_modified

    @property
    def contents(self):
        return self._contents

    @property
    def trimbox(self):
        return self._trimbox

    @property
    def bleedbox(self):
        return self._bleedbox
    
    @property
    def cropbox(self):
        return self._cropbox
    
    @property
    def rotate(self):
        return self._rotate

    @property
    def mediabox(self):
        return self._mediabox

    @property
    def resources(self):
        return self._resources



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
    inheritable_fields = {'Resources', 'MediaBox', 'CropBox', 'Rotate'}

    def __init__(self, parser : 'Parser', pages : 'dict'):
        self._parser = parser
        self._count = pages['Count']
        self._kids = pages['Kids']
        self._pages = pages
    

    def __len__(self):
        return self._count


    def __getitem__(self, n):
        """
        Returns the page number `n`. The page number starts from 1.
        """
        if n == 0:
            raise KeyError("Pages are indexed starting from 1.")
        if n > self._count:
            raise KeyError("Page number '{}' is greater than the total number of pages ({}).".format(n, self._count))
        inc_page_count = 0
        current_kids = self._kids
        to_pass_on = {x : self._pages[x] for x in self._pages if x in self.inheritable_fields}
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
                        to_pass_on.update({x : kid[x] for x in kid if x in self.inheritable_fields})
                        if isinstance(current_kids, PDFReference):
                            current_kids = self._parser.parse_reference(current_kids)
                        break
                    else:
                        # not in this subtree but in one of the next ones.
                        inc_page_count += n_children
                elif kid['Type'] == 'Page':
                    inc_page_count += 1
                    if inc_page_count == n:
                        to_pass_on.update({x : kid[x] for x in kid if x in self.inheritable_fields})
                        kid.update(to_pass_on)
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
    

    def __len__(self):
        return len(self.pages)


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
        