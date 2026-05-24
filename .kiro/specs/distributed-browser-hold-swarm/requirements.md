# Requirements Document

## Introduction

The Distributed Browser Hold Swarm is a horizontally-scalable system for holding Vatican Museums ticket slots indefinitely across multiple cheap VPS machines. Each "browser worker" node runs inside Docker, pulls hold jobs from a central Redis queue, executes the full Vatican booking UI flow (steps 1–10) using nodriver Chrome, and then re-calls `/api/visit/recap` every 4 minutes via the live browser session to keep the JSESSIONID warm. Multiple worker machines can be deployed as a swarm — each 8 GB VPS handles 8–10 simultaneous browser instances. All hold state and health data is reported back to the central Postgres database on the existing VPS.

---

## Glossary

- **Browser_Worker**: A Docker container that runs on any VPS, receives hold jobs from Redis, and manages one or more nodriver Chrome browser instances.
- **Hold_Job**: A Redis queue message instructing a Browser_Worker to hold a specific Vatican slot.
- **Hold_Session**: A single nodriver Chrome browser instance that has completed the Vatican booking flow (steps 1–10) and is actively re-recapping to keep the slot warm.
- **Re_Recap_Loop**: The background coroutine inside a Hold_Session that calls `/api/visit/recap` every 4 minutes via `page.evaluate` fetch to prevent JSESSIONID expiry.
- **Central_Server**: The existing VPS running Redis, Postgres, Django backend, and Telegram bot.
- **Swarm**: The collection of all Browser_Worker nodes registered and reporting to the Central_Server.
- **Worker_Registry**: The Postgres table tracking each registered Browser_Worker node, its capacity, and last heartbeat.
- **Hold_Record**: The Postgres row (extending the existing `HeldSlot` model) that tracks the status of a single held slot, including which Browser_Worker owns it.
- **Recap_Interval**: The fixed 4-minute period between consecutive `/api/visit/recap` calls within a Hold_Session.
- **Job_Queue**: The Redis list (`swarm:hold_jobs`) from which Browser_Workers pop Hold_Jobs.
- **Result_Queue**: The Redis list (`swarm:hold_results`) to which Browser_Workers push job outcomes.
- **Heartbeat_Key**: The Redis key (`swarm:worker:{worker_id}:heartbeat`) updated by each Browser_Worker every 30 seconds.
- **Capacity**: The maximum number of simultaneous Hold_Sessions a Browser_Worker can run (default 8, configurable).
- **Search_API**: Vatican's `/api/search/resultPerTag` endpoint used to resolve fresh ticket IDs.
- **Timeavail_API**: Vatican's `/api/visit/timeavail` endpoint used to find available time slots.
- **JSESSIONID**: The Vatican session cookie that keeps a hold alive; must be kept warm via the Re_Recap_Loop.

---

## Requirements

### Requirement 1: Hold Job Format and Dispatch

**User Story:** As an operator, I want to push a structured hold job onto the Redis queue so that any available Browser_Worker in the swarm picks it up and executes the Vatican booking flow.

#### Acceptance Criteria

1. THE Job_Queue SHALL accept Hold_Job messages serialised as JSON with the following mandatory fields: `job_id` (UUID string), `date` (DD/MM/YYYY), `slot_time` (HH:MM), `visitors` (integer ≥ 1), `adult_count` (integer ≥ 0), `child_count` (integer ≥ 0), `profile` (object containing `first_name`, `last_name`, `email`, `phone`, `city`, `country`, `birth_date_iso`, `birth_year`, `birth_month`, `birth_day`), and `card` (object containing `holder`, `number`, `expiry`, `cvv`).
2. THE Job_Queue SHALL accept an optional `slot_id` field; WHEN `slot_id` is absent, THE Browser_Worker SHALL resolve it via the Search_API and Timeavail_API before proceeding.
3. WHEN a Hold_Job is pushed, THE Job_Queue SHALL assign it a TTL of 3600 seconds so that unclaimed jobs do not accumulate indefinitely.
4. THE Central_Server SHALL expose a Django management command `dispatch_hold_job` that constructs and pushes a valid Hold_Job to the Job_Queue.
5. WHEN `adult_count + child_count` does not equal `visitors`, THEN THE Job_Queue consumer SHALL reject the job and push an error result to the Result_Queue with `status: "invalid_job"`.

