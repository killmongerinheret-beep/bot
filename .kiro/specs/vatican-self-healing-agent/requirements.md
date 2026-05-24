# Requirements Document

## Introduction

The Vatican Self-Healing Agent is an autonomous subsystem that monitors the Vatican Museums ticket bot for failures, diagnoses root causes by comparing live Vatican API responses against a RAG knowledge base of the codebase and Vatican website structure, generates targeted code fixes, validates them, deploys them, and notifies the admin via Telegram. The agent must handle the seven known failure modes: stale ticket IDs, API response format changes, expired JSESSIONID sessions, ticket name renames, new unhandled ticket types, Cloudflare/Turnstile challenge changes, and API endpoint/parameter changes.

---

## Glossary

- **Agent**: The Vatican Self-Healing Agent — the autonomous system described in this document.
- **Bot**: The existing Vatican Museums ticket monitoring bot (Django/Celery backend).
- **RAG_Store**: The vector database containing indexed snapshots of the Vatican website structure, API response schemas, and the bot's codebase.
- **Failure_Detector**: The Agent component that continuously monitors bot health signals.
- **Diagnostician**: The Agent component that queries the RAG_Store and live Vatican APIs to identify the root cause of a detected failure.
- **Fix_Generator**: The Agent component that produces code patches based on the Diagnostician's output.
- **Validator**: The Agent component that runs the generated fix in an isolated environment before deployment.
- **Deployer**: The Agent component that applies a validated fix to the live codebase and restarts affected services.
- **Notifier**: The Agent component that sends structured Telegram messages to the admin.
- **Health_Signal**: A measurable indicator of bot health — HTTP status codes, slot counts, error log entries, Celery task failure rates, or Telegram notification delivery failures.
- **Failure_Event**: A Health_Signal that crosses a defined threshold, triggering the Agent pipeline.
- **Fix_Candidate**: A code patch produced by the Fix_Generator, not yet validated.
- **Validated_Fix**: A Fix_Candidate that has passed all Validator checks.
- **Rollback_Snapshot**: A copy of the affected file(s) taken immediately before a Deployer action.
- **Admin**: The human operator identified by `ADMIN_TELEGRAM_IDS` in the environment.
- **Isolation_Sandbox**: A subprocess or temporary module environment used by the Validator to run fixes without touching the live bot.
- **Ingestion_Pipeline**: The process that crawls Vatican API endpoints and the bot codebase and upserts embeddings into the RAG_Store.

---

## Requirements

### Requirement 1: Continuous Health Monitoring

**User Story:** As an admin, I want the Agent to continuously watch the bot's health signals so that failures are detected within minutes of occurring.

#### Acceptance Criteria

1. THE Failure_Detector SHALL poll the following Health_Signals at a configurable interval (default: 60 seconds): Celery task failure rate, Vatican API HTTP status codes returned by `run_search_api_vatican_monitor`, zero-slot results on dates that previously returned slots, and Telegram notification delivery failures.
2. WHEN a Vatican API call returns HTTP 500 on three consecutive checks for the same `(date, ticket_name)` pair, THE Failure_Detector SHALL emit a Failure_Event with type `stale_ticket_id`.
3. WHEN the `timeavail` API returns slots where `residual == 0` and `availability == "AVAILABLE"` on two consecutive checks, THE Failure_Detector SHALL emit a Failure_Event with type `false_positive_residual`.
4. WHEN a JSESSIONID cookie is absent from a Vatican API response that previously set one, THE Failure_Detector SHALL emit a Failure_Event with type `session_expired`.
5. WHEN `match_ticket_by_name` returns `None` for a ticket name that was successfully matched within the previous 24 hours, THE Failure_Detector SHALL emit a Failure_Event with type `ticket_name_changed`.
6. WHEN the search API returns a ticket whose `id` does not match any name pattern in the existing matching logic, THE Failure_Detector SHALL emit a Failure_Event with type `new_ticket_type`.
7. WHEN a Vatican API endpoint returns HTTP 403 or a response body containing Cloudflare or Turnstile challenge markers, THE Failure_Detector SHALL emit a Failure_Event with type `cloudflare_challenge`.
8. WHEN a Vatican API endpoint returns HTTP 404 or a JSON schema that does not match the last known schema for that endpoint, THE Failure_Detector SHALL emit a Failure_Event with type `api_structure_changed`.
9. THE Failure_Detector SHALL deduplicate Failure_Events of the same type for the same endpoint or ticket within a 10-minute window to prevent alert storms.

