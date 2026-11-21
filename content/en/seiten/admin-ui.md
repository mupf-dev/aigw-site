title: The admin UI
summary: Screenshots of the ai-gw admin UI – overview, model groups and routing, keys, log explorer, guardrail profiles, YAML import, audit log and command palette.
wide: ja
de: oberflaeche
---
::: html
<p class="shot-intro">The admin UI is a Svelte 5 application embedded in the binary and served by the control plane (default port 4001, path <code>/admin/</code>). It uses only the public admin API – everything shown here also works via the API or as YAML. The screenshots come from the real UI; organizations, teams, keys and figures are fictitious sample or test data.</p>
:::

> **Pre-release – the UI may change.** The screenshots show the state of development in November 2026. The UI is currently in German.

## Overview {#uebersicht}

Requests, tokens, cost, p95 latency, error rate and cache hits for the selected period, with a time series, top model groups, provider traffic share and health, and the latest errors.

::: html
<figure class="shot">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="../assets/img/ui/uebersicht-dunkel.webp" width="1200" height="1307">
    <img src="../assets/img/ui/uebersicht-hell.webp" width="1200" height="1307" loading="lazy" decoding="async" alt="Overview of the fictitious organization Acme GmbH with 24-hour key figures, a request time series, a table of top model groups with requests, tokens, cost and p95 latency, traffic shares of Azure OpenAI, OpenAI, Anthropic, vLLM, AWS Bedrock, Mistral and Vertex AI, and a list of recent errors.">
  </picture>
  <figcaption>Overview – follows the system light/dark setting, just like this site.</figcaption>
</figure>
:::

## Model groups and routing {#routing}

A model group is the public model name for clients. Behind it are deployments with priority, weight and capacity; fallback chain, retries and circuit breaker are configurable per group.

::: html
<div class="shot-grid">
<figure class="shot">
  <img src="../assets/img/ui/modellgruppe-dunkel.webp" width="1200" height="750" loading="lazy" decoding="async" alt="Detail page of the model group gpt-4o in dark mode: weighted strategy, fallback chain to claude-sonnet on rate limit or unavailability, retry and circuit breaker settings, two deployments – Azure OpenAI with priority 0 and OpenAI with priority 1.">
  <figcaption>Model group with two deployments: reserved capacity first, fallback to another model.</figcaption>
</figure>
<figure class="shot">
  <img src="../assets/img/ui/routing-hell.webp" width="1200" height="750" loading="lazy" decoding="async" alt="Edit model group dialog with routing strategy, aliases, capabilities chat, embeddings, images, transcription and speech, fallback chain and a form for retries with attempts, backoff and time budget.">
  <figcaption>Routing settings as a form or JSON – validated by the same parser as the data plane.</figcaption>
</figure>
</div>
:::

## Keys {#keys}

Virtual API keys for applications, with team, allowed models, budget, rate limits, expiry and status. The plaintext is shown only once, on creation.

::: html
<figure class="shot">
  <img src="../assets/img/ui/keys-hell.webp" width="1200" height="1268" loading="lazy" decoding="async" alt="List of 14 virtual keys of the fictitious Acme GmbH, such as ci-evals, contract-review and support-bot-prod, each with team, allowed models, monthly budget, RPM and TPM limits, expiry date, last use and status active, expired or revoked.">
  <figcaption>Keys with budgets and limits per application.</figcaption>
</figure>
:::

## Log explorer {#logs}

Every request through the gateway – with model, provider, key, tokens, cost, latency, cache hits and fallback attempts. Content is stored only if configured, and then masked.

::: html
<figure class="shot">
  <img src="../assets/img/ui/logs-hell.webp" width="1200" height="750" loading="lazy" decoding="async" alt="Log explorer in live view: key figures for requests, error rate, p95 latency and cost, with a table of time, status, model and provider, key, tokens, cost, latency and cache status per request.">
  <figcaption>Log explorer with filters for status, model and cache.</figcaption>
</figure>
:::

## Guardrail profiles {#guardrails}

Profiles bundle recommended guardrail settings. Before applying one to an organization, team, key or model group, the UI shows which plugin bindings will be created or changed.

::: html
<figure class="shot">
  <img src="../assets/img/ui/guardrail-profil-hell.webp" width="1200" height="750" loading="lazy" decoding="async" alt="Apply basic profile dialog at team level: the diff shows two new plugin bindings, prompt-filter and pii; in the background the descriptions of the basic, strict and open profiles.">
  <figcaption>Applying the “basic” profile to a team – diff first, then apply.</figcaption>
</figure>
:::

## YAML import and audit {#gitops}

Configuration can be exported as YAML manifests and applied again – first as a dry run with a diff, then in one transaction. Every change lands in the audit log, whose hash chain can be verified in the UI.

::: html
<div class="shot-grid">
<figure class="shot">
  <img src="../assets/img/ui/gitops-hell.webp" width="1200" height="750" loading="lazy" decoding="async" alt="YAML import with manifests for a model group gpt-4o and a team legal; the dry run reports one creation and one change and shows the diff of the aliases and the routing strategy.">
  <figcaption>Dry run with a diff before applying.</figcaption>
</figure>
<figure class="shot">
  <img src="../assets/img/ui/audit-hell.webp" width="1200" height="750" loading="lazy" decoding="async" alt="Audit log with the message that the audit chain is intact with 50 entries verified, filters for object type, action, actor and period, and entries for creating, suspending, unsuspending and revoking API keys.">
  <figcaption>Audit log with verified hash chain (test data).</figcaption>
</figure>
</div>
:::

## Command palette {#befehlspalette}

Ctrl+K jumps to pages, actions, models or keys – without leaving the keyboard.

::: html
<figure class="shot">
  <img src="../assets/img/ui/befehlspalette-hell.webp" width="1200" height="750" loading="lazy" decoding="async" alt="Open command palette above the overview with a search field for pages, actions, models or keys and a list of pages from overview to logs.">
  <figcaption>Command palette (Ctrl+K).</figcaption>
</figure>
:::
