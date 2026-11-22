title: Schnellstart
summary: ai-gw mit Docker starten, die Admin-UI öffnen, einen Anbieter anbinden und den ersten Request senden – dazu Docker Compose mit Postgres und Redis, Kubernetes und Betrieb ohne Container.
toc: ja
---
> **Vorabversion.** Fertige Container-Images werden mit dem ersten Release veröffentlicht. Bis
> dahin wird das Image aus dem Repository gebaut (Docker mit BuildKit). Bis 1.0 können sich
> Konfiguration, Manifest-Format und Admin-API inkompatibel ändern – das
> [Changelog](https://github.com/mupf-dev/ai-gw/blob/main/CHANGELOG.md) nennt solche Änderungen.

## 1. Image bauen und starten {#starten}

```sh
git clone https://github.com/mupf-dev/ai-gw.git && cd ai-gw
docker build -t ai-gw:dev .                              # Image bauen (BuildKit)
docker run --rm ai-gw:dev keygen > aigw-master-key       # Master-Key erzeugen
docker volume create aigw-data
docker run -d --name aigw --read-only --cap-drop ALL --security-opt no-new-privileges \
  -p 127.0.0.1:4000:4000 -p 127.0.0.1:4001:4001 \
  -e AIGW_MASTER_KEY="$(cat aigw-master-key)" \
  -e AIGW_SECRET_OPENAI_API_KEY="sk-…" \
  -v aigw-data:/data ai-gw:dev
docker logs aigw 2>&1 | grep Bootstrap-Token             # einmaliges Admin-Token
```

Das Image ist distroless, läuft ohne Root mit schreibgeschütztem Dateisystem und bringt einen
Healthcheck mit; es lässt sich für amd64 und arm64 bauen. Der Master-Key verschlüsselt alle
gespeicherten Zugangsdaten – getrennt von Datenbank-Backups aufbewahren. Statt der
Umgebungsvariablen ist eine Datei als Docker- oder Kubernetes-Secret besser
(`AIGW_SECRETS__MASTER_KEY_FILE`).

Port 4000 ist die **Datenebene** für Anwendungen, Port 4001 die **Steuerebene** mit Admin-UI,
Admin-API und Metriken. Beide hier nur an `127.0.0.1` gebunden.

## 2. Admin-UI öffnen {#admin-ui}

`http://localhost:4001/admin/` mit dem Bootstrap-Token öffnen. Das Token erlischt automatisch,
sobald sich ein globaler Admin per OIDC angemeldet hat oder ein Admin-API-Key mit Rolle `admin`
existiert. In der UI nacheinander anlegen:

1. eine **Organisation** (und bei Bedarf Teams),
2. **Zugangsdaten** für einen Anbieter – im Beispiel ein Verweis auf die Umgebungsvariable
   `AIGW_SECRET_OPENAI_API_KEY`, nie der Klartext im Manifest,
3. eine **Modellgruppe** mit einem **Deployment**,
4. einen **API-Key** für die Anwendung.

## 3. Oder alles als YAML {#yaml}

Dieselben Ressourcen lassen sich als Manifeste anwenden – in der UI unter „YAML-Import/-Export“,
per Admin-API oder mit `aigw config apply`. Das Beispiel `config/examples/minimal/resources.yaml`
aus dem Repository:

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

Weitere Beispiele im Repository unter `config/examples/`: Anbieter, Teams und Budgets,
Guardrails, Cache, MCP, GitOps und ein Aufbau mit Postgres und Redis.

## 4. Erster Request {#request}

Einen API-Key in der UI anlegen (der Klartext erscheint nur einmal) und mit jedem
OpenAI-kompatiblen Client verwenden:

```sh
curl -s localhost:4000/v1/chat/completions -H "authorization: Bearer sk-aigw-…" \
  -H 'content-type: application/json' \
  -d '{"model":"gpt-4o-mini","messages":[{"role":"user","content":"Hallo"}]}'
```

In SDKs genügt es, die Basis-URL auf `http://localhost:4000/v1` und den Key auf den
virtuellen Key zu setzen. Anthropic-Clients nutzen `POST /v1/messages` mit dem Key im Header
`x-api-key`. Die Anfrage erscheint sofort im Log-Explorer – mit Tokens, Kosten und Latenz.

## Docker Compose mit Postgres und Redis {#compose}

Für mehrere Instanzen oder größere Last liegt unter `deploy/compose/` ein Aufbau mit Postgres 17,
Redis 7 und optional einem OpenTelemetry-Collector bereit:

```sh
cd deploy/compose
cp env.example .env && $EDITOR .env                      # POSTGRES_PASSWORD setzen
mkdir -p secrets
docker run --rm ai-gw:dev keygen > secrets/aigw-master-key
sudo chown 65532:65532 secrets/aigw-master-key && sudo chmod 0400 secrets/aigw-master-key
docker compose up -d
docker compose ps                                        # aigw: healthy
```

## Kubernetes {#kubernetes}

`deploy/kubernetes/` enthält ein kustomize-Grundgerüst: ConfigMap mit der Startkonfiguration,
Deployment mit zwei Replikaten (nicht-root, schreibgeschütztes Dateisystem), Services für Daten-
und Steuerebene, Probes auf `/healthz` und `/readyz` sowie ein PodDisruptionBudget. Den Master-Key
als Secret einbinden, die Steuerebene nur intern veröffentlichen.

## Ohne Container {#binary}

ai-gw ist ein einzelnes Binary. Gebaut wird es mit der Rust-Toolchain aus dem Repository (die
Admin-UI vorher mit pnpm); danach genügen `aigw keygen`, `aigw config check` und `aigw serve`,
gern als systemd-Dienst mit großzügigem Limit für Dateideskriptoren.

## Nächste Schritte {#weiter}

- **Anmeldung per OIDC** (Microsoft Entra ID, Keycloak oder ein anderer IdP) einrichten und
  Rollen an IdP-Gruppen binden.
- **Guardrail-Profil** „Basis“ global oder je Team anwenden: [Guardrails & Sicherheit](sicherheit.html).
- **Limits und Budgets** je Team setzen, Preise prüfen.
- **Monitoring** über `/metrics` und OpenTelemetry anbinden.
- **Härtung** nach [Betrieb und Härtung](doku/betrieb.html).
