title: Betrieb und Härtung
summary: Empfehlungen für den Betrieb von ai-gw – Netz und Listener, Geheimnisse, Datenhaltung und mehrere Instanzen, Admin-Zugang, Datenebene, Plugins, Monitoring und Audit.
group: betrieb
order: 20
quelle: Betriebshandbuch (Installation, Datenhaltung, Monitoring, Härtung)
---
Das Betriebshandbuch im Repository (`docs/betrieb/`) beschreibt Installation, Konfiguration,
Datenhaltung, Monitoring, Anmeldung per OIDC, Fehlersuche, Härtung und Leistung im Detail.
Diese Seite fasst die wichtigsten Empfehlungen zusammen.

## Netz und Listener {#netz}

- **Daten- und Steuerebene trennen.** Die Datenebene (Port 4000) ist für Anwendungen da; die
  Steuerebene (Port 4001) mit Admin-API, UI und Metriken gehört ins Verwaltungsnetz oder hinter
  einen Ingress mit Zugriffsbeschränkung.
- **Reverse Proxy vor die Datenebene:** TLS-Terminierung (ai-gw spricht selbst Klartext-HTTP/1.1
  und h2c), HSTS, Verbindungs- und Ratenlimits je Client-IP.
- **Verbindungsschutz im Gateway:** Höchstzahl gleichzeitiger Verbindungen je Listener (darüber
  sofort `503`), Lese-Timeouts für Kopf und Körper der Anfrage gegen Slowloris, Keep-Alive-Leerlauf
  und HTTP/2-Grenzen. Laufende Antworten – auch minutenlange Streams – brechen diese Timeouts nicht
  ab. Das Leerlauf-Timeout größer wählen als das eines vorgeschalteten Load Balancers.
- **Ausgehend** zusätzlich zur SSRF-Prüfung eine Egress-Firewall: nur Anbieter, IdP, Webhook- und
  MCP-Ziele erlauben, Metadaten-Endpunkte der Cloud auf Netzebene sperren.
- Ausnahmen für private Upstreams (z. B. ein vLLM im eigenen Netz) so eng wie möglich fassen:
  einzelne Hosts statt großer Bereiche. Sie gelten nur für Ressourcen, die globale Admins oder
  GitOps anlegen.

## Geheimnisse {#geheimnisse}

- Master-Key mit `aigw keygen` erzeugen, als Datei-Secret einbinden und **getrennt von
  Datenbank-Backups** aufbewahren – wer beides hat, hat alle Zugangsdaten.
- Rotation über eine Liste vorheriger Schlüssel und `aigw config rekey`; alte Schlüssel nach der
  Neuverschlüsselung entfernen.
- In GitOps-Manifesten nur Verweise auf Umgebungsvariablen (`AIGW_SECRET_*`) oder Dateien,
  nie Klartext.
- Den optionalen Snapshot-Cache nur auf einem Pfad ablegen, den ausschließlich der
  Gateway-Benutzer schreiben kann; sein Höchstalter begrenzt, wie lange ein Start ohne
  Datenbank mit altem Stand möglich ist.

## Datenhaltung und mehrere Instanzen {#datenhaltung}

| Aufbau | Datenbank | Zähler | Hinweis |
|---|---|---|---|
| Einzelinstanz | SQLite im Volume | lokal | einfachster Betrieb |
| Mehrere Instanzen | Postgres | Redis (exakt) oder Abgleich über Postgres | Änderungen per LISTEN/NOTIFY in unter einer Sekunde überall wirksam |
| Lastbetrieb | Postgres | Redis | Request-Log-Writer konkurriert sonst mit dem Budget-Abgleich |

Datenbank-Migrationen laufen beim Start; Backups der Datenbank enthalten Zugangsdaten nur
verschlüsselt. Fällt die Datenbank im Betrieb aus, arbeitet der Gateway mit dem letzten Snapshot
weiter; fällt Redis aus, zählt er lokal weiter.

