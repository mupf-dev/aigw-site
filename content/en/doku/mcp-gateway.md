title: MCP gateway
summary: ai-gw as an MCP server for clients and as an MCP client to connected servers – with grants per team and key down to the tool level, credentials, limits, logging and SSRF protection.
group: konzept
order: 10
quelle: Concept 15 “MCP gateway”
de: mcp-gateway
---
The Model Context Protocol (MCP) connects AI applications with tools and data sources.
In organisations, MCP servers quickly proliferate, with their credentials stored separately in every
IDE and every agent. ai-gw consolidates them: clients talk to one
endpoint and see exactly the tools, prompts and resources granted to their key, and the
gateway sets the upstream credentials, applies limits and logs every
tool call.

## Roles {#rollen}

- **MCP server** for clients (agents, IDEs) over **Streamable HTTP** at `/mcp` (all
  granted servers merged) and `/mcp/{server}` (a single server).
- **MCP client** to the connected upstream servers over Streamable HTTP, the older HTTP+SSE,
  or **stdio** (as a managed process, only after explicit enablement).

The implementation is in-house: JSON-RPC 2.0 and the transports are implemented in the gateway
itself. The gateway needs both sides at once, with its own session, permission and
pool logic, and passes messages through largely unchanged – unknown fields are
preserved. For outbound connections it uses the same HTTP stack with SSRF checks as for the
model providers.

## Namespace {#namensraum}

Under `/mcp`, the tools and prompts of all granted servers are merged and prefixed
with the server name (`<server>__<tool>`), so that identically named tools from different servers do
not shadow each other. Resources keep their URI; the gateway remembers per session which server
supplied them. Lists from the upstream servers are cached for a few minutes; an
unreachable server is missing from the merged result instead of blocking the whole list.

## Grants {#freigaben}

```yaml
apiVersion: aigw/v1alpha1
kind: McpGrant
metadata: {name: platform-github}
spec:
  server: github
  subject: {level: team, target: platform}     # team | api-key
  tools: ["get_*", "search_*", "!get_secret*"]  # empty = all
```

- **Default: nothing.** Without a matching grant, a key sees no server.
- `tools` are glob patterns on the tool name at the upstream; `!pattern` excludes. An empty
  list or exclusions only mean “all remaining tools”.
- **The team is the upper bound** – as with model grants: if a key belongs to a team,
  a team grant for the server is required; key grants narrow it further.
- The gateway rejects calls to tools that are not granted, even if a client guesses the name.

## Upstream servers {#upstream}

An `McpServer` describes transport, address and credentials. Secrets (bearer tokens,
header values) are stored encrypted in the database, like those of the model providers, or are given as
a reference to the environment or a file; when saving, the gateway checks that the reference can
be resolved. For stdio servers, ai-gw starts and monitors the process itself – this is
blocked by default and must be enabled in the startup configuration.

## SSRF protection {#ssrf}

Upstream addresses are checked when saving and on every connection attempt, after name
resolution. Private, loopback and link-local ranges are blocked unless they are explicitly
and narrowly allowed; the gateway does not follow redirects. This way an
MCP server entry cannot serve as a stepping stone into the internal network.

## Limits, log and metrics {#beobachtung}

- Every tool call (and every list request) counts as a request in the limits of key, team and
  organisation; hard budget limits also block tool calls. In addition there are upper bounds for
  MCP sessions per key and team, timeouts and a maximum message size.
- Every tool call appears in the request log with server, tool, status, duration and key; arguments
  and results only according to the payload policy (sizes only, masked or complete).
- Prometheus metrics count calls and duration per server, tool and status; traces pass
  the trace context on to the upstream.

## Administration {#verwaltung}

MCP servers and grants are managed through the admin API (`mcp-servers`, `mcp-grants`), the admin UI
(“MCP servers” page with connection state and grants) or as a GitOps manifest. Agents
that sign in with a signed token (see
[Workload and agent identities](workload-identities.html)) also receive the grants of the
mapped key.

## Distinction from tool policies {#abgrenzung}

The MCP gateway controls which tools a client reaches **through ai-gw**. Many applications,
however, connect MCP servers themselves and only send the tool definitions along in the model request.
For this case there are the [tool inventory and tool policies](tool-policies.html).

## Open items {#offen}

Sessions across multiple instances (sticky sessions or a shared session store), resumption
of SSE streams, OAuth to the upstream, grants at resource and prompt level, and the
plugin chain on tool arguments and results are not yet implemented.
