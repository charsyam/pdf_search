# PDF Search UI Technical Design

## 1. Purpose

This document translates the product requirements into an implementable technical design for the first release.

The first release targets:

- Python desktop application
- Windows support
- Multiple PDFs can be loaded and indexed
- Search is performed against one selected PDF at a time
- OCR is excluded
- Search runs when the user presses Enter
- Search uses whitespace-insensitive 2-gram indexing
- Ranking prefers matches that preserve the query term order

## 2. Technology Choices

### UI

- `PySide6`

Reason:

- Mature Windows support
- Good split-pane desktop UI support
- Clean threading model with `QThreadPool`, `QRunnable`, or signal-slot patterns
- Straightforward image display, scroll area, and list item customization

### PDF Processing

- `PyMuPDF` (`fitz`)

Reason:

- Fast page text extraction
- Reliable page rasterization for both thumbnail and detail images
- Possibility to use text coordinates later for match highlighting

### Local Storage

- `SQLite`

Reason:

- Good fit for catalog metadata and per-PDF persistent index structures
- Easy to ship with a desktop app
- No external service dependency

### Packaging

- `PyInstaller` for Windows packaging in a later step

## 3. High-Level Architecture

The system is divided into five layers:

1. UI layer
2. application service layer
3. search engine layer
4. PDF extraction and rendering layer
5. persistence and cache layer

### 3.1 UI Layer

Responsibilities:

- file open flow
- active PDF selection
- search input and Enter submission
- result list rendering
- selected page detail viewer
- progress and status updates

Suggested screens and widgets:

- main window
- left pane:
  - PDF selector
  - search input
  - result count label
  - search result list
- right pane:
  - selected document and page label
  - high-resolution image viewer
  - zoom controls
- bottom or top status bar:
  - indexing progress
  - rendering status

### 3.2 Application Service Layer

Responsibilities:

- coordinate UI actions
- dispatch background jobs
- connect search results to rendering requests
- enforce one-selected-PDF search rule

Main services:

- `DocumentRegistryService`
- `IndexingService`
- `SearchService`
- `PreviewService`
- `DetailRenderService`

### 3.3 Search Engine Layer

Responsibilities:

- text normalization
- token segmentation for order-aware scoring
- 2-gram generation
- candidate retrieval
- exact normalized substring verification
- order-aware ranking
- display context extraction

### 3.4 PDF Extraction and Rendering Layer

Responsibilities:

- page text extraction
- optional text block extraction for future highlight support
- low-resolution thumbnail generation
- high-resolution page rendering

### 3.5 Persistence and Cache Layer

Responsibilities:

- global document catalog storage
- per-PDF page and posting storage
- thumbnail cache
- high-resolution rendered page cache

## 4. Proposed Project Structure

Suggested initial structure:

```text
src/
  app/
    main.py
    bootstrap.py
  ui/
    main_window.py
    widgets/
      pdf_selector.py
      search_bar.py
      result_list.py
      result_item_widget.py
      page_viewer.py
      status_bar.py
  services/
    document_registry.py
    indexing_service.py
    search_service.py
    preview_service.py
    render_service.py
  domain/
    models.py
    search_types.py
  pdf/
    extractor.py
    renderer.py
  search/
    normalizer.py
    tokenizer.py
    ngram_index.py
    ranker.py
    context_extractor.py
  storage/
    db.py
    repositories.py
    cache.py
  workers/
    indexing_worker.py
    thumbnail_worker.py
    render_worker.py
tests/
  search/
  services/
  pdf/
docs/
```

If the repo stays small initially, these may start as fewer modules and split later.

## 5. Main Data Flow

### 5.1 PDF Load and Index Flow

1. User opens PDF files.
2. `DocumentRegistryService` registers metadata.
3. `IndexingService` schedules background indexing per PDF.
4. `pdf.extractor` iterates pages and extracts page text.
5. `search.normalizer` creates normalized text and offset mapping.
6. `search.ngram_index` generates 2-gram postings for each page.
7. Page and posting data are stored in SQLite.
8. UI receives progress updates.
9. Indexed PDFs become selectable in the PDF selector.

### 5.2 Search Flow

