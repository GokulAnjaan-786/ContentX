# ContentForge AI — Backend Dependencies & Follow-Ups (Part 3)

During the development of the Part 3 frontend dashboard, the frontend was designed to strictly consume existing APIs from Part 1 (Auth, Ingestion, Documents) and Part 2 (Understanding Pass, Fact Registry, Generation, Outputs).

To provide a seamless user experience, the frontend includes graceful fallbacks for endpoints that were not confirmed in Parts 1 and 2. The following list details the backend endpoints to implement or extend as small follow-ups:

---

## 1. Dedicated History Endpoint: `GET /history`
- **Purpose**: Retrieves a paginated list of past transformation jobs run within the current user's organization.
- **Suggested Signature**:
  ```http
  GET /history?limit=20&offset=0
  Authorization: Bearer <jwt_token>
  ```
- **Suggested Response**:
  ```json
  [
    {
      "id": "job-uuid",
      "job_id": "job-uuid",
      "document_id": "doc-uuid",
      "document_title": "Q3 Threat Intelligence Report 2026.pdf",
      "status": "completed",
      "selected_outputs": ["linkedin", "executive_summary", "advisory"],
      "created_at": "2026-09-26T10:00:00Z"
    }
  ]
  ```
- **Current Frontend Handling**: The frontend attempts `GET /history`. If this endpoint is not yet mounted on the backend, it transparently falls back to local workspace session history (`contentforge_history`), so the Dashboard and History screens function cleanly without errors.

---

## 2. Editable Output Update: `PUT /outputs/{id}`
- **Purpose**: Persists inline edits made by an operator to a generated output prior to export or review.
- **Suggested Signature**:
  ```http
  PUT /outputs/{output_id}
  Authorization: Bearer <jwt_token>
  Content-Type: application/json

  {
    "content": { ...updated_generator_schema... }
  }
  ```
- **Suggested Response**:
  ```json
  {
    "id": "output-uuid",
    "job_id": "job-uuid",
    "output_type": "linkedin",
    "content": { ... },
    "validation_score": 0.95,
    "status": "completed",
    "updated_at": "2026-09-26T11:00:00Z"
  }
  ```
- **Current Frontend Handling**: The frontend attempts `PUT /outputs/{id}`. If the backend returns 404/405, the frontend caches the updated content in `localStorage` (`contentforge_output_{id}`) and notifies the operator that edits have been preserved locally pending Part 4 backend synchronization.

---

## 3. Document Export Endpoints: `GET /outputs/{id}/export`
- **Purpose**: Generates and streams compiled PDF or DOCX binary downloads.
- **Suggested Signature**:
  ```http
  GET /outputs/{output_id}/export?format=pdf
  GET /outputs/{output_id}/export?format=docx
  Authorization: Bearer <jwt_token>
  ```
- **Current Frontend Handling**: "Copy to Clipboard" is 100% implemented client-side with full markdown/text serialization for all 7 formats. The PDF/DOCX buttons display a clear "Coming in Part 4" tooltip and status rather than executing broken HTTP calls.

---

## 4. Reviewer / Approval Workflow: `POST /outputs/{id}/submit-review`
- **Purpose**: Submits a draft output to the reviewer queue for editorial and compliance sign-off.
- **Constraint Compliance**: As specified in the Part 3 requirements, this workflow is reserved for Part 4. The frontend renders a visible but permanently disabled "Send for Review" button with an explanatory tooltip.