---

### Requirement 2: Browser Worker Registration

**User Story:** As an operator, I want each Browser_Worker node to register itself with the Central_Server on startup so that the swarm membership is always known.

#### Acceptance Criteria

1. WHEN a Browser_Worker container starts, THE Browser_Worker SHALL publish a registration message to the Redis key `swarm:workers` containing: `worker_id` (UUID generated at container start), `hostname`, `ip`, `capacity`, `version`, and `started_at` (ISO-8601 UTC timestamp).
2. THE Browser_Worker SHALL write its registration record to the `Worker_Registry` Postgres table via the Central_Server REST endpoint `POST /api/swarm/workers/register` within 10 seconds of container start.
3. WHEN the Central_Server receives a registration request, THE Central_Server SHALL respond with HTTP 200 and a JSON body containing `accepted: true` and the `worker_id` echoed back.
4. IF the Central_Server is unreachable at startup, THEN THE Browser_Worker SHALL retry registration every 15 seconds until successful, logging each attempt.
5. THE Worker_Registry table SHALL store: `worker_id`, `hostname`, `ip`, `capacity`, `current_load` (integer), `status` (`idle`, `busy`, `draining`, `offline`), `version`, `registered_at`, and `last_heartbeat_at`.

---

### Requirement 3: Worker Heartbeat and Health Reporting

**User Story:** As an operator, I want each Browser_Worker to continuously report its health so that the Central_Server can detect dead nodes and reassign their jobs.

#### Acceptance Criteria

1. WHILE a Browser_Worker is running, THE Browser_Worker SHALL update the Heartbeat_Key in Redis every 30 seconds with a JSON payload containing `worker_id`, `current_load`, `active_sessions` (list of `job_id` strings), `cpu_percent`, `ram_mb_used`, and `timestamp`.
2. WHILE a Browser_Worker is running, THE Browser_Worker SHALL call `PATCH /api/swarm/workers/{worker_id}/heartbeat` on the Central_Server every 60 seconds with the same payload.
3. WHEN the Central_Server has not received a heartbeat for a Browser_Worker for 120 seconds, THE Central_Server SHALL mark that worker's status as `offline` in the Worker_Registry.
4. WHEN a Browser_Worker is marked `offline`, THE Central_Server SHALL re-enqueue all Hold_Jobs owned by that worker that have `hold_status: "acquiring"` back onto the Job_Queue.
5. THE Central_Server SHALL expose `GET /api/swarm/workers/` returning the current state of all registered workers including `worker_id`, `status`, `current_load`, `capacity`, and `last_heartbeat_at`.

---

### Requirement 4: Vatican Booking Flow Execution

**User Story:** As an operator, I want the Browser_Worker to execute the complete Vatican booking flow (steps 1–10) for each Hold_Job so that the slot is reserved and the JSESSIONID is captured.

#### Acceptance Criteria

1. WHEN a Browser_Worker dequeues a Hold_Job, THE Browser_Worker SHALL execute the Vatican booking flow in the following order: (a) resolve fresh `ticket_id` via Search_API matching by name containing "musei vaticani" and "ingresso", (b) navigate to the Vatican deep link `fromtag/{visitors}/{ts}/MV-Biglietti/1` where `ts` is midnight Rome timezone in milliseconds, (c) click `PRENOTA` on the matching ticket card identified by `data-cy='bookTicket_{tid}'`, (d) set visitor quantity, (e) select the target time slot via `data-cy='time'`, (f) click PROCEDI via `data-cy='bookVisit'`, (g) fill the checkout form using the `profile` fields from the Hold_Job, (h) wait for Turnstile resolution (nodriver handles invisibly), (i) click BUY via `data-cy='buyVisit'`.
2. WHEN the Vatican `/api/visit/reservation` call fires (step i), THE Browser_Worker SHALL capture the JSESSIONID cookie from the browser session and store it in the Hold_Record.
3. WHEN the booking flow completes successfully, THE Browser_Worker SHALL push a result to the Result_Queue with `status: "held"`, `job_id`, `worker_id`, `jsessionid`, `recap_id`, `total_price`, `epay_url`, and `held_at` (ISO-8601 UTC).
4. IF any step in the booking flow fails after 3 retries, THEN THE Browser_Worker SHALL push a result to the Result_Queue with `status: "failed"`, `job_id`, `worker_id`, `step` (the step number that failed), and `error` (string description), and SHALL close the browser tab.
5. THE Browser_Worker SHALL resolve a fresh `ticket_id` via the Search_API immediately before clicking PRENOTA, as Vatican changes IDs frequently; THE Browser_Worker SHALL never use a hardcoded or cached ticket ID.
6. WHEN computing the deep link timestamp, THE Browser_Worker SHALL use midnight in the `Europe/Rome` timezone for the target date, expressed as milliseconds since Unix epoch.
7. THE Browser_Worker SHALL use the `visitLang` parameter as an empty string for standard tickets when calling the Timeavail_API.

