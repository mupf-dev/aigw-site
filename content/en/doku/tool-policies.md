title: Tool inventory and tool policies
summary: ai-gw records every tool that applications send along in model requests, detects changed or suspicious descriptions and enforces policies – from removing individual tools to approval on a case-by-case basis.
group: konzept
order: 20
quelle: Concept 16 “Tool inventory and tool policies”
de: tool-richtlinien
---
With every model request, applications send along the tools the model may call –
coding assistants, for example, all the tools of their MCP servers as `mcp__<server>__<tool>`. The gateway
does not run these tools, but it sees them in full. ai-gw makes use of exactly that:

- **Inventory:** every tool with name, kind, presumed origin, client, organisation, team and
  key, first and last sighting, number of requests and of calls by the model.
- **Changes and suspicion:** changed descriptions or schemas of known tools (“rug pull”)
  and descriptions with prompt-injection signals are flagged, audited and reported.
- **Policies:** allow, remove, reject, observe or “only after approval” – also
  for tool calls in the response.

## Place in the pipeline {#pipeline}

```text
Sign-in ─► Body ─► Model grant ─► [Tool policies + inventory] ─► Limits/budgets
        ─► Guardrails ─► Cache ─► Routing
        ─► [Tool-call filter] ─► Output guardrails ─► Client
```

- **Before limits and guardrails:** removed tools do not count towards the token estimate, guardrails and
  webhooks only see the tools that remain allowed, and a rejection does not consume quota.
- **Tool-call filter as the innermost response layer:** output guardrails already see filtered
  responses; cache hits also pass through the filter.
- Applies to Chat Completions, Messages, Responses and the playground. Without tools in the request,
  the step is skipped entirely.

## Inventory {#inventar}

| Attribute | Source |
|---|---|
| Name | Name of the function or the provider tool |
| Kind | Function with JSON schema, versioned server tool of a provider, or built-in tool |
| Origin | MCP server from the name pattern (`mcp__<server>__<tool>` or `<server>__<tool>`), otherwise “client” |
| Client | Configurable header (e.g. `x-aigw-client`), otherwise `User-Agent` |
| Assignment | Organisation, team, key and name – one entry per application |

For description and schema, ai-gw stores one hash each; the schema is hashed as a JSON tree,
independent of whitespace and key order. The **contents** are only
stored if the key's payload policy allows it – complete or masked. The description is always
checked, in memory.

On the hot path the inventory costs little: known definitions are recognised by a fast
fingerprint keyed randomly per process; only new or changed definitions
are copied. A background task writes the inventory to the database in batches – never in the
request path. Multiple instances write additively to the same entries.

## Changed and suspicious tools {#aenderungen}

- **Changed:** If a hash deviates from the stored state, the entry is flagged, the
  history is extended, an audit entry is written and the `tool.changed` event is sent to the
  event webhooks. If desired, ai-gw automatically blocks the tool for that key until
  someone confirms the change.
- **Suspicious:** The prompt-injection signals of the `prompt-filter` run over every new or
  changed description. Hits are stored with the signal names, audited and reported as
  `tool.suspicious`; blocking is not automatic.

## Policies {#richtlinien}

```yaml
apiVersion: aigw/v1alpha1
kind: ToolPolicy
metadata: {name: block-destructive}
spec:
  scope: {level: global}               # global | organization | team | api-key | model-group
  tools: ["*delete*", "!delete_draft"] # glob pattern, !exclusion; empty = all
  servers: [github]                    # origin; empty = any
  action: block-strip                  # allow | block-strip | block-reject | observe | require-approval
  locked: true                         # also applies against more specific allow rules
  description: Never give destructive tools to models
```

A pattern matches the full name or the name without the server prefix. The decision is made per
tool in the context of the request:

1. A matching **locked** block always wins, regardless of level.
2. Otherwise the matching `allow` or `block-*` policy of the **most specific level** applies
   (key before model group before team before organisation before global); at the same level, the stricter one.
3. Without such a policy, a matching `require-approval` policy applies: the tool is not
   approved until an `allow` policy covers it.
4. Otherwise the tool is allowed. `observe` changes nothing, but logs and counts.

| Effect | Request | Response |
|---|---|---|
| allow | unchanged | – |
| remove (`block-strip`) | Tool removed from the request; a `tool_choice` forced on it becomes `auto` | Calls to this tool suppressed |
| reject (`block-reject`) | `403` with code `tool_blocked` in the format of the entry point | – |

If a model nevertheless calls a tool that is not allowed – hallucinated, from the history or as a
built-in provider tool –, ai-gw treats it like an output rejection by the guardrails:
`finish_reason: content_filter` or `stop_reason: refusal` and header
`x-aigw-guardrail: tool-policy`. In a stream, no further content is passed on from that call;
text already sent remains, and the usage is billed.

## Approving and blocking from the inventory {#freigabe}

In the admin UI and admin API, each inventory entry shows its status: new, approved, blocked
or pending. “Approve” and “Block” write ordinary `ToolPolicy` resources per level – with
audit, immediate effect via the snapshot and export via GitOps. The permissions follow those of the
plugin bindings: team admins decide within their own team, global levels remain reserved for global
admins; restricted roles see the inventory only in their own scope.

## Measurements {#messwerte}

Measured with 30 tools per request (description around 600 characters, schema with eight fields), one
core:

| Case | µs per request |
|---|---|
| without tools | 0.02 |
| 30 tools, without inventory and policies | 2.6 |
| 30 tools, 6 policies | 7.9 |
| 30 tools, inventory (known definitions) | 13.2 |
| 30 tools, inventory and 6 policies | 18.0 |

For comparison: merely decoding such a body of around 40 KB costs many times as much.

## Limits {#grenzen}

- Tool results in the request and calls through the [MCP gateway](mcp-gateway.html) are not checked by
  this component – guardrails and MCP grants are responsible for those.
- Multiple clients with the same key share one inventory entry.
- Automatic blocking takes effect from the next snapshot; requests within the same write interval
  still pass through.