---

### Requirement 2: RAG Knowledge Base Ingestion

**User Story:** As an admin, I want the Agent to maintain an up-to-date knowledge base of the Vatican API structure and the bot's codebase so that the Diagnostician has accurate context for generating fixes.

#### Acceptance Criteria

1. THE Ingestion_Pipeline SHALL index the following sources into the RAG_Store: all Python source files under `backend/` and `worker_vatican/`, the Vatican API response schemas for `resultPerTag` and `timeavail` endpoints, and the `VATICAN_BOT_RULES.md` mandatory rules document.
2. WHEN a source file is modified on disk, THE Ingestion_Pipeline SHALL re-index that file within 5 minutes of the modification.
3. THE Ingestion_Pipeline SHALL crawl the live Vatican `resultPerTag` API for a representative set of dates (next 7 days) and upsert the response schemas into the RAG_Store on a configurable schedule (default: every 6 hours).
4. THE Ingestion_Pipeline SHALL store each indexed chunk with metadata including: source file path, last modified timestamp, Vatican API endpoint name, and schema version hash.
5. IF the RAG_Store is unavailable, THEN THE Ingestion_Pipeline SHALL retry with exponential backoff (initial delay 30 seconds, maximum 5 retries) and emit a Health_Signal indicating RAG unavailability.
6. THE RAG_Store SHALL retain the two most recent schema versions for each Vatican API endpoint to enable diff-based diagnosis.

---

### Requirement 3: Failure Diagnosis

**User Story:** As an admin, I want the Agent to automatically identify what changed on Vatican's side so that fixes target the actual root cause.

#### Acceptance Criteria

1. WHEN a Failure_Event is received, THE Diagnostician SHALL query the RAG_Store with the Failure_Event type and affected endpoint as the search context and retrieve the top 5 most relevant chunks.
2. WHEN the Failure_Event type is `stale_ticket_id`, THE Diagnostician SHALL call the live `resultPerTag` API, compare the returned ticket IDs against the IDs stored in the RAG_Store snapshot, and produce a diagnosis report identifying which IDs changed.
3. WHEN the Failure_Event type is `api_structure_changed`, THE Diagnostician SHALL diff the current live API response schema against the most recent RAG_Store snapshot and produce a diagnosis report listing added, removed, and changed fields.
4. WHEN the Failure_Event type is `ticket_name_changed`, THE Diagnostician SHALL retrieve all ticket names from the live `resultPerTag` API and compare them against the name patterns in `match_ticket_by_name` to identify unmatched names.
5. WHEN the Failure_Event type is `false_positive_residual`, THE Diagnostician SHALL retrieve the raw `timeavail` response and identify the filtering condition in `check_availability` that failed to exclude the false positive.
6. THE Diagnostician SHALL produce a structured diagnosis report containing: Failure_Event type, affected component (file path and function name), root cause description, confidence score (0.0–1.0), and recommended fix strategy.
7. IF the Diagnostician confidence score is below 0.6, THEN THE Diagnostician SHALL include a `requires_human_review: true` flag in the diagnosis report and THE Notifier SHALL alert the Admin before any fix is attempted.

---

### Requirement 4: Automated Fix Generation

**User Story:** As an admin, I want the Agent to generate targeted code fixes based on the diagnosis so that the bot recovers without manual intervention.

#### Acceptance Criteria

