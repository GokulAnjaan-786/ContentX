# ContentForge AI — Part 5 Live Demo Script
## Blockchain Trust Layer & Public Verification Portal

This demo script provides step-by-step instructions for judges, evaluators, and stakeholders to witness the cryptographic tamper-evidence and public verification features in a live presentation.

---

### Demo Objective
Demonstrate that:
1. **Source Document Integrity**: Every document uploaded is immediately fingerprinted with SHA-256 and chained into an immutable local ledger.
2. **Reviewer Provenance & Signatures**: When an advisory is approved, it is signed with the reviewer's private Ed25519 key and linked to the source report.
3. **QR Code Export**: Exported files carry an embedded QR code pointing to a completely public verification page.
4. **Tamper Detection**: Altering even a single word in a forwarded advisory immediately causes public verification to fail with a warning.
5. **Full Ledger Integrity**: Administrators can audit the entire multi-block hash-chain in a single click.

---

### Prerequisites
1. Backend running:
   ```bash
   cd backend
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
2. Frontend running:
   ```bash
   cd frontend
   npm run dev
   ```

---

### Step-by-Step Live Demo Flow

#### Step 1: Upload Incident Document & Anchor Provenance
1. Open browser to `http://localhost:3000/login` and log in:
   - **Email**: `operator@test.com`
   - **Password**: `ValidPass123!`
2. Navigate to **New Transformation** (`/new-transformation/upload`).
3. Upload a sample incident report (e.g. `tests/fixtures/sample_incident_report.pdf` or paste text).
4. Point out to the audience:
   > *"Immediately upon upload, ContentForge AI calculates a deterministic SHA-256 digest of the raw document bytes and commits Block #0 (Genesis Block) to the organisation's tamper-evident hash-chain in PostgreSQL. Zero user action required."*

---

#### Step 2: Generate & Approve an Advisory
1. Proceed through the transformation wizard selecting **Advisory** and **Executive Summary**.
2. When generation completes, view the **Advisory** card in the dashboard results.
3. Click **Approve Output**:
   - Backend computes the SHA-256 hash of the exact final JSON payload.
   - Signs the hash using the reviewer's private Ed25519 key (`approval_signatures` table).
   - Commits **Block #1** to the `trust_records` ledger, referencing `previous_record_hash` of Block #0 and `document_id`.

---

#### Step 3: Export & Inspect the Verification QR Code
1. Click the **Export** button on the approved Advisory card.
2. Observe the exported payload:
   - Notice the embedded verification line:
     `"Scan to verify authenticity — contentforge.ai/verify/{record_id}"`
   - Notice the high-resolution QR code generated on the fly encoding `http://localhost:3000/verify/{record_id}`.
3. Highlight to the judges:
   > *"If an attacker prints or PDFs this document, any recipient on their mobile phone or laptop can scan the QR code without needing an account or login."*

---

#### Step 4: Open Public Verification Page (Proof of Authenticity)
1. In an **Incognito / Private Window** (no login cookies):
   - Open `http://localhost:3000/verify/{record_id}`
2. Show the big vibrant green **"✅ AUTHENTIC OFFICIAL OUTPUT"** banner.
3. Walk the audience through the displayed audit proofs:
   - **Issuing Organisation**: Confirmed genuine.
   - **Authorized Reviewer**: Reviewer display name + signature confirmation.
   - **Source Document Provenance**: Linked to unaltered incident report.
   - **Ledger Hash-Chain**: All blocks intact.
   - **Zero Confidential Leakage**: Emphasize that **only SHA-256 digests and block indexes** are shown — confidential corporate secrets never touch public endpoints.

---

#### Step 5: Test Tamper Detection with Modified Text
1. Click **"Verify Another Content / File"** to navigate to `http://localhost:3000/verify`.
2. First, copy and paste the **exact text** of the approved advisory into the box and click **Verify Content Authenticity**.
   - Result: **"✅ Content Perfectly Verified"** (matching SHA-256).
3. Now, make a **subtle malicious change** to the text:
   - Example: Change *"Severity: HIGH"* to *"Severity: LOW"* or delete a single comma.
4. Click **Verify Content Authenticity**.
5. Observe the big vibrant red **"❌ NOT VERIFIED — No Matching Official Record Found"** alert:
   > *"Even a single modified character breaks the SHA-256 mathematical hash. An employee receiving a spoofed security bulletin knows immediately that it was manipulated and not authorized."*

---

#### Step 6: Live 1-Click Trust-Chain Audit (Admin Demo Moment)
1. Switch back to your logged-in administrator window.
2. In your browser or terminal, trigger the admin live chain audit:
   ```bash
   curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/admin/trust-chain/verify
   ```
   Or visit the admin audit section.
3. Show the JSON response:
   ```json
   {
     "organisation_name": "Acme Cyber Defense Corp",
     "intact": true,
     "total_records": 2,
     "broken_at_index": null,
     "latest_record_hash": "6dbc134f7198...",
     "message": "Hash-chain verified successfully: all 2 blocks intact."
   }
   ```
4. Point out the automated test:
   > *"Our automated test suite runs `test_tamper_detection_on_corrupted_historical_record()`. When a historical row in the PostgreSQL database is manually modified by a malicious DBA, `verify_chain()` detects the break immediately and identifies the exact block index."*

---

### Summary Checklist for Evaluators
| Evaluation Criteria | Demonstrated Feature | Proof Mechanism |
|---|---|---|
| **Tamper Evidence** | Local Hash-Chain Ledger | `previous_record_hash` cryptographic link |
| **Tamper Detection** | Historical corruption detection | Automated test altering historical row |
| **Non-Repudiation** | Reviewer Approval Signatures | Asymmetric Ed25519 digital signature |
| **Confidentiality** | Zero sensitive data exposure | Only SHA-256 hashes public |
| **Accessibility** | Public Verification Portal | `/verify` & `/verify/[id]` require no login |
| **Practical Delivery** | Document QR Code Embed | QR code embedded on all exports |
