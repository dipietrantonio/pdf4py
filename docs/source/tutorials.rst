.. _tutorials:

Tutorials and examples
======================

In this page are collected a bunch of examples that will show you the correct
use of `pdf4py`.


PDF objects count
----------------------------

Suppose we want to know how many PDF (in use) objects are in a PDF file. Let's
use the following snippet to find it out.

::

    >>> import pdf4py.parser
    >>> fp = open('tests/pdfs/0000.pdf', 'rb')
    >>> parser = pdf4py.parser.Parser(fp)
    >>> all_xref_entries = list(parser.xreftable)
    >>> len(all_xref_entries)
    119
    >>> for x in all_xref_entries[:10]:
    ...     print(x)
    ... 
    XrefInUseEntry(offset=15, object_number=1, generation_number=0)
    XrefInUseEntry(offset=525989, object_number=2, generation_number=0)
    XrefInUseEntry(offset=63, object_number=3, generation_number=0)
    XrefInUseEntry(offset=60167, object_number=4, generation_number=0)
    XrefInUseEntry(offset=285, object_number=5, generation_number=0)
    XrefInUseEntry(offset=38737, object_number=6, generation_number=0)
    XrefInUseEntry(offset=36091, object_number=7, generation_number=0)
    XrefInUseEntry(offset=21676, object_number=8, generation_number=0)
    XrefInUseEntry(offset=4102, object_number=9, generation_number=0)
    XrefInUseEntry(offset=5162, object_number=10, generation_number=0)

The special method `__iter__` called on `xreftable` returns a generator
over the in-use and compressed objects references. To know how
many of them there are one must iterates over the generator until it is
exhausted. This is what `list` does: to collect all entries.


Navigate the document structure
-------------------------------

A PDF document is organized in a hierarchical structure made up of
basic constructs such as dictionaries and references. This snippet 
shows how one can navigate such a structure to access content that
defines a particular page.

::

    >>> from pdf4py.parser import Parser
    >>> fp = open('tests/pdfs/0000.pdf', 'rb')
    >>> parser = Parser(fp)
    >>> parser.trailer
    {'Size': 120, 'Root': PDFReference(object_number=119, generation_number=0), 'Info': PDFReference(object_number=114, generation_number=0), 'ID': [PDFHexString(value=b'C49DFA7375A44BAA174802F645A8A459'), PDFHexString(value=b'C49DFA7375A44BAA174802F645A8A459')]}
    >>> root_ref = parser.trailer['Root']
    >>> root_dict = parser.parse_reference(root_ref)
    >>> root_dict
    {'Type': 'Catalog', 'Pages': PDFReference(object_number=2, generation_number=0)}
    >>> pages = parser.parse_reference(root_dict['Pages'])
    >>> pages
    {'Type': 'Pages', 'Count': 10, 'Kids': [PDFReference(object_number=23, generation_number=0), PDFReference(object_number=31, generation_number=0), PDFReference(object_number=49, generation_number=0), PDFReference(object_number=58, generation_number=0), PDFReference(object_number=64, generation_number=0), PDFReference(object_number=71, generation_number=0), PDFReference(object_number=87, generation_number=0), PDFReference(object_number=94, generation_number=0), PDFReference(object_number=104, generation_number=0), PDFReference(object_number=110, generation_number=0)]}
    >>> page_1 = parser.parse_reference(pages['Kids'][0])
    >>> page_1
    {'Type': 'Page', 'Parent': PDFReference(object_number=2, generation_number=0), 'Contents': PDFReference(object_number=24, generation_number=0), 'Resources': PDFReference(object_number=27, generation_number=0), 'MediaBox': [0, 0, 595.276, 841.89]}
    >>> contents = parser.parse_reference(page_1['Contents'])
    >>> contents
    PDFStream(dictionary={'Length': PDFReference(object_number=25, generation_number=0), 'Filter': 'FlateDecode'}, stream=<function Parser._stream_reader.<locals>.complete_reader at 0x7f43b1c19d90>)
    >>> data = contents.stream()
    >>> data
    b'q\n/I0 Do\nQ\nq\n0.539 w\nBT\n/F0 11 Tf\n0 TL\n48 804.69 Td\n[(Proceedings 7th Modelica Conference, Como, Italy)65(, Sep. 20-22, 2009)]TJ\nET\nQ\nq\n0.539 w\nBT\n/F0 11 Tf\n0 TL\n48 35.8 Td\n[(\xa9 )18(The Modelica )55(Association, 2009)]TJ\nET\nQ\nq\n0.539 w\nBT\n/F0 11 Tf\n0 TL\n289.388 35.8 Td\n[(251)]TJ\nET\nQ\nq\n0.49 w\nBT\n/F0 10 Tf\n0 TL\n435.066 37 Td\n[(DOI: 10.3384/ecp09430032)]TJ\nET\nQ\n'


In the last part can be seen a sequence of instructions that the rendering program has to execute to depict the page. That sequence can be tokenized using `pdf4py.parser.SequentialParser`.

::

    >>> from pdf4py.parser import SequentialParser
    >>> seq = SequentialParser(data)
    >>> seq_iter = iter(seq)
    >>> next(seq_iter)
    PDFOperator(value='q')
    >>> next(seq_iter)
    'I0'
    >>> next(seq_iter)
    PDFOperator(value='Do')
    >>> next(seq_iter)
    PDFOperator(value='Q')
    >>> next(seq_iter)
    PDFOperator(value='q')
    >>> next(seq_iter)
    0.539

The user that wishes to interpret these commands to extract text, images, or other higher level information must use `pdf4py` to build a software module for that purpose.