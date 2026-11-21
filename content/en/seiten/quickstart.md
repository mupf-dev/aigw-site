title: Quickstart
summary: Start ai-gw with Docker, open the admin UI, connect a provider and send the first request – plus Docker Compose with Postgres and Redis, Kubernetes and running without containers.
toc: ja
de: schnellstart
---
> **Pre-release.** Ready-made container images will be published with the first release. Until
> then the image is built from the repository (Docker with BuildKit). Until 1.0, configuration,
> manifest format and admin API may change incompatibly – the
> [changelog](https://github.com/mupf-dev/ai-gw/blob/main/CHANGELOG.md) lists such changes.

## 1. Build and start the image {#starten}

```sh
git clone https://github.com/mupf-dev/ai-gw.git && cd ai-gw
docker build -t ai-gw:dev .                              # build the image (BuildKit)
docker run --rm ai-gw:dev keygen > aigw-master-key       # generate a master key
docker volume create aigw-data
docker run -d --name aigw --read-only --cap-drop ALL --security-opt no-new-privileges \
  -p 127.0.0.1:4000:4000 -p 127.0.0.1:4001:4001 \
  -e AIGW_MASTER_KEY="$(cat aigw-master-key)" \
  -e AIGW_SECRET_OPENAI_API_KEY="sk-…" \
  -v aigw-data:/data ai-gw:dev
docker logs aigw 2>&1 | grep Bootstrap-Token             # one-time admin token
```

The image is distroless, runs as non-root with a read-only file system and includes a health
check; it can be built for amd64 and arm64. The master key encrypts all stored credentials – keep
it separate from database backups. A file mounted as a Docker or Kubernetes secret is better than
the environment variable (`AIGW_SECRETS__MASTER_KEY_FILE`).

Port 4000 is the **data plane** for applications, port 4001 the **control plane** with admin UI,
admin API and metrics. Both are bound to `127.0.0.1` here.

## 2. Open the admin UI {#admin-ui}

Open `http://localhost:4001/admin/` with the bootstrap token. The token expires automatically as
soon as a global admin has signed in via OIDC or an admin API key with role `admin` exists. In the
UI, create in turn:

1. an **organization** (and teams if needed),
2. **credentials** for a provider – in the example a reference to the environment variable
   `AIGW_SECRET_OPENAI_API_KEY`, never the plaintext in a manifest,
3. a **model group** with a **deployment**,
4. an **API key** for the application.

## 3. Or everything as YAML {#yaml}

The same resources can be applied as manifests – in the UI under “YAML import/export”, via the
admin API or with `aigw config apply`. The example `config/examples/minimal/resources.yaml` from the
repository:

```yaml
apiVersion: aigw/v1alpha1
kind: Organization
metadata: {name: default}
spec:
  displayName: Standard
---
apiVersion: aigw/v1alpha1
kind: ProviderCredential
metadata: {name: openai}
spec:
  provider: openai
  data:
    apiKey:
      valueFrom: {env: AIGW_SECRET_OPENAI_API_KEY}
---
apiVersion: aigw/v1alpha1
kind: ModelGroup
metadata: {name: gpt-4o-mini}
spec: {}
---
apiVersion: aigw/v1alpha1
kind: Deployment
metadata: {name: gpt-4o-mini-openai}
spec:
  modelGroup: gpt-4o-mini
  provider: openai
  providerModel: gpt-4o-mini
  credential: openai
```

```sh
curl -s localhost:4001/admin/api/v1/config:apply -H "authorization: Bearer <bootstrap-token>" \
  -H 'content-type: application/yaml' --data-binary @config/examples/minimal/resources.yaml
```

More examples in the repository under `config/examples/`: providers, teams and budgets,
guardrails, cache, MCP, GitOps and a setup with Postgres and Redis.

## 4. First request {#request}

Create an API key in the UI (the plaintext is shown only once) and use it with any
OpenAI-compatible client:

```sh
curl -s localhost:4000/v1/chat/completions -H "authorization: Bearer sk-aigw-…" \
  -H 'content-type: application/json' \
  -d '{"model":"gpt-4o-mini","messages":[{"role":"user","content":"Hello"}]}'
```

In SDKs it is enough to set the base URL to `http://localhost:4000/v1` and the key to the virtual
key. Anthropic clients use `POST /v1/messages` with the key in the `x-api-key` header. The request
shows up in the log explorer right away – with tokens, cost and latency.

## Docker Compose with Postgres and Redis {#compose}

For multiple instances or higher load, `deploy/compose/` contains a setup with Postgres 17,
Redis 7 and optionally an OpenTelemetry collector:

```sh
cd deploy/compose
cp env.example .env && $EDITOR .env                      # set POSTGRES_PASSWORD
mkdir -p secrets
docker run --rm ai-gw:dev keygen > secrets/aigw-master-key
sudo chown 65532:65532 secrets/aigw-master-key && sudo chmod 0400 secrets/aigw-master-key
docker compose up -d
docker compose ps                                        # aigw: healthy
```

## Kubernetes {#kubernetes}

`deploy/kubernetes/` contains a kustomize baseline: a ConfigMap with the startup configuration, a
Deployment with two replicas (non-root, read-only file system), services for data and control
plane, probes on `/healthz` and `/readyz` and a PodDisruptionBudget. Mount the master key as a
secret and expose the control plane internally only.

## Without containers {#binary}

ai-gw is a single binary. It is built with the Rust toolchain pinned in the repository (build the
admin UI with pnpm first); after that `aigw keygen`, `aigw config check` and `aigw serve` are all
you need, ideally as a systemd service with a generous file-descriptor limit.

## Next steps {#weiter}

- Set up **sign-in via OIDC** (Microsoft Entra ID, Keycloak or another IdP) and bind roles to IdP
  groups.
- Apply the **“basic” guardrail profile** globally or per team: [Guardrails & security](security.html).
- Set **limits and budgets** per team and review prices.
- Connect **monitoring** via `/metrics` and OpenTelemetry.
- **Harden** the setup following [Operations and hardening](docs/operations.html).
