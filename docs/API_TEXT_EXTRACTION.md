# PDF Text Extraction API

## Overview
Extract raw text content from uploaded policy PDFs for AI processing.

## Endpoints

### 1. Extract Text from Policy
**POST** `/api/v1/policies/{policy_id}/extract-text`

Triggers text extraction from a policy PDF document.

**Parameters:**
- `policy_id` (path) - Unique policy identifier
- `force` (query, optional) - Force re-extraction if already extracted (default: false)

**Response:** `TextExtractionResponse`
```json
{
  "policy_id": "pol_abc123xyz",
  "processing_id": 1,
  "status": "completed",
  "character_count": 15420,
  "word_count": 2340,
  "text_preview": "This policy document outlines..."
}
```

**Status Codes:**
- `200 OK` - Text extraction successful
- `404 Not Found` - Policy not found
- `409 Conflict` - Already extracted (use force=true)
- `500 Internal Server Error` - Extraction failed

---

### 2. Get Extracted Text
**GET** `/api/v1/policies/{policy_id}/text`

Retrieves the full extracted text content from a policy.

**Parameters:**
- `policy_id` (path) - Unique policy identifier

**Response:** `ExtractedTextResponse`
```json
{
  "policy_id": "pol_abc123xyz",
  "filename": "healthcare_policy_2024.pdf",
  "extracted_text": "Full text content of the policy document...",
  "character_count": 15420,
  "word_count": 2340,
  "extraction_timestamp": "2024-01-27T18:05:00Z"
}
```

**Status Codes:**
- `200 OK` - Text retrieved successfully
- `404 Not Found` - Policy not found or text not extracted

---

## Usage Examples

### Extract text after uploading a policy

```bash
# 1. Upload policy
curl -X POST "http://localhost:8000/api/v1/policies/upload" \
  -F "file=@policy.pdf"

# 2. Extract text
curl -X POST "http://localhost:8000/api/v1/policies/{policy_id}/extract-text"
```

### Retrieve full extracted text

```bash
curl -X GET "http://localhost:8000/api/v1/policies/{policy_id}/text"
```

### Force re-extraction

```bash
curl -X POST "http://localhost:8000/api/v1/policies/{policy_id}/extract-text?force=true"
```

---

## Error Responses

### Encrypted PDF
```json
{
  "error": {
    "type": "TextExtractionError",
    "message": "PDF is encrypted and cannot be processed"
  }
}
```

### Empty PDF
```json
{
  "error": {
    "type": "TextExtractionError",
    "message": "No text content found in PDF"
  }
}
```

### Already Extracted
```json
{
  "error": {
    "type": "TextExtractionError",
    "message": "Text has already been extracted. Use force=true to re-extract."
  }
}
```

---

## Processing Pipeline

The text extraction integrates with the `PolicyProcessing` table:

1. **Stage**: `TEXT_EXTRACTION`
2. **Status Flow**: `PENDING` → `IN_PROGRESS` → `COMPLETED`/`FAILED`
3. **Result Storage**: Extracted text stored in `result_data` JSON field

This enables tracking and auditing of all extraction attempts.

---

## Next Steps

Once text is extracted, it can be used for:
- **Summarization** - Generate plain-language summaries
- **Embedding** - Create vector embeddings for semantic search
- **Q&A** - Enable RAG-based question answering
- **Classification** - Auto-categorize policies