1. WHEN a diagnosis report is produced with confidence score ≥ 0.6, THE Fix_Generator SHALL produce a Fix_Candidate as a unified diff patch targeting the specific file and function identified in the diagnosis report.
2. WHEN the Failure_Event type is `stale_ticket_id`, THE Fix_Generator SHALL produce a Fix_Candidate that updates the ticket ID resolution logic in `VaticanSearchAPIMonitor.resolve_ticket_ids` to use the fresh IDs identified by the Diagnostician.
3. WHEN the Failure_Event type is `ticket_name_changed`, THE Fix_Generator SHALL produce a Fix_Candidate that adds the new ticket name pattern to the keyword list in `VaticanSearchAPIMonitor.match_ticket_by_name` without removing existing patterns.
4. WHEN the Failure_Event type is `false_positive_residual`, THE Fix_Generator SHALL produce a Fix_Candidate that tightens the `residual` filtering condition in `VaticanSearchAPIMonitor.check_availability` to exclude slots where `residual == 0`.
5. WHEN the Failure_Event type is `api_structure_changed`, THE Fix_Generator SHALL produce a Fix_Candidate that updates the response parsing logic to handle the new field names or structure identified in the diagnosis report.
6. WHEN the Failure_Event type is `new_ticket_type`, THE Fix_Generator SHALL produce a Fix_Candidate that adds the new ticket type's name keywords to the matching strategy in `match_ticket_by_name`.
7. THE Fix_Generator SHALL not produce Fix_Candidates that modify authentication credentials, database connection strings, proxy configurations, or Telegram bot tokens.
8. THE Fix_Generator SHALL include a human-readable explanation of each change in the Fix_Candidate metadata.
9. IF no Fix_Candidate can be generated for a Failure_Event type, THEN THE Fix_Generator SHALL set the Fix_Candidate status to `no_fix_available` and THE Notifier SHALL alert the Admin with the full diagnosis report.

---

### Requirement 5: Fix Validation

**User Story:** As an admin, I want every generated fix to be tested before deployment so that the Agent never makes the bot worse.

#### Acceptance Criteria

1. WHEN a Fix_Candidate is produced, THE Validator SHALL apply the patch to a copy of the affected file in an Isolation_Sandbox without modifying the live codebase.
2. THE Validator SHALL execute the existing unit tests for the patched module within the Isolation_Sandbox and require all tests to pass before promoting the Fix_Candidate to Validated_Fix status.
3. WHEN the Failure_Event type is `stale_ticket_id` or `ticket_name_changed`, THE Validator SHALL make a live call to the Vatican `resultPerTag` API using the patched logic and verify that at least one ticket is returned with a non-null ID.
4. WHEN the Failure_Event type is `false_positive_residual`, THE Validator SHALL replay the raw `timeavail` response captured during diagnosis through the patched `check_availability` function and verify that slots with `residual == 0` are excluded from the result.
5. IF any Validator check fails, THEN THE Validator SHALL set the Fix_Candidate status to `validation_failed`, discard the Isolation_Sandbox copy, and THE Notifier SHALL alert the Admin with the failure details.
6. THE Validator SHALL complete all checks within 120 seconds; IF the timeout is exceeded, THEN THE Validator SHALL treat the Fix_Candidate as `validation_failed`.
7. THE Validator SHALL record the full test output and live API response in the Fix_Candidate metadata for audit purposes.

---

### Requirement 6: Safe Deployment

**User Story:** As an admin, I want validated fixes deployed automatically with rollback capability so that recovery is fast but reversible.

#### Acceptance Criteria

1. WHEN a Validated_Fix is ready, THE Deployer SHALL create a Rollback_Snapshot of all files modified by the patch before applying any changes.
2. THE Deployer SHALL apply the Validated_Fix patch to the live codebase and restart only the Celery workers that consume the `vatican` queue, without restarting the Django web process.
3. WHEN the Deployer has applied a fix, THE Failure_Detector SHALL resume monitoring the affected Health_Signals and THE Deployer SHALL wait up to 5 minutes for the Failure_Event that triggered the fix to stop recurring.
4. IF the triggering Failure_Event recurs within 5 minutes of deployment, THEN THE Deployer SHALL automatically restore the Rollback_Snapshot, restart the affected workers, and set the fix status to `rolled_back`.
5. THE Deployer SHALL record a deployment log entry containing: timestamp, Failure_Event type, patched file paths, patch diff, deployment result (deployed/rolled_back), and post-deployment Health_Signal values.
6. THE Deployer SHALL not apply more than 3 automated fixes within any 60-minute window; IF this limit is reached, THEN THE Deployer SHALL pause automated deployments and THE Notifier SHALL alert the Admin.

