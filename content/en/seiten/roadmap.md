title: Status & roadmap
summary: Where ai-gw stands in November 2026 – what is implemented, what is missing for the first release and which topics come after.
toc: ja
de: roadmap
---
## Status in November 2026 {#stand}

ai-gw has been public since November 2026. The planned feature set of the first version 0.1 is
**implemented and tested**: data plane with OpenAI and Anthropic input, all listed providers,
routing and resilience, tenants, limits and budgets, a plugin chain with guardrails, response
cache, MCP gateway, admin API and admin UI, GitOps, observability, SQLite and Postgres, container
image for amd64 and arm64. Since then, WASM plugins with signatures, tool inventory and tool
policies, further guardrails (`prompt-leak`, `link-guard`, `language`, invisible characters),
guardrail profiles, Microsoft Entra ID in many places and workload/agent identities have been
added, among others. The full
[changelog](https://github.com/mupf-dev/ai-gw/blob/main/CHANGELOG.md) is in the repository.

> **No release yet.** There is no published version and no ready-made container images yet; you
> build from source. Until 1.0, configuration, manifest format (`aigw/v1alpha1`) and admin API may
> change incompatibly between minor versions.

## Implemented {#umgesetzt}

| Area | Status |
|---|---|
| Endpoints | chat completions, messages, responses, embeddings, images, audio, models; streaming with backpressure |
| Providers | OpenAI, Azure OpenAI, Claude in Azure AI Foundry, Anthropic, AWS Bedrock, Gemini, Vertex AI, Mistral, Ollama, vLLM, OpenAI-compatible |
| Routing | model groups, four strategies, priorities, retries, fallbacks, circuit breakers, health checks |
| Access | organizations, teams, users, virtual keys, workload/agent identities (JWT, Entra Agent ID) |
| Limits and costs | request, token and concurrency limits, budgets, prices with suggestions, three counter backends |
| Guardrails | `pii`, `prompt-filter`, `prompt-leak`, `link-guard`, `language`, `content-safety`, profiles |
| Extensibility | plugin chain, webhooks, sandboxed WASM plugins with Ed25519 signatures |
| Tools and MCP | MCP gateway with grants, tool inventory, tool policies |
| Cache | exact (RAM, Redis) and semantic (HNSW, pgvector, Redis Search) |
| Operations | admin UI, admin API (OpenAPI), OIDC and roles, GitOps, audit log with hash chain, Prometheus, OpenTelemetry, Compose, Kubernetes |
| Performance | load measurements and a comparison with LiteLLM under equal conditions ([measurements](docs/performance.html)) |

## Until the first release {#release}

- Release 0.1.0 with ready-made container images for amd64 and arm64.
- Legal confirmation of the license of the embedded tokenizer tables (MIT); they can already be
  switched off.
- A security policy and a confidential reporting channel in the repository.

## Afterwards {#danach}

Topics marked as open or “later” in the concept documents – in no fixed order:

- **MCP server for administration**, generated from the OpenAPI specification, so that admin API,
  UI and MCP are on par.
- **MCP gateway:** sessions across multiple instances, resumption of SSE streams, OAuth to the
  upstream, grants at resource and prompt level, the plugin chain on tool arguments and results.
- **WASM plugins:** keyless signatures with a transparency log in addition to own keys, four-eyes
  approval, more host functions, asynchronous execution.
- **Performance:** a faster stream path (fewer small allocations per chunk), batched counter calls
  for Redis, the request-log writer on its own core.
- **Logs:** an optional backend for very large log volumes.
- **Embedding in platforms:** ai-gw is API-first, a single binary and declaratively configured so
  that platforms can embed it – for example [BYOC (Build Your Own Cloud)](https://mupf-dev.github.io/cloud-project-site/en/index.html),
  whose service catalog includes an AI gateway.

Wishes and priorities from practice are welcome: [Contribute](contribute.html).