1. User selects one PDF.
2. User types query and presses Enter.
3. The application opens or reuses the selected PDF's index database.
4. `SearchService` normalizes the query.
5. Query terms and 2-grams are derived.
6. Candidate pages are retrieved from the selected PDF index database only.
7. Candidate pages are verified by normalized substring match or strong gram overlap.
8. Candidates are scored using exactness, order preservation, and gram coverage.
9. Display context is extracted from original text.
10. Result list is returned to the UI.
11. Thumbnails are requested lazily for visible rows only.

### 5.3 Result Click Flow

1. User clicks a result row.
2. UI requests high-resolution page render for that page.
3. `DetailRenderService` checks in-memory cache, then disk cache, then renders via `pdf.renderer`.
4. The right pane displays the image.

## 6. Text Normalization Design

Normalization must support whitespace-insensitive matching while preserving enough information to map matches back to readable original text.

### 6.1 Normalization Rules

First-release normalization rules:

- Unicode normalization with `NFKC`
- convert line breaks, tabs, and repeated whitespace to removable search separators
- remove all whitespace for indexed text
- keep punctuation in normalized text for first release
- optionally lowercase Latin text

Important decision:

- Spaces are ignored for search
- Punctuation is not ignored in first release, except where it naturally disappears during exact verification logic for order-aware matching variants

### 6.2 Dual Text Representation

For each page, store:

- `original_text`
- `normalized_text_no_space`
- `norm_to_original_map`

`norm_to_original_map` is an integer array where each normalized character offset maps to the original text offset.

Example:

```text
original_text:      "해외 동포"
normalized_text:    "해외동포"
offset mapping:     [0, 1, 3, 4]
```

This allows the system to:

- find matches in normalized text
- recover approximate original text boundaries
- extract readable snippets around a match

## 7. Query Interpretation

The query must produce two views:

- a normalized compact form for fast matching
- an ordered token sequence for ranking

### 7.1 Query Normalization

Input:

- `해외 동포`

Derived forms:

- raw query: `해외 동포`
- split tokens: `["해외", "동포"]`
- normalized compact query: `해외동포`
- 2-grams: `["해외", "외동", "동포"]`

### 7.2 Tokenization Strategy for Ranking

Token order ranking should use whitespace-delimited query tokens from the user input.

For the first release:

- split query on whitespace
- discard empty tokens
- preserve user-entered order

This design is intentionally simple and predictable.

## 8. Index Design

### 8.1 Indexing Unit

Use page-level indexing.

Reason:

- the UI displays results at page granularity
- page render is the natural click target
- page-level storage keeps implementation simpler

### 8.2 Inverted Index Shape

For each PDF-specific index database, store:

- page metadata
- normalized page text
- postings by 2-gram

Conceptual shape:

```text
gram -> [(page_id, [positions...]), ...]
```

Where:

- `gram` is a 2-character normalized unit
- `positions` are starting offsets in `normalized_text_no_space`

### 8.3 Candidate Retrieval

For a query:

1. generate all query 2-grams
2. fetch postings for those grams from the selected PDF index database only
3. count matched grams per page
4. build candidate pages above a threshold
5. verify exact normalized substring match where possible

Recommended first-release threshold:

- for normalized query length 1 to 2: special-case direct scan
- for normalized query length 3 or more: require at least 50 percent gram overlap before exact verification

This threshold can be tuned after measurement.

## 9. Ranking Design

Ranking is the most important behavior detail for perceived search quality.

### 9.1 Ranking Goals

- exact normalized phrase matches should appear first
- results preserving query token order should outrank reversed-order matches
- whitespace and hyphen differences should not penalize a good match too heavily
- result order should remain stable

### 9.2 Scoring Signals

Each result should compute these signals:

- `exact_compact_match`
  - whether normalized compact query appears as a direct substring
- `ordered_token_match`
  - whether query tokens appear in the page text in the same order
- `adjacent_token_match`
  - whether ordered tokens appear with only whitespace or light separators between them
- `gram_overlap_score`
  - fraction or count of matching 2-grams
- `match_position_score`
  - optional small bonus for earlier page occurrence
- `page_number_score`
  - stable tie-breaker

### 9.3 First-Release Sort Priority

Sort by:

1. `exact_compact_match` descending
2. `adjacent_token_match` descending
3. `ordered_token_match` descending
4. `gram_overlap_score` descending
5. `first_match_offset` ascending
6. `page_number` ascending

### 9.4 Interpretation Example

Query:

- `해외 동포`

Preferred order:

1. `해외동포`
2. `해외-동포`
3. `해외 동포`
4. `해외에 있는 동포`
5. `동포 해외`

