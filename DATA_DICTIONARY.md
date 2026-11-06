# Data Dictionary

## `documents.jsonl`

| Field | Type | Meaning |
|---|---|---|
| `document_id` | string | Stable unique evidence identifier |
| `bank_name` | string | Fictional institution name |
| `model_id`, `model_name` | string | Model-family identifiers |
| `document_type` | string | Charter, validation, monitoring, issue, remediation, committee, policy, development, or data-quality record |
| `version` | string | Document version or reporting period |
| `created_date` | ISO date | Date the record was created |
| `effective_date` | ISO date | Date from which its contents apply |
| `expiration_date` | ISO date/null | Last applicable date when explicitly bounded |
| `document_status` | string | `current`, `superseded`, or `historical` |
| `approval_status` | string | Governance state such as approved, reviewed, open, or pending committee |
| `source_authority` | string | Fictional function responsible for the record |
| `supersedes_document_id` | string/null | Prior document replaced by this record |
| `related_issue_ids` | array | Linked fictional issue identifiers |
| `synthetic` | boolean | Always true |
| `content` | string | Retrieval text |

## `questions.jsonl`

| Field | Type | Meaning |
|---|---|---|
| `question_id` | string | Stable unique question identifier |
| `model_id`, `model_name` | string | Model family in scope |
| `category` | string | Direct retrieval, synthesis, temporal update, conflicting evidence, or abstention |
| `split` | string | Train, development, or test |
| `question` | string | User question |
| `as_of_date` | ISO date | Time boundary that the system must respect |
| `expected_answer` | string | Controlled reference answer |
| `gold_document_ids` | array | Documents that support the answer |
| `superseded_document_ids` | array | Older/conflicting documents that should not be treated as authoritative |
| `should_abstain` | boolean | Whether the corpus intentionally lacks the answer |

## Recommended evaluation

Use Recall@5 and mean reciprocal rank for retrieval; correctness, citation precision, temporal accuracy, conflict-resolution accuracy, abstention precision/recall/F1, and unsupported-claim rate for answers. Record latency, token use, API failures, and estimated cost separately.
