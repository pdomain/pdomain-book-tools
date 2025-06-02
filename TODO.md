TODO:

"Add Word to Line" Button (see page 37 of Chile Nitrate Fields, the * isn't being captured by detection)

- Break "Sidenotes" off as their own paragraph.
    add logic to put these somewhere in the OCR (top for left sidenotes, bottom for right sidenotes)

Add ability to label a word as in Italics, Bold, Blackletter

"All Lines" is refreshing itself after Go To Page # a second time

Add Logic for General Lists/Tables, Tables of Contents, Plate lists, figure lists, etc:
 - scan line for ". . . ." and in post-processing expand line horizontally to connect
 - find if multiple items on right are very short compared to other lines they're probably page numbers

Single-line overflow words are not getting auto-matched
Line editor

- Text 'page group' Classifiers:
    - page number
    - running header
    - body text
    - footnote
    - printer marks (usually on bottom of page)

- Rebase and remove models from train_pgdp_ocr. Add a tool to download and cache models locally instead.
