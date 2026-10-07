# RFC-001: CognitiveZip (.czip) Binary File Format Specification

**Status:** Proposed Open Standard  
**Version:** 1.0.0  
**Author:** Javohirbek Asqarov (Jasper)  
**Date:** October 2026  
**License:** MIT Open Standard  

---

## 1. Abstract

This document defines the formal binary format, structural layout, and runtime algorithmic requirements for **CognitiveZip (`.czip`)**, a next-generation compressed archive format designed specifically for the artificial intelligence era. 

Unlike traditional archival formats (ZIP, TAR, 7Z) which require linear scanning or full decompression to inspect internal contents, CognitiveZip implements a **tail-indexed random-access chunk layout** coupled with an **embedded lexical-semantic inverted index**. This allows both human developers and autonomous AI agents to execute sub-millisecond semantic search queries and selective single-file in-memory reads without performing disk-level extraction.

---

## 2. Terminology & Requirements

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", and "MAY" in this document are to be interpreted as described in RFC 2119.

- **Archive:** A single file adhering to the `.czip` binary layout.
- **Payload Chunk:** An independently compressed byte sequence corresponding to a single archived file.
- **Cognitive Index:** An embedded data structure combining an address table and a BM25 lexical-semantic inverted index.
- **Zero-Extraction:** Retrieving content or metadata from within an archive without creating uncompressed files on a filesystem.

---

## 3. High-Level Binary Structure

A `.czip` file MUST consist of four contiguous sections arranged in sequential order:

```
+-----------------------------------------------------------------------------------+
| Section 1: Magic Header (6 bytes)                                                 |
|   'C' 'Z' 'I' 'P' 0x01 0x00                                                       |
+-----------------------------------------------------------------------------------+
| Section 2: Compressed File Payload Chunks (Variable Length)                       |
|   [Chunk 0: DEFLATE/ZSTD compressed payload]                                      |
|   [Chunk 1: DEFLATE/ZSTD compressed payload]                                      |
|   ...                                                                             |
|   [Chunk N-1: DEFLATE/ZSTD compressed payload]                                    |
+-----------------------------------------------------------------------------------+
| Section 3: Cognitive Semantic Index (Variable Length)                             |
|   [Compressed JSON/Binary: File Table + BM25 Inverted Postings + Line Snippets]   |
+-----------------------------------------------------------------------------------+
| Section 4: Tail Anchor Footer (28 bytes fixed size)                               |
|   [Index Offset: uint64 (8B)]                                                     |
|   [Index Compressed Size: uint64 (8B)]                                            |
|   [Index CRC-32: uint32 (4B)]                                                     |
|   [End Magic: 'CZIPEND\0' (8B)]                                                   |
+-----------------------------------------------------------------------------------+
```

---

## 4. Detailed Specification

### 4.1 Section 1: Magic Header

The archive MUST start with an exact 6-byte magic identifier:

| Byte Offset | Value | Description |
|:---|:---|:---|
| `0x00` | `0x43` (`'C'`) | Protocol ASCII Identifier |
| `0x01` | `0x5A` (`'Z'`) | Protocol ASCII Identifier |
| `0x02` | `0x49` (`'I'`) | Protocol ASCII Identifier |
| `0x03` | `0x50` (`'P'`) | Protocol ASCII Identifier |
| `0x04` | `0x01` | Major Version Number (1) |
| `0x05` | `0x00` | Minor Version Number (0) |

Parsers MUST reject any file whose leading 6 bytes do not match `CZIP\x01\x00`.

---

### 4.2 Section 2: Compressed File Chunks

Each archived file is compressed independently:
- **Compression Algorithm:** Standard DEFLATE (RFC 1951 / zlib) or Zstandard (RFC 8878).
- **Chunk Boundary:** Chunks are written contiguously. Individual chunks do NOT require local per-chunk headers; offset and length coordinates are registered globally in the Cognitive Index.
- **Integrity:** Uncompressed content MUST be verified against its IEEE 802.3 CRC-32 checksum stored in the File Table.

---

### 4.3 Section 3: Cognitive Semantic Index

The Cognitive Semantic Index is serialized and compressed as a single contiguous stream. It contains two primary components:

#### 4.3.1 File Table (`file_table`)
A dictionary mapping normalized UTF-8 relative POSIX paths to chunk coordinates:
```json
{
  "src/auth/jwt.py": {
    "offset": 6,
    "comp_size": 348,
    "orig_size": 812,
    "crc32": 2847291034
  }
}
```

#### 4.3.2 Semantic Inverted Index (`semantic_index`)
Contains statistical corpus metadata and BM25 postings for tokenized terms:
- `total_docs`: Total indexed text/code documents.
- `avg_doc_len`: Mean token length across indexed documents.
- `inverted_index`: Token to `[(file_path, term_frequency)]` postings.
- `snippets_cache`: Line number to stripped line text mapping for snippet synthesis.

---

### 4.4 Section 4: Tail Anchor Footer

The archive terminates with a strictly fixed 28-byte footer. Decoders MUST seek to `(FileLength - 28)` to read the footer.

| Field Offset | Type | Endianness | Size | Description |
|:---|:---|:---|:---|:---|
| `0` | `uint64` | Big-Endian | 8 bytes | Absolute file offset where Section 3 starts |
| `8` | `uint64` | Big-Endian | 8 bytes | Compressed size of Section 3 in bytes |
| `16` | `uint32` | Big-Endian | 4 bytes | CRC-32 checksum of Section 3 bytes |
| `20` | `char[8]` | Raw ASCII | 8 bytes | `CZIPEND\0` (0x43 0x5A 0x49 0x50 0x45 0x4E 0x44 0x00) |

---

## 5. Tokenization & Search Algorithm

To ensure language-agnostic code search (Python, TypeScript, Go, Rust, C++):

1. **Identifier Decomposition:** Identifiers MUST be split into component sub-tokens:
   - CamelCase: `UserToken` $\to$ `['user', 'token']`
   - snake_case: `jwt_access_token` $\to$ `['jwt', 'access', 'token']`
   - kebab-case: `auth-handler` $\to$ `['auth', 'handler']`
2. **BM25 Scoring Function:**
   $$\text{Score}(D, Q) = \sum_{t \in Q} \text{IDF}(t) \cdot \frac{f(t, D) \cdot (k_1 + 1)}{f(t, D) + k_1 \cdot \left(1 - b + b \cdot \frac{|D|}{\text{avgdl}}\right)}$$
   - Default constants: $k_1 = 1.5$, $b = 0.75$.
   - Bonus multiplier: If term $t$ matches the directory/file path directly, term score is multiplied by $1.5$.

---

## 6. Implementation Conformance (C / Rust / Python)

Any compliant reader in any programming language (C, Rust, Go, TypeScript) MUST implement:
1. **Seek to EOF - 28**: Validate `CZIPEND\0`.
2. **Seek to IndexOffset**: Decompress only the index into RAM.
3. **Seek to ChunkOffset**: When a user queries a single file, decompress solely that chunk.

Disk write operations MUST NOT be performed during search or selective read operations.

---
*Copyright (c) 2026 Javohirbek Asqarov (Jasper). Open Standard Specification.*
