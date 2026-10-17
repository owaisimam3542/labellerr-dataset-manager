# Future Improvements

## 1. Typed SDK adapter and provider abstraction (architecture)
**Current limitation:** The SDK's storage-connection API can vary between releases, and this implementation checks a small set of operation names. Provider-specific options are represented by a common CLI shape.

**Proposal:** Pin a verified SDK version, define a typed `StorageProvider` protocol, and implement separate S3/GCS adapters with provider-specific schemas. Add contract tests against the supported SDK version.

**Benefit:** Explicit interfaces make SDK changes easier to detect, improve type checking, and isolate provider-specific behavior.

**Trade-offs:** More files and maintenance effort; contract tests need careful version management. GCS should only be enabled after its real SDK flow and credentials are verified.

## 2. Retry policy and API observability (production readiness)
**Current limitation:** Transient network errors are reported but not retried, and the CLI does not measure API latency or classify rate limits.

**Proposal:** Add bounded retries with exponential backoff and jitter for safe transient failures (timeouts, 429, selected 5xx responses), respect `Retry-After`, and log request duration plus a correlation ID.

**Benefit:** More resilient operations and better diagnostics without exposing credentials.

**Trade-offs:** Retries increase latency and can duplicate mutations if the remote API is not idempotent. Do not retry create/delete operations unless idempotency semantics are known.

## 3. Pagination and filtering
**Current limitation:** Listing currently consumes the SDK's returned collection as a whole.

**Proposal:** Support cursor/page-based pagination, provider/status filters, and a configurable page size; preserve a JSON output mode for automation.

**Benefit:** Better performance and usability for accounts with many connections.

**Trade-offs:** Pagination depends on the SDK/API exposing stable cursors and may require additional calls.

## 4. Stronger credential management
**Current limitation:** Environment variables and a local `.env` file are suitable for development but can be mishandled on shared machines.

**Proposal:** Use a managed secret store in production, rotate credentials regularly, restrict `.env` file permissions, and scan commits for secrets in CI.

**Benefit:** Reduces accidental disclosure and improves operational security.

**Trade-offs:** Secret managers add cost, access-policy configuration, and deployment complexity.

## 5. Destructive-operation safeguards and idempotency
**Current limitation:** Deletion requires confirmation, but there is no dry-run mode or duplicate detection for create operations.

**Proposal:** Add `--dry-run`, optional exact-name duplicate checks, and server-supported idempotency keys if available.

**Benefit:** Reduces accidental deletion and duplicate resources in automation.

**Trade-offs:** Duplicate checks can race under concurrent requests; dry-run output must clearly state that remote state may change before execution.