---

### Requirement 7: Admin Telegram Notifications

**User Story:** As an admin, I want structured Telegram notifications at each stage of the self-healing pipeline so that I always know what the Agent detected and what it did.

#### Acceptance Criteria

1. WHEN a Failure_Event is emitted, THE Notifier SHALL send a Telegram message to the Admin within 30 seconds containing: failure type, affected component, first occurrence timestamp, and a brief description of the symptom.
2. WHEN a diagnosis report is produced, THE Notifier SHALL send a Telegram message to the Admin containing: root cause description, confidence score, affected file and function, and the recommended fix strategy.
3. WHEN a Validated_Fix is deployed, THE Notifier SHALL send a Telegram message to the Admin containing: a summary of the code change, the validation test results, and the deployment timestamp.
4. WHEN a fix is rolled back, THE Notifier SHALL send a Telegram message to the Admin containing: the rollback reason, the restored snapshot details, and instructions for manual intervention.
5. WHEN a Failure_Event has `requires_human_review: true`, THE Notifier SHALL send a Telegram message to the Admin containing the full diagnosis report and SHALL NOT proceed with fix generation until the Admin replies with `/approve` or `/skip`.
6. THE Notifier SHALL use the existing `tg_send` utility function and the `ADMIN_TELEGRAM_IDS` environment variable to identify the recipient.
7. THE Notifier SHALL format all messages using HTML parse mode consistent with the existing bot notification style.
8. IF a Telegram message fails to deliver, THEN THE Notifier SHALL retry up to 3 times with a 10-second delay between attempts and log the failure.

---

### Requirement 8: Audit Trail and Observability

**User Story:** As an admin, I want a complete audit trail of every Agent action so that I can review, replay, or revert any automated change.

#### Acceptance Criteria

1. THE Agent SHALL persist every Failure_Event, diagnosis report, Fix_Candidate, validation result, and deployment log entry to a dedicated Django model (`SelfHealingEvent`) in the existing database.
2. THE `SelfHealingEvent` model SHALL store: event type, timestamp, affected component, diagnosis JSON, fix diff, validation output, deployment result, and rollback status.
3. THE Agent SHALL expose a read-only Django admin view for `SelfHealingEvent` records, filterable by event type, date range, and deployment result.
4. WHEN a Rollback_Snapshot is created, THE Agent SHALL store the snapshot content in the `SelfHealingEvent` record so that the original file can be recovered from the database without relying on the filesystem.
5. THE Agent SHALL retain `SelfHealingEvent` records for a minimum of 90 days before automatic deletion.

---

### Requirement 9: RAG Round-Trip Integrity

**User Story:** As an admin, I want the RAG knowledge base to accurately reflect the current state of the codebase and Vatican APIs so that diagnoses are based on correct information.

#### Acceptance Criteria

1. THE Ingestion_Pipeline SHALL compute a SHA-256 hash of each indexed source file and Vatican API response snapshot at ingestion time.
2. WHEN the Ingestion_Pipeline re-indexes a source, THE Ingestion_Pipeline SHALL verify that the stored embedding can be retrieved by querying the RAG_Store with the source file path and that the retrieved chunk's hash matches the stored hash.
3. FOR ALL Vatican API response snapshots stored in the RAG_Store, parsing the stored JSON then re-serializing it then parsing again SHALL produce an object equal to the original (round-trip property).
4. THE Ingestion_Pipeline SHALL emit a Health_Signal with type `rag_integrity_failure` if any hash mismatch or round-trip failure is detected.
