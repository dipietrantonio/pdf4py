import sys
sys.path.append(".")
from pdfpy.parser import PDFParser, Seekable
import logging


if __name__ == "__main__":
    
    if len(sys.argv) < 2:
        print("Usage: {} <pdf>".format(sys.argv[0]))
    
    #logging.basicConfig(level=logging.DEBUG)
    P = PDFParser(sys.argv[1])
    for i, x in enumerate(P.xrefTable.active_keys()):
        #print("Key: ", x)
        print(i+1, "/", len(P.xrefTable.active_keys()), end="             \r")
        a = P.parse_xref_entry(P.xrefTable[x])


 