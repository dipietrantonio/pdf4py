.. toctree::
    :maxdepth: 3
    :hidden:

    tutorials
    modules/index
    standard_coverage

pdf4py's documentation
==================================

The package `pdf4py` allows the user to analyze a PDF file at a very low level and in a very
flexible way by giving access to its atomic components, the PDF objects. All through a very
simple API that can be used to build higher level functionalities (e.g. text and/or image
extraction). In particular, it defines the class `Parser` that reads the *Cross Reference Table*
of a PDF document and uses its entries to give the user the ability to locate PDF objects within
the file and parse them into suitable Python objects.

.. image:: https://travis-ci.org/Halolegend94/pdf4py.svg?branch=master
    :target: https://travis-ci.org/Halolegend94/pdf4py
    :alt: Build Status
.. image:: https://readthedocs.org/projects/pdf4py/badge/?version=latest
    :target: https://pdf4py.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status
.. image:: https://badge.fury.io/py/pdf4py.svg
    :target: https://pypi.org/project/pdf4py/
.. image:: https://img.shields.io/pypi/dm/pdf4py?color=brightgreen
    :target: https://pypi.org/project/pdf4py/

**DISCLAIMER**: this package hasn't reached a stable version (>= 1.0.0) yet. Although the parser
API is quite simple it may change suddenly from one release to the next one. All breaking changes
will be properly notified in the release notes.


Quick example
-------------

Here is a quick demonstration on how to use pdf4py. For more examples, look at the :ref:`tutorials` page.

::

    >>> from pdf4py.parser import Parser
    >>> fp = open('tests/pdfs/0000.pdf', 'rb')
    >>> parser = Parser(fp)
    >>> info_ref = parser.trailer['Info']
    >>> print(info_ref)
    PDFReference(object_number=114, generation_number=0)
    >>> info = parser.parse_reference(info_ref)
    >>> print(info)
    {'Creator': PDFLiteralString(value=b'PaperCept Conference Management System'),
        ... , 'Producer': PDFLiteralString(value=b'PDFlib+PDI 7.0.3 (Perl 5.8.0/Linux)')}
    >>> creator = info['Creator'].value.decode('utf8')
    >>> print(creator)
    PaperCept Conference Management System


Extracting text or images
-------------------------
Extracting text from a PDF and other higher level analysis tasks are not natively supported as of now 
because of two reasons:

- their complexity is not trivial and would require a not indifferent amount of work which now I prefer
  investing into developing a complete and reliable parser;
- they are conceptually different tasks from PDF parsing, since the PDF does not define the concept of
  document as a sequence of paragraphs, images, and other objects that can be normally considered *content*.

Therefore, they require a separate implementation built on top of `pdf4py`. In don't exclude that in
future these functionalities will be made available as modules in this package, but I am not planning
to do it anytime soon.


Installation
------------
You can install `pdf4py` using pip:

::

    python3 -m pip install pdf4py


or download the latest release from GitHub and use the `setup.py` script.


Release Notes
-------------
You can find the list of all releases with associated notes `on GitHub <https://github.com/Halolegend94/pdf4py/releases>`_.


Why this package
----------------
One day at work I was asked to analyze some PDF files. To my surprise I had discovered that
there was not an established Python module to easily parse a PDF document. In order to understand
why I delved into the PDF 1.7 specification: since that moment I've got interested more and more
in the inner workings of one of the most important and ubiquitous file format. And what's
a better way to understand the PDF than writing a parser for it?
