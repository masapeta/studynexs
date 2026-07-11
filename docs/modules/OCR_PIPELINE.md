# OCR Pipeline

> Module dashboard · Master: [`../PLATFORM_STATUS.md`](../PLATFORM_STATUS.md)

## Status

**🟡 Partial** (feature-specific, not unified)

## Owner

Vision eval + admissions extract (converging to FILE_PROCESSING)

## Features

| Feature | State |
|---------|-------|
| Answer-sheet vision OCR | ✅ `answer_sheet_vision.py` |
| Async eval job (Arq) | ✅ |
| Admissions document OCR | ✅ fragment |
| Unified Document Intelligence pipeline | ⬜ |

## Files

`apps/api/app/modules/examinations/services/answer_sheet_vision.py` · school_ops admission extract

## Used by

Assessment Intelligence · Admissions

## Tests

`tests/test_answer_sheet_eval.py` (vision paths)