Implementation note:

- `해외-동포` and `해외 동포` may not be compact exact matches if punctuation is retained in one path, but they should still receive strong `adjacent_token_match` and `ordered_token_match` scores.

### 9.5 Order-Aware Matching Algorithm

For each verified candidate page:

1. locate positions of each query token in original text and normalized text
2. find the earliest chain of token hits that preserves input order
3. classify the chain:
   - compact adjacent
   - separator-adjacent
   - ordered but distant
   - unordered only
4. score based on class

Suggested classes:

- `compact_adjacent`
  - tokens collapse into a contiguous normalized substring
- `separator_adjacent`
  - tokens are separated only by spaces or punctuation like `-`
- `ordered_near`
  - tokens appear in order within a bounded window
- `unordered`
  - same tokens exist but not in user order

## 10. Snippet and Context Extraction

The UI requires surrounding text that is readable, not only offsets.

### 10.1 Context Strategy

Preferred strategy:

- extract the matched sentence if sentence boundaries can be found
- otherwise take a character window around the original match

Recommended first-release sentence delimiters:

- `.`
- `!`
- `?`
- newline
- Korean full-stop equivalents when present

### 10.2 Snippet Data

Each result should include:

- `context_before`
- `context_match`
- `context_after`
- `first_match_offset`
- `match_class`

### 10.3 Display Marking

If UI complexity is acceptable, highlight the matched text span in the snippet.

## 11. Thumbnail and Detail Rendering Design

### 11.1 Thumbnail Rendering

Use low DPI page renders, such as:

- 72 to 96 DPI

Rules:

- render lazily when result rows become visible
- cache by `(index_key, page_number, size_bucket)`
- keep thumbnails on disk and in memory

### 11.2 Detail Rendering

Use higher DPI renders, such as:

- 150 to 200 DPI for first release

Rules:

- render only the selected page
- reuse cached image when available
- render asynchronously to avoid UI stalls

### 11.3 Cache Strategy

Use two cache tiers:

- in-memory LRU cache for recent thumbnails and detail images
- disk cache for persisted image files

Cache keys:

- index key or document hash
- page number
- render mode
- dpi or size bucket

## 12. Storage Design

Use a hybrid SQLite layout:

- one global `catalog.db`
- one per-PDF index database file

This matches the product behavior where multiple PDFs may exist, but search is always scoped to one selected PDF.

Recommended directory layout:

```text
data/
  catalog.db
  indexes/
    <index_key>.db
  cache/
    thumbs/
    renders/
```

`index_key` should be derived from:

- normalized absolute PDF path
- file size
- file modification time
- optional schema version salt

Reason:

- fast lookup without reading the whole file
- simple invalidation when the PDF changes

## 13. Global Catalog Schema

The global catalog tracks registered PDFs and the per-PDF index file assigned to each one.

### 13.1 Catalog Documents

```sql
CREATE TABLE documents (
  document_id INTEGER PRIMARY KEY,
  file_path TEXT NOT NULL UNIQUE,
  file_name TEXT NOT NULL,
  file_size INTEGER NOT NULL,
  file_mtime REAL NOT NULL,
  index_key TEXT NOT NULL UNIQUE,
  index_db_path TEXT NOT NULL,
  index_version INTEGER NOT NULL,
  page_count INTEGER NOT NULL,
  status TEXT NOT NULL,
  indexed_at REAL
);
```

Recommended indexes:

```sql
CREATE INDEX idx_documents_status
ON documents(status);
```

## 14. Per-PDF Index Database Schema

Each indexed PDF gets its own SQLite file in `indexes/<index_key>.db`.

### 14.1 Pages

```sql
CREATE TABLE pages (
  page_id INTEGER PRIMARY KEY,
  page_number INTEGER NOT NULL,
  original_text TEXT NOT NULL,
  normalized_text TEXT NOT NULL,
  offset_map_blob BLOB NOT NULL
);
```

### 14.2 Gram Postings

```sql
CREATE TABLE gram_postings (
  gram TEXT NOT NULL,
  page_id INTEGER NOT NULL,
  positions_blob BLOB NOT NULL,
  PRIMARY KEY (gram, page_id),
  FOREIGN KEY(page_id) REFERENCES pages(page_id)
);
```

Recommended indexes:

```sql
CREATE INDEX idx_pages_page_number
ON pages(page_number);

CREATE INDEX idx_postings_gram
ON gram_postings(gram);
```

