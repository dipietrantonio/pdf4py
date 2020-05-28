from datetime import datetime, timezone, timedelta
from .exceptions import PDFGenericError
from .types import PDFReference, PDFHexString, PDFLiteralString
from numbers import Integral


_DATE_KEYS = ['year', 'month', 'day', 'hour', 'minute', 'second', 'tzinfo']



class AbstractTree:


    def __init__(self, parser : 'Parser', obj : 'dict or PDFReference'):
        self._parser = parser
        self._root = parser.parse_reference(obj) if isinstance(obj, PDFReference) else obj
    

    def __getitem__(self, key):
        """
        Retrieves the value associated with `key`.

        Parameters
        ----------
        key : PDFLiteralString, PDFHexString, Integral
            key to search for.
        
        Returns
        -------
        val : Any PDF object type
            The associated value.
        
        Raises
        ------
        ke : KeyError
            Exception thrown if `key` is not found.
        """
        if not isinstance(key, self._pdftype):
            raise ValueError("Key specified is not a string object.")
        current_node = self._root
        while self._label not in current_node:
            kids = current_node['Kids']
            if isinstance(kids, PDFReference):
                kids = self._parser.parse_reference(kids)
            current_node = None
            for ref in kids:
                kid = self._parser.parse_reference(ref)
                limits = []
                for x in kid['Limits']:
                    if isinstance(x, PDFReference):
                        x = self._parser.parse_reference(x)
                    limits.append(x)
                if key < limits[0]:
                    raise KeyError(key)
                if key <= limits[1]:
                    current_node = kid
                    break
            if current_node is None:
                raise KeyError(key)
        # TODO: binary search here
        nitems = len(current_node[self._label])
        for i in range(0, nitems, 2):
            k = current_node[self._label][i]
            if isinstance(k, PDFReference):
                k = self._parser.parse_reference(k)
            if k == key:
                return  current_node[self._label][i + 1]
        raise KeyError(key)

        
    def __contains__(self, item):
        """
        Checks if `item` is contained in the dictionary.

        Parameters
        ----------
        item : PDFLiteralString or PDFHexString
            The item to search for.
        """
        try:
            self.__getitem__(item)
            return True
        except KeyError:
            return False
    

    def get(self, key, default = None):
        """
        Returns the value associated with `key` if present, the default otherwise.

        Parameters
        ----------
        key : PDFLiteralString or PDFHexString
            The key to search for.
        
        Returns
        -------
        val : Any PDF object type
            The value associated to `key` or `default`.
        """
        try:
            return self.__getitem__(key)
        except KeyError:
            return default    



class NameTree(AbstractTree):
    """
    An ordered dict whose keys are strings.
    """
    _pdftype = (PDFHexString, PDFLiteralString)
    _label = 'Names'



class NumberTree(AbstractTree):
    """
    An ordered dict whose keys are strings.
    """
    _pdftype = Integral
    _label = 'Nums'


def parse_date(s : 'str'):
    """
    Parses a date encoded using the PDF standard into a `datetime` object.

    Parameters
    ----------
    s : str
        A string representing a date encoded using the rules of PDF standard.
    
    Returns
    -------
    d : datetime
        A datetime object representing the date encoded in s.
    """
    if not s.startswith('D:'):
        raise PDFGenericError("'parse_date' called on a string that does not represent a date.")
    components = []
    components.append(int(s[2:6]))
    
    i = 6
    while i < len(s) and s[i] not in ['Z', '-', '+']: 
        components.append(int(s[i:i+2]))
        i += 2

    for j in range(len(components), 6):
        components.append(1 if j < 3 else 0)
      
    if i < len(s):
        O = s[i]
        if O != 'Z':
            off_HH = int(s[i+1:i+3])
            if s[i+4:i+6] != '00':
                raise PDFGenericError('Unsupported date format (minutes UTC offset) in: ' + s)
            d = timedelta(hours=off_HH)
            components.append(timezone(-d if O == '-' else d))
    else:
        components.append(None)

    return datetime(**dict(zip(_DATE_KEYS, components)))