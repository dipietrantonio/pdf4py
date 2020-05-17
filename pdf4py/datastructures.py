from datetime import datetime, timezone, timedelta
from .exceptions import PDFGenericError

_DATE_KEYS = ['year', 'month', 'day', 'hour', 'minute', 'second', 'tzinfo']



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