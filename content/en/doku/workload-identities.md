title: Workload and agent identities
summary: AI agents and services sign in with signed access tokens – primarily from Microsoft Entra Agent ID – instead of a distributed gateway key. The token acts exactly like the key to which the identity is mapped.
group: konzept
order: 40
quelle: Concept 18 “Workload and agent identities”
de: workload-identitaeten
---
Virtual API keys are simple, but they have to be distributed, stored securely and rotated. For
AI agents and services with their own identity this is unnecessary: they can obtain a short-lived access token
from their identity provider. ai-gw accepts such **signed tokens
(JWT)** on the data plane – OpenAI and Anthropic entry points, embeddings, images, audio,
model list – and in the MCP gateway as `Authorization: Bearer …`.

The main case is **Microsoft Entra Agent ID**: AI agents with their own Entra identity sign in
without a gateway key. The same mechanism works in general for workload identities such as service
principals, managed identities or other OAuth 2.0 issuers.

```text
Agent ──Client Credentials / On-Behalf-Of──► Entra ID: token for the gateway API
  └─ Authorization: Bearer eyJ… ─► ai-gw
        1. Check signature, issuer, audience, lifetime, tenant, and if set role/scope
        2. (issuer, identifier) → mapped API key
        3. from here on as with the key: grants, limits, budgets, guardrails, tools, MCP
  Provider: only the deployment's credentials – never the token
```

## Issuer configuration {#aussteller}

Trusted issuers are defined in the operator's startup configuration, not in the
admin API:

```yaml
auth:
  jwt:
    issuers:
      - name: entra-prod
        profile: entra                         # generic | entra
        tenant_id: "<tenant-guid>"
        audiences: ["api://ai-gw", "<client-id-of-the-gateway>"]
        required_roles: [Gateway.Invoke]       # optional
        # required_scopes: [access_as_user]    # optional, for delegated tokens
        # require_agent: true                  # agent identities only
```

The `entra` profile derives the issuer (token versions 1 and 2) and the key source from the
tenant ID. Generic issuers specify their key source explicitly or via
OpenID discovery.

## Mapping to keys {#zuordnung}

Instead of a new resource kind, ai-gw extends the **virtual key**: a key carries a list
of identities made up of issuer and identifier (by default the app ID of the agent identity). A
token with a matching combination acts **exactly like this key** – model grants, limits,
budgets, team and organisation, guardrail bindings, tool policies, MCP grants,
payload policy and attribution in the request log apply without special logic.

- Each identity belongs to at most **one** active key; the admin API and GitOps check this.
- Unknown identities are rejected (`403`) – there is **no automatic provisioning**. The
  Microsoft documentation explicitly advises against authorising solely on the basis of an agent claim.
- A key can carry several identities, such as all instances of an agent; they then share
  limits and budgets.
- Blocked or expired keys also block token sign-in; when a key is rotated,
  the identities move along with it.

## Validation {#pruefung}

- A bearer value in JWT format is treated as a token, anything else as an API key; virtual
  keys never contain dots.
- Size limit before any evaluation; only **RS256 and ES256**. `none`, symmetric algorithms and
  critical header extensions are never accepted, and keys are never fetched based on token contents –
  only from the configured source.
- Signature verification with aws-lc-rs, no home-grown cryptography. Issuer exact, audience from the
  list, expiry mandatory, clock skew configurable, and for Entra additionally the tenant.
- Key sets are loaded via the shared component for outbound connections (HTTPS
  only, no redirects, size and time limits), cached, and reloaded with throttling when an unknown
  key ID appears. If the issuer is unreachable, the known
  keys remain in use.
- Validated tokens are kept in a bounded cache until they expire; the mapping to the key
  is nevertheless evaluated on every request against the current configuration snapshot.

The admin UI's OIDC login uses the same validation components.

## Traceability {#attribution}

The request log records who made the request: issuer, identifier, kind (application, delegated,
agent user account), whether it is an agent identity, and for delegated tokens the user and the
agent's blueprint – never the token itself. Only admins and auditors see the user identifier.
Traces and OpenTelemetry logs carry issuer, identifier and kind. There are deliberately no per-agent metric labels,
because the number of identities is unbounded.

## Security and limits {#grenzen}

- **Tokens never go to providers:** Outbound requests are built from the credentials of the
  deployment or MCP server; incoming headers are not passed through.
- **Revocation:** Tokens are valid until they expire; ai-gw does not query the issuer for
  revocation. Removing the identity from the key or blocking the key takes effect immediately.
- **Tenant-wide tokens:** Without a role or scope requirement, any application in the tenant can obtain a
  token for the gateway API – but only registered identities are mapped.
  Recommendation: define an app role (e.g. `Gateway.Invoke`), enforce assignment and
  set `required_roles`.
- Error responses reveal no details (`401` or `403`); reasons are recorded without the token in the
  debug log.

In the admin UI, identities are managed on the key; only configured
issuers are offered. See also [MCP gateway](mcp-gateway.html) and
[Guardrails & security](../security.html).