Optional metadata table:

```sql
CREATE TABLE index_meta (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
```

Suggested metadata entries:

- source file path
- source file size
- source file mtime
- page count
- index version
- created at

## 15. Search and DB Interaction Strategy

SQLite is not the ranking engine. It is the persistent candidate store.

Search execution should follow this pattern:

1. look up the selected PDF in `catalog.db`
2. open its per-PDF index database
3. query `gram_postings` for the query grams
4. aggregate page candidates in Python
5. load only candidate page rows from `pages`
6. run exact verification and order-aware ranking in Python
7. return final ranked results

Important rule:

- do not use SQLite `LIKE '%...%'` as the primary search path

Reason:

- poor performance on large text bodies
- weak control over ranking
- difficult to express order-aware phrase scoring

## 16. Background Job Model

### 16.1 Job Types

- document indexing job
- thumbnail render job
- detail render job
- search job

### 16.2 Threading Rules

- UI thread only updates widgets
- background workers do extraction, indexing, search, and rendering
- results return via Qt signals

### 16.3 Cancellation Rules

- if the user changes the selected PDF, in-flight search results for the previous PDF should be discarded
- if the user submits a new query, older search jobs should be ignored on completion
- detail renders for pages no longer selected can be dropped from immediate display, but may still remain cached

## 17. Performance Plan

### 17.1 Target Scenarios

- single PDF with 100 to 200+ pages
- mixed Korean and English text
- repeated search on an already indexed PDF

### 17.2 Key Optimizations

- page-level inverted 2-gram index
- per-PDF SQLite index file
- selected-PDF-only search scope
- candidate filtering before exact verification
- lazy thumbnail rendering
- high-resolution detail rendering only on click
- persistent per-PDF SQLite-backed index

Recommended connection strategy:

- keep `catalog.db` open for the application lifetime
- keep only the selected PDF index DB open by default
- optionally retain the previous one or two PDF DB connections in an LRU pool

Recommended SQLite pragmas for per-PDF index DB:

- `journal_mode=WAL`
- `synchronous=NORMAL`
- `temp_store=MEMORY`
- `mmap_size` enabled when practical

These should be validated on Windows during benchmarking.

### 17.3 Measurements to Capture

- PDF indexing time by page count
- query latency
- candidate count before and after verification
- per-PDF DB open time
- thumbnail render latency
- detail render latency
- peak memory usage

## 18. Error Handling

### 18.1 PDF Extraction Failures

- show document status as failed or partial
- keep the application responsive
- allow the user to retry or remove the document

### 18.2 Cache Failures

- if disk cache read fails, rerender
- if disk cache write fails, continue with in-memory-only behavior

### 18.3 Search Edge Cases

- empty query should return no results and not start search
- one-character query should use direct normalized scan rather than 2-gram postings only
- pages with empty extracted text should be skipped

## 19. Testing Strategy

### 19.1 Unit Tests

- normalization behavior
- offset mapping correctness
- 2-gram generation
- candidate retrieval
- ranking order for ordered vs reversed phrases
- snippet extraction

### 19.2 Integration Tests

- PDF indexing pipeline
- `catalog.db` and per-PDF DB creation
- per-PDF SQLite persistence and reload
- selected-PDF-only search
- thumbnail generation and cache hit behavior

### 19.3 Ranking Test Cases

For query `해외 동포`, verify ordering such as:

1. `해외동포`
2. `해외-동포`
3. `해외 동포`
4. `해외에 있는 동포`
5. `동포 해외`

The exact ordering between 2 and 3 may be tuned later, but both must rank above reversed order.

## 20. MVP Delivery Sequence

1. Bootstrap PySide6 app shell with split-pane layout
2. Add PDF open and selected-PDF management
3. Add PDF text extraction using PyMuPDF
4. Implement normalization and offset mapping
5. Implement `catalog.db` and per-PDF index DB creation
6. Implement Enter-based search for selected PDF
7. Implement exact verification and order-aware ranking
8. Implement result snippets
9. Implement lazy thumbnails
10. Implement high-resolution detail pane rendering
11. Add tests and benchmark sample PDFs

## 21. Open Design Choice

One item remains intentionally open:

- whether punctuation-insensitive matching should be added for Korean phrase search in the first release or deferred

Current recommendation:

- defer broad punctuation-insensitive normalization until after baseline ranking and correctness are validated
