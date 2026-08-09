# Deployment notes — decisions, alternatives, lessons

Working log from taking this MCP server from "runs on my laptop over stdio" to
"deployed on Cloud Run with keyless CI/CD". Kept as interview prep and blog
material. Each entry: what we chose, what we rejected, why.

## Platform & cost model

- **Cloud Run over a VM/VPS.** A VPS bills per month for a machine that mostly
  idles; Cloud Run bills per request (CPU is only allocated while serving).
  With `min_instance_count = 0` the idle cost is zero; the price is a cold
  start (~2-4s) on the first request after idle. For a personal MCP server the
  trade is obviously right. `max_instance_count = 1` doubles as a hard cost cap.
- **Free trial ≠ free tier.** The $300 trial is one-off credits; the always-free
  tier is monthly and permanent (2M Cloud Run requests, 0.5 GB Artifact
  Registry, 6 secret versions). This project fits inside the free tier, so an
  expired trial cost us nothing.
- **Budget alerts notify, they don't cap.** €5 budget with 50/90/100% email
  thresholds on the billing account. A true hard-stop requires wiring budget →
  Pub/Sub → function that unlinks billing; deliberately skipped as overkill.
- **Region: `europe-west1` for everything.** Cheapest EU tier-1 region; keeping
  registry and service co-located makes image pulls fast (cold starts) and free
  (no cross-region egress). GCS free tier is US-only — the state bucket costs
  actual money: fractions of a cent.

## Terraform

- **Terraform over a pile of gcloud commands.** Declarative + state means
  idempotency (second `apply` is a no-op), drift detection (refresh), implicit
  parallelism, and a reviewable diff (`plan`) before any change.
- **Remote state on GCS, versioned.** Local state is a single point of failure,
  breaks concurrent work (no locking), and leaks sensitive values onto laptops.
  Bucket versioning is the undo button for corrupted state.
- **Two chicken-and-egg bootstraps, both deliberate:** the state bucket is
  created imperatively (Terraform needs a state home before it can manage
  anything), and the backend block cannot use variables (it's read before
  variables are evaluated) — hence partial backend config: bucket name lives in
  a gitignored `backend.hcl`, mirroring the `terraform.tfvars(.example)`
  pattern so no project IDs are committed.
- **APIs enabled as code** (`google_project_service` with `for_each`), with
  `disable_on_destroy = false` — disabling an API can cascade-delete resources;
  destroy should forget, not break.
- **`plan -out` + `apply <file>`** as the standard ritual: the applied plan is
  exactly the reviewed plan (also the only way in non-interactive contexts —
  `apply` prompting for "yes" dies with EOF without a TTY).

## Container & transport

- **The server spoke stdio; Cloud Run speaks HTTP.** MCP's remote transport is
  streamable HTTP (SSE transport is deprecated). Change kept minimal and
  backward-compatible: `MCP_TRANSPORT=http` env switch in `main()`, binding
  `0.0.0.0:$PORT` per the Cloud Run contract (the *platform* injects PORT —
  neither the Dockerfile nor Terraform decides it). Default stays stdio so
  local Claude Desktop usage is untouched; the Docker image bakes
  `MCP_TRANSPORT=http` since images are for the cloud.
- **Multi-stage uv Dockerfile.** Lockfile-first layer ordering for cache hits;
  `UV_COMPILE_BYTECODE=1` and a slim runtime stage because on scale-to-zero
  *every* start is a first start — build-time work is repaid on every cold
  start. Non-root `USER` as standard hygiene. 221 MB local, ~79 MB compressed.
- **Apple Silicon gotcha:** local builds are arm64, Cloud Run is amd64. Local
  pushes need `--platform linux/amd64` (the push itself would succeed and the
  failure would only appear at deploy). CI runners are amd64, so the problem
  disappears in the pipeline.

## Secrets

- **Terraform manages secret *envelopes*, never values.** A
  `google_secret_manager_secret_version` in Terraform lands the plaintext in
  the state file. Values are added out-of-band: `read -s` + stdin pipe to
  `gcloud secrets versions add` — never in git, state, shell history, or
  process args.