---

### Requirement 5: Re-Recap Loop (Infinite Hold)

**User Story:** As an operator, I want each active Hold_Session to re-call `/api/visit/recap` every 4 minutes so that the Vatican slot is held indefinitely without expiring.

#### Acceptance Criteria

1. WHEN a Hold_Session is established (JSESSIONID captured), THE Re_Recap_Loop SHALL start immediately and call `/api/visit/recap` via `page.evaluate` fetch within the live browser session every 4 minutes.
2. WHEN the Re_Recap_Loop calls `/api/visit/recap`, THE Re_Recap_Loop SHALL first resolve a fresh `ticket_id` via the Search_API using the same browser session, as Vatican changes IDs between recap calls.
3. WHEN `/api/visit/recap` returns HTTP 200, THE Re_Recap_Loop SHALL update the Hold_Record in Postgres with `last_keepalive_at` (current UTC timestamp) and the new `recap_id`.
4. WHEN `/api/visit/recap` returns a non-200 status, THE Re_Recap_Loop SHALL retry up to 3 times with a 30-second delay between attempts before marking the Hold_Record status as `recap_failed`.
5. WHEN the Hold_Record status is set to `recap_failed`, THE Browser_Worker SHALL send a Telegram notification to the admin chat containing `job_id`, `date`, `slot_time`, `worker_id`, and the HTTP status code received.
6. WHILE a Hold_Session is active, THE Re_Recap_Loop SHALL log each successful recap with `job_id`, `recap_id`, `elapsed_minutes` since hold start, and `next_recap_in` seconds.
7. THE Re_Recap_Loop SHALL use `page.evaluate` to execute the recap fetch call inside the browser context so that the Vatican server sees the same browser fingerprint and JSESSIONID as the original booking flow.

---

### Requirement 6: Hold Capacity Management

**User Story:** As an operator, I want each Browser_Worker to enforce a maximum number of simultaneous Hold_Sessions so that the host machine's RAM is not exhausted.

#### Acceptance Criteria

1. THE Browser_Worker SHALL read its maximum capacity from the environment variable `WORKER_CAPACITY` (default: 8).
2. WHEN a Browser_Worker's `current_load` equals `WORKER_CAPACITY`, THE Browser_Worker SHALL not dequeue additional Hold_Jobs and SHALL leave them on the Job_Queue for other workers.
3. WHEN a Hold_Session ends (either released, failed, or purchased), THE Browser_Worker SHALL decrement `current_load` by 1 and resume polling the Job_Queue.
4. THE Browser_Worker SHALL poll the Job_Queue using a blocking Redis `BLPOP` with a 5-second timeout so that idle workers do not busy-loop.
5. WHEN `current_load` drops below `WORKER_CAPACITY`, THE Browser_Worker SHALL immediately resume polling the Job_Queue without waiting for the next poll cycle.

---

### Requirement 7: Hold Release and Purchase Handoff

**User Story:** As an operator, I want to be able to release a held slot or hand it off for payment so that the slot can be purchased or freed when no longer needed.

#### Acceptance Criteria