## Admin-Zugang {#admin}

- **OIDC** bevorzugen (Microsoft Entra ID, Keycloak oder ein anderer IdP) und Rollen an
  IdP-Gruppen binden; Sitzungen kurz halten.
- Das **Bootstrap-Token** gilt nur bis zum ersten globalen Admin per OIDC oder Admin-API-Key und
  erlischt dann automatisch.
- Die Rolle `gitops` schreibt standardmäßig keine Nutzer mit Rollen und keine Admin-Keys.
- Entra-Anmeldung per Workload- oder Managed Identity an Anbieter-Zugangsdaten nur ausdrücklich
  freigeben; Zertifikatsschlüssel möglichst verschlüsselt ablegen.
- Einladungslinks sind Inhaber-Token und gehören in einen vertraulichen Kanal.

## Datenebene {#datenebene}

- Keys mit Ablaufdatum, Limits und Budgets je Organisation und Team; widerrufene Keys wirken
  sofort, auch über Instanzen hinweg.
- Limits für gleichzeitige Anfragen bei mehreren Instanzen mit Redis-Zählern betreiben; beim
  Abgleich über Postgres gelten sie je Instanz.
- MCP-Sessions je Key und Team passend zur Nutzung begrenzen.
- Guardrails mit externen Diensten auf `failMode: closed`; ein Prüfmodell mit eigener
  Kapazitätsgrenze versehen und die Zahl der Prüfungen je Anfrage begrenzen. Azure AI Content
  Safety bevorzugt mit Entra ID statt API-Key anbinden.
- **Payload-Logging** nur, wo nötig. Inhalte lesen nur `admin` und `auditor`; bei
  Compliance-Pflichten an der Organisation eine Obergrenze setzen und sperren.

## Plugins {#plugins}

- Webhook-Plugins mit Secret signieren lassen und auf `failMode: closed` setzen.
- WASM-Module nur aus vertrauenswürdiger Quelle, mit Signaturpflicht über eigene Ed25519-Schlüssel
  (privater Schlüssel außerhalb des Gateways) und festgeschriebenem SHA-256 in der Bindung. Wer
  keine WASM-Plugins braucht, schaltet sie ab. Details: [WASM-Plugins](wasm-plugins.html).

## Monitoring {#monitoring}

- `/healthz` (Liveness) und `/readyz` (Readiness, mit Zustand `degraded` bei veraltetem oder aus
  dem Cache geladenem Snapshot) auf beiden Listenern.
- Prometheus-Metriken unter `/metrics` – unter anderem Anfragen, Latenzen, Tokens, Kosten,
  Upstream-Fehler, Circuit Breaker, Cache, verworfene Log-Ereignisse, Verbindungen und
  Timeouts der Listener, Plugins, MCP und WASM. Alarme lohnen sich besonders für abgewiesene
  Verbindungen, verworfene Log-Ereignisse und `degraded`.
- OpenTelemetry-Traces und -Logs per OTLP/HTTP, Request-Log zusätzlich als JSON-Lines-Datei mit
  Rotation.

## Audit {#audit}

- Jede Admin-Änderung steht im Audit-Log mit Vorher/Nachher; Geheimnisse sind redigiert.
- Die Hash-Kette regelmäßig prüfen (Admin-API, UI oder `aigw audit verify`) und den Kopf-Hash
  extern ablegen.
- Schreibrechte auf die Datenbank nur für den Gateway-Benutzer.

## Abhängigkeiten {#abhaengigkeiten}

Die Prüfkette führt `cargo deny` (Lizenzen und Sicherheitsmeldungen) aus; für die UI zusätzlich
`pnpm audit`. Bewusst akzeptierte Ausnahmen stehen begründet und mit Prüftermin in der
Konfiguration des Repositorys.

Leistungsdaten und Empfehlungen für Lastbetrieb: [Leistung und Lastvergleich](leistung.html).
