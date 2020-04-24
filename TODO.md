# TODO list


A list of things to do to make pdf4py better. A priority is associated to each point
and can assume the value `LOW`, `MEDIUM` or `HIGH`. 

- [MEDIUM] (IN PROGRESS) Code and documentation cleanup.
- [MEDIUM] (IN PROGRESS) To collect more PDFs for testing purposes.
- [MEDIUM] (TO DO) To support *File specifications* (Section 7.11 of the Standard). 
- [LOW] (TO DO) To implement LZW decoding scheme (but it is not really necessary since it is deprecated).
- [LOW] (TO DO) To implement Public Key security handlers.
- [HIGH] (IN PROGRESS) To implement the module `pdf4py.document` that defines the
  class `Document`, a high level abstraction of the PDF file that understands and
  provides an interface to the document structure (sections 7.7 to 7.10: pages, 
  content streams, etc ..). Currently I am experimenting as I study those sections in depth.
- [HIGH] (TO DO) To implement tests for some predictors used in FlateDecode filter.
- [MEDIUM] (TO DO) To analyze performances and to compare them with other libraries.
- [LOW] (TO DO) To go through the 2.0 standard and see if there are major changes.
- [MEDIUM] (TO DO) Better handling of Compressed Object Streams.