1. THE Central_Server SHALL expose `POST /api/swarm/holds/{job_id}/release` which pushes a `release` command to the Redis key `swarm:worker:{worker_id}:commands` for the owning Browser_Worker.
2. WHEN a Browser_Worker receives a `release` command for a Hold_Session, THE Browser_Worker SHALL close the browser tab, update the Hold_Record status to `released`, and decrement `current_load`.
3. THE Central_Server SHALL expose `POST /api/swarm/holds/{job_id}/purchase` which pushes a `purchase` command containing `card` details to `swarm:worker:{worker_id}:commands`.
4. WHEN a Browser_Worker receives a `purchase` command, THE Browser_Worker SHALL navigate the existing browser session to the epay/Datatrans payment page, fill the card fields (number via iframe, CVV via iframe, expiry dropdowns), and click PAY.
5. WHEN the purchase flow completes successfully, THE Browser_Worker SHALL update the Hold_Record status to `purchased` and push a result to the Result_Queue with `status: "purchased"`, `job_id`, `confirmation_url`, and `purchased_at`.
6. IF the purchase flow fails, THEN THE Browser_Worker SHALL update the Hold_Record status to `purchase_failed` and push a result to the Result_Queue with `status: "purchase_failed"`, `job_id`, and `error`.

---

### Requirement 8: Failure Handling and Recovery

**User Story:** As an operator, I want the system to handle browser crashes, network failures, and Vatican API errors gracefully so that holds are not silently lost.

#### Acceptance Criteria

1. WHEN a nodriver Chrome process crashes during an active Hold_Session, THE Browser_Worker SHALL detect the crash within 10 seconds, update the Hold_Record status to `crashed`, and re-enqueue the Hold_Job onto the Job_Queue with a `retry_count` incremented by 1.
2. WHEN a Hold_Job's `retry_count` reaches 3, THE Browser_Worker SHALL not re-enqueue it and SHALL push a result to the Result_Queue with `status: "abandoned"` and notify the admin via Telegram.
3. WHEN the Vatican Search_API returns a non-200 response during the Re_Recap_Loop, THE Re_Recap_Loop SHALL use the last known `ticket_id` stored in the Hold_Record as a fallback for that recap cycle only.
4. WHEN a Browser_Worker receives a SIGTERM signal (Docker stop), THE Browser_Worker SHALL enter draining mode: stop accepting new jobs, allow active Re_Recap_Loops to complete their current cycle, then gracefully shut down all browser instances within 60 seconds.
5. IF a Hold_Session's Re_Recap_Loop has not successfully recapped for more than 12 minutes (3 missed intervals), THEN THE Browser_Worker SHALL attempt to re-establish the hold by re-executing the full booking flow for the same slot using a fresh browser instance.
6. WHEN a re-establishment attempt succeeds, THE Browser_Worker SHALL update the Hold_Record with the new `jsessionid` and `recap_id` and resume the Re_Recap_Loop.

---

### Requirement 9: Docker Deployment Model

**User Story:** As an operator, I want a single `docker-compose.yml` that I can copy to any VPS and run with one command so that deploying a new swarm node requires no manual setup.

#### Acceptance Criteria

1. THE Browser_Worker image SHALL be defined in a `Dockerfile` at `browser_worker/Dockerfile` that installs Python 3.11, nodriver, Chromium (or Google Chrome), and all required Python dependencies from `browser_worker/requirements.txt`.
2. THE `docker-compose.yml` at `browser_worker/docker-compose.yml` SHALL define a single service `browser_worker` with the following configurable environment variables: `REDIS_URL`, `POSTGRES_DSN`, `WORKER_CAPACITY`, `TELEGRAM_BOT_TOKEN`, `ADMIN_TELEGRAM_IDS`, and `WORKER_VERSION`.
3. THE `docker-compose.yml` SHALL mount `/dev/shm` with a minimum size of 2 GB to prevent Chrome from running out of shared memory when running multiple instances.
4. THE `docker-compose.yml` SHALL set `restart: unless-stopped` so that the worker automatically recovers from crashes without operator intervention.
5. WHEN the `docker-compose.yml` is copied to a new VPS and `docker-compose up -d` is run, THE Browser_Worker SHALL connect to the Central_Server's Redis and Postgres within 30 seconds and appear as `idle` in `GET /api/swarm/workers/`.
6. THE `docker-compose.yml` SHALL NOT require any Vatican-specific credentials to be baked into the image; all secrets SHALL be passed via environment variables or a `.env` file mounted at runtime.
7. THE Browser_Worker Dockerfile SHALL support running Chrome in `--no-sandbox` mode required for containerised environments, and SHALL set `DISPLAY=:99` with a virtual framebuffer (Xvfb) so that headful Chrome can run without a physical display.

