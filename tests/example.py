import sys
sys.path.append(".")
from pdfpy.parser import PDFParser, Seekable

if __name__ == "__main__":
    
    if len(sys.argv) < 2:
        print("Usage: {} <pdf>".format(sys.argv[0]))
    
    P = PDFParser(sys.argv[1])
    print(vars(P))
    for i, x in enumerate(P.xrefTable.active_keys()):
        print(i+1, "/", len(P.xrefTable.active_keys()))
        print(P.parse_xref_entry(P.xrefTable[x]))
        print("----------------------")


 