- **Env vars over volume mounts** for delivering secrets to the container:
  zero code change (the client already reads the environment). Mounted files
  win when you need hot rotation or very large payloads; not our case.
- **`user_managed` replication pinned to `europe-west1`** instead of `auto`:
  Greek tax credentials stay in the EU, and pricing (per version *per
  location*) stays predictable — 2 version-locations, free tier is 6.

## IAM

- **Dedicated runtime service account.** The default compute SA is
  project-Editor — an RCE in the app would inherit the whole project. Ours can
  read exactly two secrets, nothing else. Logs need no grant (stdout/stderr is
  captured by the platform); image pulls are done by Cloud Run's own service
  agent, not the runtime SA.
- **Resource-level bindings over project-level**, `_member` over `_binding` /
  `_policy` (additive, doesn't silently evict other grantees).
- **`iam.serviceAccountUser` is the subtle one:** CI deploys a service that
  *runs as* the runtime SA, so CI needs "act as" on that SA. Without this
  model, anyone with deploy rights could escalate by attaching a powerful SA.

## CI/CD & Workload Identity Federation

- **WIF over service-account JSON keys.** A JSON key is a forever-password;
  WIF inverts the trust: GCP verifies GitHub's signed OIDC tokens
  cryptographically (issuer public keys), exchanges them via STS for
  minutes-lived credentials. Nothing stored on either side. Token flow:
  workflow → GitHub OIDC token → STS (checks `attribute_condition`) →
  federated token → iamcredentials mints CI SA token → push + deploy.
- **Repo restriction enforced twice** (provider `attribute_condition` and the
  `principalSet` on the SA binding) — defense in depth; a fork's token fails
  both checks independently.
- **`permissions: id-token: write`** in the workflow is the line that enables
  OIDC issuance — its absence is the classic WIF failure mode. Scoped to the
  deploy job only.
- **GitHub Variables (not Secrets) for project ID / provider / SA email:**
  they're addresses, not credentials — worthless without the WIF trust. Kept
  out of git for the same hygiene as tfvars.
- **Deploy `:sha`, also tag `:latest`.** Immutable identity for audit/rollback;
  `latest` is a human convenience pointer, never deployed directly.
- **Image ownership split:** Terraform ignores `template.containers.image`
  (`lifecycle.ignore_changes`) so CI deploys don't show as drift and Terraform
  can't "correct" the service back to an old tag. Terraform owns config, CI
  owns the running image. Alternative (CI runs `terraform apply`) rejected as
  heavier for no benefit at this scale.

## Access control

- **IAM-authenticated, not public.** The server has no auth of its own and
  fronts tax data; a public URL would hand the tools to anyone. Anonymous
  requests die at Google's front end (403) before touching (or billing) the
  container. The cost: MCP clients must send an identity token. Public would
  be one `run.invoker` binding for `allUsers` away, if it ever made sense.

## Audit logging (BigQuery)

- **Streaming REST insert over the official client library.** The
  `google-cloud-bigquery` package drags a large dependency tree into the
  image (cold-start cost); the streaming `insertAll` endpoint is one httpx
  POST, and httpx was already a dependency. Tokens come from the Cloud Run
  metadata server — the same mechanism ADC uses under the hood — so the
  feature needs zero new dependencies and zero stored credentials.
- **Fire-and-forget by design:** 3s timeout, all exceptions swallowed. An
  audit outage must never break or visibly slow a tool call.
- **Metadata only** (tool, status, duration, result count, error type) —
  never AADE payload contents. Day-partitioned on `ts`.
- **Toggle by presence:** the hook is active only when `AUDIT_TABLE`
  (`project.dataset.table`) is set — Terraform sets it on Cloud Run; locally
  it is absent and every call is a no-op.
- **Table-level IAM:** the runtime SA gets `dataEditor` on the single events
  table — even finer than the per-secret grants.

## Not done (deliberately)

- Custom domain, Cloud Armor, multi-env (staging/prod). For a second
  environment: same code, new tfvars + backend prefix — that's the payoff of
  keeping personal values out of the module.