---

### Requirement 10: Observability and Admin Visibility

**User Story:** As an operator, I want a clear view of all active holds, worker health, and recent failures so that I can manage the swarm without SSH-ing into individual machines.

#### Acceptance Criteria

1. THE Central_Server SHALL expose `GET /api/swarm/holds/` returning all Hold_Records with `job_id`, `worker_id`, `date`, `slot_time`, `visitors`, `status`, `hold_started_at`, `last_keepalive_at`, `elapsed_minutes`, and `recap_count`.
2. WHEN a Hold_Session's `last_keepalive_at` is more than 8 minutes in the past, THE Central_Server SHALL flag that Hold_Record with `stale: true` in the API response.
3. THE Central_Server SHALL send a Telegram notification to the admin chat when any of the following events occur: a new hold is successfully acquired, a hold is released or purchased, a hold enters `recap_failed` or `crashed` status, or a worker goes `offline`.
4. THE Telegram notification for a new hold SHALL include: `job_id`, `date`, `slot_time`, `visitors`, `worker_id`, `total_price`, and a direct link to the epay URL.
5. THE Central_Server SHALL expose `GET /api/swarm/stats/` returning aggregate counts: `total_workers`, `online_workers`, `total_active_holds`, `holds_by_status` (dict), and `total_recaps_today`.

---

### Requirement 11: Mid-Flow Error Detection and Redirect Strategy

**User Story:** As an operator, I want the Browser_Worker to detect failures at each specific step of the Vatican booking flow and redirect to the correct recovery path so that transient errors are retried intelligently and permanent failures are escalated without wasting browser resources.

#### Acceptance Criteria

**Step-level failure detection:**

1. WHEN the Vatican deep link page loads but zero `[data-cy^='bookTicket_']` buttons are found after 15 seconds, THE Browser_Worker SHALL detect this as a `page_load_failure` and reload the page up to 2 times before marking the step as failed.

2. WHEN the Search_API returns HTTP 500 or an empty `visits` array during ticket ID resolution (step 2), THE Browser_Worker SHALL wait 10 seconds and retry the Search_API call up to 3 times; IF all retries fail, THE Browser_Worker SHALL re-enqueue the Hold_Job with `retry_count + 1` and close the browser tab.

3. WHEN the PRENOTA button for the target ticket cannot be found in the DOM after 10 seconds (step 3), THE Browser_Worker SHALL attempt a page reload and re-resolve the ticket ID; IF the button is still absent after reload, THE Browser_Worker SHALL mark the step as `ticket_not_found` and re-enqueue the job.

4. WHEN the quantity selector is not found after 10 seconds (step 4), THE Browser_Worker SHALL take a screenshot, log the current DOM state, and retry the PRENOTA click once; IF the selector is still absent, THE Browser_Worker SHALL mark the step as `quantity_selector_missing` and re-enqueue the job.

5. WHEN zero time slots (`[data-cy='time']`) are found after 20 seconds (step 5), THE Browser_Worker SHALL check whether the target `slot_time` is in the afternoon (≥ 14:00) and switch to the afternoon tab if not already on it; IF still no slots after tab switch, THE Browser_Worker SHALL mark the step as `slot_time_unavailable` — this means the slot was taken between job dispatch and execution — and push a result with `status: "slot_gone"` WITHOUT re-enqueueing (the slot no longer exists).

6. WHEN the PROCEDI button (`data-cy='bookVisit'`) is not found or is disabled after 10 seconds (step 6), THE Browser_Worker SHALL check for Angular form validation errors on the page; IF validation errors are present, THE Browser_Worker SHALL log the invalid field names and mark the step as `form_validation_error`; IF no validation errors, THE Browser_Worker SHALL retry the click once after a 2-second delay.

