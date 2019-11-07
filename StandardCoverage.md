# PDF 1.7 Standard Coverage

In this file the progress in implementing all the features in the [PDF 1.7 standard](http://wwwimages.adobe.com/www.adobe.com/content/dam/acom/en/devnet/pdf/pdfs/PDF32000_2008.pdf) is tracked.
As the development goes on, the various sections decribing features that have been supported
will be marked with an check (✓) in the following table.

## Chapters 1 - 6

Nothing to implement here, just introductory stuff.

## Chapter 7 - Syntax

| Section           | Description         | Status           |
| ----------------- | -----------         | ---------------- |
| 7.2               | Lexical conventions | ✓                |
| 7.3               | Objects             | Work in progress |
| 7.3.2             | Boolean objects     | ✓                |
| 7.3.3             | Numeric objects     | ✓                |
| 7.3.4             | String objects      | ✓                |
| 7.3.5             | Name objects        | ✓                |
| 7.3.6             | Array objects       | Refactoring      |
| 7.3.7             | Dictionary objects  | Refactoring      |
| 7.3.8             | Stream objects      | Refactoring      |
| 7.3.9             | Null object         | ✓                |
| 7.3.10            | Indirect objects    | Refactoring      |
| 7.4               | Filters             | Minimal support  |
| 7.4.2             | ASCIIHexDecode      | ✗                |
| 7.4.3             | ASCII85Decode       | ✗                |
| 7.4.4             | LZWDecode           | ✗                |
| 7.4.4             | FlateDecode         | ✓                |
| 7.4.5             | RunLengthDecode     | ✗                |
| 7.4.6             | CCITTFaxDecode      | ✗                |
| 7.4.7             | JBIG2Decode         | ✗                |
| 7.4.8             | DCTDecode           | ✗                |
| 7.4.9             | JPXDecode           | ✗                |
| 7.4.10            | Crypt               | ✗                |
| ....                                                       |


## Chapter 8 - Graphics

Not supported

## Chapter 9 - Text

Not supported

## Chapter 10 - Rendering

Not supported

## Chapter 11 - Transparency

Not supported


## Chapter 12 - Interactive features

Not supported

## Chapter 13 - Multimedia features

Not supported