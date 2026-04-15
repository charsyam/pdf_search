# PDF Search UI Requirements

## 1. Objective

Build a desktop application in Python that supports fast full-text search across PDF documents and provides a two-pane viewer for search results and page previews.

The product goal is to let a user choose a PDF, enter a keyword, and immediately find matching locations inside that document, including surrounding text context and visual page previews.

## 2. Target Users

- Users who need to search technical documents, reports, manuals, or books in PDF format
- Users who need both text context and visual page confirmation
- Users who may work with PDFs larger than 100 to 200 pages

## 3. Scope

### In Scope

- Desktop UI implemented in Python
- Windows support as a required target
- PDF text extraction and search indexing
- 2-gram based search index
- Search that ignores whitespace inside indexed text and query text
- Fast result lookup for large PDFs
- Result list with location, text context, and low-resolution page preview
- Clickable result that opens a high-resolution page image in a detail pane

### Out of Scope for First Version

- OCR for scanned image-only PDFs
- Multi-user or server-based search
- Cloud sync
- Annotation, editing, highlighting persistence, or collaboration features
- Advanced ranking such as semantic search or vector search

## 4. Platform Requirements

### Required

- Python-based implementation
- Windows support

### Recommended

- macOS support during development
- Packaging as a standalone desktop app for Windows

### Suggested UI Technology

The preferred direction is `PySide6` or `PyQt6` because:

- Native desktop UI is easier to deliver than a browser-wrapped approach
- Windows support is mature
- Split-pane layout, image rendering, threading, and model-view UI are well supported
- High-DPI image handling is practical

## 5. Core User Flow

1. User opens one or more PDF documents.
2. The application extracts PDF text and builds a searchable index.
3. User selects one PDF as the active search target.
4. User enters a search keyword and presses Enter.
5. The search executes without requiring whitespace to match exactly.
6. The left pane shows:
   - document name
   - page number
   - matched position or snippet location
   - previous and next sentence or surrounding context
   - low-resolution image preview of the page
7. User clicks a search result.
8. The right pane shows a high-resolution image of the corresponding page.
9. The selected result remains linked to the page image and page location.

## 6. Functional Requirements

### FR-1. PDF Loading

- The application shall allow the user to open PDF files from local storage.
- The application shall allow the user to choose which loaded PDF to search.
- The application shall parse page-level text from each PDF.
- The application shall maintain page identity, page number, and source file path for every extracted page.

### FR-2. Text Normalization

- All searchable text shall be normalized before indexing.
- Normalization shall remove whitespace characters for search purposes.
- The original extracted text shall still be preserved for display.
- Normalization should include at minimum:
  - removal of spaces, tabs, and line breaks
  - consistent Unicode normalization policy
  - optional lowercasing if case-insensitive search is adopted

### FR-3. 2-Gram Indexing

- All searchable text shall be indexed using 2-gram tokenization.
- The 2-gram index shall be generated from normalized text with whitespace removed.
- Queries shall be normalized using the same rule set as document text.
- The system shall support substring-like matching using the 2-gram index.

Example:

- Original text: `deep learning model`
- Normalized text: `deeplearningmodel`
- 2-grams: `de`, `ee`, `ep`, `pl`, `le`, ...

### FR-4. Search Behavior

- The application shall allow the user to input a keyword or phrase.
- The application shall execute search when the user presses Enter.
- The application shall search only within the currently selected PDF.
- Search shall not require spaces in the query to match spaces in the source text.
- Search ranking shall consider token order from the user's input.
- Search shall return all candidate matches with enough metadata to identify the document and page.
- Search results shall be ranked in a predictable order.

Recommended initial sort order:

- exact normalized substring match first
- then matches that preserve the query token order
- then by number of matching 2-grams
- then by document order and page number

Example ranking for query `해외 동포`:

- `해외동포`
- `해외-동포`
- `해외 동포`
- results where `동포` appears before `해외`

### FR-5. Search Results Pane

The left pane shall display each result with:

- document name
- page number
- matched text location identifier if available
- surrounding context before and after the match
- low-resolution page image preview

Context display requirements:

- show the matched sentence when sentence boundaries are detectable
- also show nearby leading and trailing text when sentence boundaries are ambiguous
- visually mark the matched term if practical

### FR-6. Detail Viewer Pane

The right pane shall display:

- a high-resolution rendered image of the selected page
- the corresponding page from the clicked result

Recommended enhancements for initial design:

- fit-to-width and zoom controls
- optional highlight box over the matched region when positional extraction is available

### FR-7. Page Image Generation

- The system shall generate low-resolution page previews for the result list.
- The system shall generate higher-resolution images for the detail pane.
- Page rendering should be cached to avoid repeated rendering cost.

### FR-8. Performance

- Search on already indexed PDFs shall feel immediate to the user.
- PDFs with more than 100 to 200 pages shall still support practical real-time search.
- Index creation may take time, but progress should be visible if indexing is not instantaneous.

Initial performance targets:

- query response on indexed content: under 300 ms for typical searches
- first visible results: under 500 ms after query submission
- left-pane preview generation: lazy-loaded or cached
- right-pane high-resolution image display after click: under 1 second for cached or recently viewed pages

### FR-9. Background Processing

- Indexing and page rendering shall not block the UI thread.
- The application shall use background workers or threads for:
  - PDF parsing
  - index building
  - low-resolution preview generation
  - high-resolution page rendering

