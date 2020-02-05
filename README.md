# pdf4py

A PDF parser written in Python 3 with no external dependencies.

## Introduction

The module `pdf4py` allows the user to interact with a PDF file at a low level and to build higher
level functionalities (e.g. text and/or image extraction). In particular, it defines the class
`Parser` that reads the Cross Reference Table of a PDF document and uses its entries to give the
user the ability to locate PDF objects within the file and parse them into suitable Python objects.

Extracting text from a PDF and other higher level analysis tasks are not natively supported because
of two reasons:

- their complexity is not trivial and would require a not indifferent amount of work which now I prefer
investing into developing a complete and reliable parser;
- they are conceptually different tasks from PDF parsing, since the PDF does not define the concept of
structured document from the content point of view.

Therefore, they require a separate implementation built on top of `pdf4py`.

## Why

One day at work I was asked to analyze some PDF files; to my surprise I have discovered that
there is not an established Python module to easily parse a PDF document. In order to understand
why I delved into the PDF 1.7 specification: from that moment on, I got more and more interested
in the inner workings of one of the most important and ubiquitous file format. And what's
a better way to understand the PDF than writing a parser for it?

## PDF standard coverage

You can check how many features of the standard are implemented and what is the progress on
supporting the missing ones by checking the standard coverage [page](StandardCoverage.md).

## Example usage

--

## Contributing

You can contribute by:

- filing a new issue;
- proposing changes and additions through a pull request.
