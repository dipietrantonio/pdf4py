# PDF 1.7 Standard Coverage

In this file the progress in implementing all the features in the [PDF 1.7 standard](http://wwwimages.adobe.com/www.adobe.com/content/dam/acom/en/devnet/pdf/pdfs/PDF32000_2008.pdf) is tracked.
As the development goes on, the various sections decribing features that have been supported will be marked with an check (✓) in the following table.
The tilde mark (~) means almost every aspect is supported.

## Chapters 1 - 6

Nothing to implement here, just introductory stuff.

## Chapter 7 - Syntax

| Section           | Description                     | Status                                 |
| ----------------- | ------------------------------- | -------------------------------------- |
| 7.2               | Lexical conventions             | ✓                                      |
| 7.3               | Objects                         | ~                                      |
| 7.3.2             | Boolean objects                 | ✓                                      |
| 7.3.3             | Numeric objects                 | ✓                                      |
| 7.3.4             | String objects                  | ✓                                      |
| 7.3.5             | Name objects                    | ✓                                      |
| 7.3.6             | Array objects                   | ✓                                      |
| 7.3.7             | Dictionary objects              | ✓                                      |
| 7.3.8             | Stream objects                  | ~ (F parameter not supported yet)      |
| 7.3.9             | Null object                     | ✓                                      |
| 7.3.10            | Indirect objects                | ✓                                      |
| 7.4               | Filters                         | Minimal support                        |
| 7.4.2             | ASCIIHexDecode                  | ~ (Testing is missing still)           |
| 7.4.3             | ASCII85Decode                   | ✗                                      |
| 7.4.4             | LZWDecode                       | ✗                                      |
| 7.4.4             | FlateDecode                     | ~ (Predictors must still be tested)    |
| 7.4.5             | RunLengthDecode                 | ✗                                      |
| 7.4.6             | CCITTFaxDecode                  | ~ (data returned 'as is')              |
| 7.4.7             | JBIG2Decode                     | ~ (data returned 'as is')              |
| 7.4.8             | DCTDecode                       | ~ (data returned 'as is')              |
| 7.4.9             | JPXDecode                       | ~ (data returned 'as is')              |
| 7.4.10            | Crypt                           | ✓                                      |
| 7.5               | File Structure                  | ~                                      |
| 7.5.2             | File header                     | ✓                                      |
| 7.5.4             | Cross Reference Table           | ✓                                      |
| 7.5.5             | File trailer                    | ✓                                      |
| 7.5.6             | Incremental updates             | ✓                                      |
| 7.5.7             | Object streams                  | ~                                      |
| 7.5.8             | Cross Reference Streams         | ✓                                      |
| 7.6               | Encription                      | ~ (no embedded files for now)          |
| 7.6.1             | General                         | ✓                                      |
| 7.6.2             | General Encription Algorithm    | ✓                                      |
| 7.6.3             | Standard Security Handler       | ~ (permission bits ignored)            |
| 7.6.4             | Public Key Security Handler     | ✗                                      |
| 7.6.5             | Crypt Filters                   | ✓                                      |


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