### FR-10. Index Persistence

Recommended for first implementation:

- Store generated index data on local disk
- Reopen previously indexed PDFs without rebuilding everything unless the source file changed
- Support multiple indexed PDFs in the application, but search one selected PDF at a time

Minimum metadata:

- source file path
- source file modification timestamp
- page count
- normalized page text
- 2-gram postings or equivalent search structure

## 7. Non-Functional Requirements

### NFR-1. Responsiveness

- The UI shall remain responsive during indexing and search.
- Long-running work shall show status and progress.

### NFR-2. Accuracy

- Search results shall be traceable back to exact document and page.
- Text normalization must be deterministic so indexing and querying produce consistent results.

### NFR-3. Maintainability

- The architecture should separate UI, PDF parsing, indexing, and rendering modules.
- Core search logic should be testable without the UI.

### NFR-4. Portability

- The codebase shall run on Windows.
- OS-specific behavior should be isolated.

### NFR-5. Resource Usage

- Memory use should remain controlled for large documents.
- Page images should be generated on demand and cached with an eviction strategy.

## 8. Suggested Architecture

### UI Layer

- Python desktop UI using `PySide6`
- Split layout:
  - left pane: search box + result list
  - right pane: page image viewer

### PDF Processing Layer

Suggested libraries:

- `PyMuPDF` (`fitz`) for:
  - text extraction
  - page rasterization to low/high resolution images
  - possible coordinate extraction for future highlighting

Reason:

- It is practical for both text extraction and image rendering in one library.

### Search Engine Layer

Suggested internal components:

- text normalizer
- 2-gram tokenizer
- inverted index
- candidate scorer
- context extractor

Recommended indexing unit:

- page-level index with offsets into normalized text

Reason:

- It balances lookup speed, memory cost, and page-based UI requirements.

### Storage Layer

Suggested options:

- SQLite for metadata and persistence
- local binary or JSON cache for rendering metadata

Alternative:

- keep first version in memory only, but this weakens restart performance

## 9. Data Model Draft

### Document

- document_id
- file_path
- file_name
- file_modified_at
- page_count

### Page

- page_id
- document_id
- page_number
- original_text
- normalized_text

### Gram Posting

- gram
- page_id
- positions

### Search Result

- document_id
- page_id
- page_number
- match_start
- match_end
- display_context_before
- display_context_match
- display_context_after
- preview_image_cache_key

## 10. UI Layout Draft

### Left Pane

- file open control
- PDF selection control
- indexing status area
- search input field
- Enter-based search action
- result count
- scrollable result list

Each result item should show:

- document title
- page number
- matched snippet
- surrounding text
- low-resolution thumbnail

### Right Pane

- selected page title and page number
- high-resolution page image
- zoom or fit controls

## 11. Edge Cases

- PDFs with broken text extraction order
- PDFs with mixed Korean and English text
- PDFs with repeated headers and footers
- Very short queries that create too many 2-gram collisions
- Image-heavy PDFs with limited extractable text
- Large documents that exceed memory if all previews are loaded at once

## 12. Risks and Design Decisions

### Risk 1. 2-Gram Search Noise

Short queries can create many false positives.

Mitigation:

- require post-filtering with normalized substring verification
- add order-aware ranking after candidate retrieval
- consider minimum query length rules

### Risk 2. Whitespace Removal Mapping

When whitespace is removed for indexing, match offsets in normalized text may not align directly with original text.

Mitigation:

- keep a mapping table from normalized offsets to original offsets

### Risk 3. PDF Text Quality

Some PDFs have poor extraction quality.

Mitigation:

- define OCR support as a later phase
- make extraction failures visible to the user

### Risk 4. Rendering Cost

High-resolution page rendering can be expensive.

Mitigation:

- render thumbnails separately
- lazy-load detail images
- cache recently viewed pages

## 13. Acceptance Criteria

- User can open a PDF in the desktop app.
- User can load multiple PDFs and select one active PDF for search.
- The app indexes extracted page text using whitespace-free 2-gram indexing.
- Search runs when the user presses Enter.
- User can search with or without spaces and still find equivalent text.
- Results that preserve the input keyword order rank above reversed-order matches when both are otherwise valid.
- Search results show page number, surrounding context, and low-resolution preview in the left pane.
- Clicking a result shows the corresponding high-resolution page image in the right pane.
- The UI remains responsive while indexing and rendering are in progress.
- Search over a 100 to 200+ page PDF is fast enough to feel immediate after indexing completes.

## 14. Recommended Phase Split

### Phase 1. MVP

- multiple PDF open and indexing support
- one selected PDF searched at a time
- page text extraction
- normalization and 2-gram index
- fast search
- result list with snippets
- low-resolution thumbnails
- high-resolution selected page view

### Phase 2. Usability

- index persistence
- progress UI
- result highlighting
- cache tuning

### Phase 3. Advanced

- OCR support
- richer ranking
- incremental indexing
- multi-tab document management

## 15. Confirmed Product Decisions

- The application may load multiple PDFs, but search is executed only against one selected PDF at a time.
- OCR for scanned PDFs is excluded from the first release.
- Search runs when the user presses Enter, not on every keystroke.
- Korean text handling remains an open design decision for punctuation-insensitive matching.