7. WHEN the checkout form (`data-cy='managerSurname'`) does not appear within 30 seconds after clicking PROCEDI (step 7), THE Browser_Worker SHALL check the current URL: IF the URL contains `error` or `errore`, THE Browser_Worker SHALL mark the step as `vatican_error_page` and re-enqueue the job; IF the URL is still on the ticket selection page, THE Browser_Worker SHALL retry PROCEDI once; IF the URL is on an unexpected page, THE Browser_Worker SHALL take a screenshot and mark the step as `unexpected_redirect`.

8. WHEN any required form field (`managerSurname`, `managerName`, `managerEmail`, `managerPhone`, `dateCalendar`) remains in Angular `ng-invalid` state after filling (step 8), THE Browser_Worker SHALL log the invalid fields, attempt to re-fill them once using `send_keys` instead of `evaluate`, and re-check validity; IF still invalid after re-fill, THE Browser_Worker SHALL mark the step as `form_fill_failed` and push a result with `status: "form_error"` and the list of invalid fields.

9. WHEN the BUY button (`data-cy='buyVisit'`) is not found or is disabled after 10 seconds (step 9), THE Browser_Worker SHALL check for Turnstile widget presence; IF Turnstile is present but unsolved after 30 seconds, THE Browser_Worker SHALL reload the checkout page and re-fill the form; IF Turnstile is absent and the button is still disabled, THE Browser_Worker SHALL log all `ng-invalid` fields and mark the step as `buy_button_disabled`.

10. WHEN the Vatican `/api/visit/reservation` call returns a non-200 response (captured via XHR intercept), THE Browser_Worker SHALL parse the error body: IF the error contains "scaduta" or "expired", THE Browser_Worker SHALL mark the step as `session_expired` and re-enqueue the job with `retry_count + 1`; IF the error contains "non dispone" or "not enough tickets", THE Browser_Worker SHALL mark the step as `slot_gone` and push `status: "slot_gone"` WITHOUT re-enqueueing; FOR all other errors, THE Browser_Worker SHALL mark the step as `reservation_error` and re-enqueue.

11. WHEN the epay redirect does not occur within 60 seconds after clicking BUY (step 10), THE Browser_Worker SHALL check the page for error messages in `[class*="error"]`, `[role="alert"]`, and `mat-snack-bar-container`; IF an error message is found, THE Browser_Worker SHALL log it and re-enqueue the job; IF no error message is found, THE Browser_Worker SHALL take a screenshot and mark the step as `epay_redirect_timeout`.

**Redirect routing table:**

12. THE Browser_Worker SHALL implement the following redirect routing for each failure type:

| Failure Type | Action |
|---|---|
| `page_load_failure` | Reload page, retry up to 2× |
| `ticket_not_found` | Reload + re-resolve ticket ID, retry 1× |
| `slot_gone` | Push `status: "slot_gone"`, do NOT re-enqueue, notify admin |
| `slot_time_unavailable` | Same as `slot_gone` |
| `quantity_selector_missing` | Retry PRENOTA click 1×, then re-enqueue |
| `form_validation_error` | Log invalid fields, re-enqueue with error details |
| `form_fill_failed` | Push `status: "form_error"`, notify admin, do NOT re-enqueue |
| `buy_button_disabled` | Reload checkout, re-fill form, retry 1× |
| `session_expired` | Re-enqueue with `retry_count + 1` |
| `reservation_error` | Re-enqueue with `retry_count + 1` |
| `epay_redirect_timeout` | Re-enqueue with `retry_count + 1` |
| `unexpected_redirect` | Screenshot + notify admin + re-enqueue |
| `vatican_error_page` | Re-enqueue with `retry_count + 1` |

13. WHEN any failure results in a re-enqueue, THE Browser_Worker SHALL include the `failure_type`, `failed_step`, `screenshot_base64` (if taken), and `error_detail` in the re-enqueued Hold_Job so that the next worker has context.

14. WHEN a Hold_Job's `retry_count` reaches 3 for any failure type, THE Browser_Worker SHALL NOT re-enqueue it; instead THE Browser_Worker SHALL push `status: "abandoned"` to the Result_Queue and send a Telegram notification to the admin containing the full failure history from the job's `failure_type` field.

15. WHEN a `slot_gone` result is pushed, THE Central_Server SHALL automatically dispatch a new timeavail check for the same date and visitor count and, if a different slot is available, push a new Hold_Job for that slot.
