# pdf4py

[![Build Status](https://travis-ci.org/Halolegend94/pdf4py.svg?branch=master)](https://travis-ci.org/Halolegend94/pdf4py) [![Documentation Status](https://readthedocs.org/projects/pdf4py/badge/?version=latest)](https://pdf4py.readthedocs.io/en/latest/?badge=latest) [![PyPI version](https://badge.fury.io/py/pdf4py.svg)](https://badge.fury.io/py/pdf4py) ![PyPI - Downloads](https://img.shields.io/pypi/dm/pdf4py?color=brightgreen)

A PDF parser written in Python 3 with no external dependencies.

The package `pdf4py` allows the user to analyze a PDF file at a very low level and in a very
flexible way by giving access to its atomic components, the PDF objects. All through a very
simple API that can be used to build higher level functionalities (e.g. text and/or image
extraction). In particular, it defines the class `Parser` that reads the *Cross Reference Table*
of a PDF document and uses its entries to give the user the ability to locate PDF objects within
the file and parse them into suitable Python objects.

**DISCLAIMER**: this package hasn't reached a stable version (>= 1.0.0) yet. Although the parser
API is quite simple it may change suddenly from one release to the next one. All breaking changes
will be properly notified in the release notes.


## Quick example

Here is a quick demonstration on how to use pdf4py. You can find more at the [tutorials page](https://pdf4py.readthedocs.io/en/latest/tutorials.html).

```python
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
```

## Installation and updates

You can install `pdf4py` using pip:

```
python3 -m pip install pdf4py
```

or download one of the releases and use the `setup.py` script.

The `master` branch is used for development and it is not advised to use it in production.

For this package the semantic versioning (specification 2.0.0) is adopted.

## Extracting text or images

Extracting text from a PDF and other higher level analysis tasks are not natively supported as of now 
because of two reasons:

- their complexity is not trivial and would require a not indifferent amount of work which now I prefer
investing into developing a complete and reliable parser;
- they are conceptually different tasks from PDF parsing, since the PDF does not define the concept of
document as a sequence of paragraphs, images, and other objects that can be normally considered *content*.

Therefore, they require a separate implementation built on top of `pdf4py`. In don't exclude that in
future these functionalities will be made available as modules in this package, but I am not planning
to do it anytime soon.


## Why this package

One day at work I was asked to analyze some PDF files. To my surprise I had discovered that
there was not an established Python module to easily parse a PDF document. In order to understand
why I delved into the PDF 1.7 specification: since that moment I've got interested more and more
in the inner workings of one of the most important and ubiquitous file format. And what's
a better way to understand the PDF than writing a parser for it?


## Documentation

You can read the documentation on [readthedocs.io](https://pdf4py.readthedocs.io/en/latest/).


## Contributing

Contributions are more than welcome! Please, when writing code or documentation for this package remind:

- to use the [numpy docstring conventions](https://numpydoc.readthedocs.io/en/latest/format.html) for documenting code.
- to follow the [Python guideline (PEP 8)](https://www.python.org/dev/peps/pep-0008/) when writing code.
- `pdf4py` is designed to be readable and easy to work with. I prefer readability over (not so significant)
  performance improvements.
- `pdf4py` is designed to be modular, flexible but also easy to use. It shouldn't be complicated for the user
  to perform one particular task.
- to adopt as much as possible a test-driven development process. Each contribution must be accompanied by a 
  test addition/modification.

If you are wondering in which way you can help, check the [TODO list](https://github.com/Halolegend94/pdf4py/blob/master/TODO.md). For now it will do as a simple "road map".  

If you have found a bug, please file a new issue here on GitHub. Proposing fixes, changes and additions can
be done through a pull request.
