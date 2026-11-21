title: Architektur
summary: Wie ai-gw aufgebaut ist – ein Binary mit Daten- und Steuerebene, ein Konfigurations-Snapshot im Speicher, ein heißer Pfad ohne Datenbankzugriff und Streaming mit Backpressure.
toc: ja
---
## Ziele {#ziele}

ai-gw soll im heißen Pfad möglichst wenig kosten und im Betrieb einfach bleiben. Die
Qualitätsziele der ersten Version:

| Ziel | Zielwert |
|---|---|
| Zusätzliche Latenz durch das Gateway (ohne Plugins und Cache) | p50 < 200 µs, p99 < 1 ms |
| Aufschlag auf die Time-to-first-token | < 1 ms – Chunks werden sofort weitergereicht |
| Gleichzeitige Streams | ≥ 10.000 je Instanz mit 2 vCPU und 1 GB RAM |
| Kaltstart bis betriebsbereit | < 500 ms (SQLite) |
| Wirksamwerden von Konfigurationsänderungen | < 1 s auf allen Instanzen |
| Datenbankzugriff im heißen Pfad | keiner – Anmeldung, Routing, Limits und Policies kommen aus dem RAM |
| Ausfall von Datenbank oder Redis | Proxy läuft mit dem letzten Snapshot weiter; Zähler fallen auf lokal zurück |

Wie weit die Ziele erreicht sind, steht unter [Leistung und Lastvergleich](doku/leistung.html).

## Ein Binary, zwei Ebenen {#ebenen}

Das Binary `aigw` öffnet zwei Listener, die sich auf einen Port zusammenlegen lassen:

- **Datenebene** (Standard `:4000`): OpenAI-kompatible API, Anthropic-Messages-API und MCP-Gateway.
- **Steuerebene** (Standard `:4001`): Admin-API unter `/admin/api/v1`, Admin-UI unter `/admin/`,
  `/metrics`, `/healthz` und `/readyz`.

Die Trennung erlaubt, die Steuerebene nur im Verwaltungsnetz zu veröffentlichen. Laufzeit ist
tokio mit hyper (HTTP/1.1 und HTTP/2) und rustls; zu den Anbietern hält ai-gw je Endpunkt einen
eigenen Verbindungspool mit Keep-Alive und HTTP/2.

::: html
<figure class="diagram">
<svg class="g" viewBox="0 0 760 250" role="img" aria-labelledby="pipe-t pipe-d">
  <title id="pipe-t">Weg einer Anfrage durch ai-gw</title>
  <desc id="pipe-d">Eine Anfrage durchläuft Annahme, Anmeldung, Kontext mit Modellfreigabe, Reservierung der Limits, Plugins vor der Anfrage und Cache. Ein Cache-Treffer antwortet sofort. Sonst wählt das Routing ein Deployment, der Adapter übersetzt ins Anbieterformat und sendet an den Anbieter; bei Fehlern vor dem ersten Byte folgen Retry oder Fallback. Die Antwort fließt Chunk für Chunk durch Adapter und Stream-Plugins zum Client, danach werden Usage und Kosten abgerechnet und ein Log-Ereignis geschrieben.</desc>
  <defs><marker id="pp-ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path class="ah-acc" d="M0,0 L10,5 L0,10 z"/></marker></defs>
  <rect class="box" x="6" y="20" width="96" height="44" rx="5"/><text class="b" x="54" y="40" text-anchor="middle">Annahme</text><text class="s" x="54" y="55" text-anchor="middle">Header, Größe</text>
  <rect class="box" x="114" y="20" width="96" height="44" rx="5"/><text class="b" x="162" y="40" text-anchor="middle">Anmeldung</text><text class="s" x="162" y="55" text-anchor="middle">Key-Hash · JWT</text>
  <rect class="box" x="222" y="20" width="96" height="44" rx="5"/><text class="b" x="270" y="40" text-anchor="middle">Kontext</text><text class="s" x="270" y="55" text-anchor="middle">Freigabe · Tools</text>
  <rect class="box" x="330" y="20" width="96" height="44" rx="5"/><text class="b" x="378" y="40" text-anchor="middle">Limits</text><text class="s" x="378" y="55" text-anchor="middle">reservieren</text>
  <rect class="soft" x="438" y="20" width="96" height="44" rx="5"/><text class="b" x="486" y="40" text-anchor="middle">Plugins</text><text class="s" x="486" y="55" text-anchor="middle">Guardrails</text>
  <rect class="box" x="546" y="20" width="96" height="44" rx="5"/><text class="b" x="594" y="40" text-anchor="middle">Cache</text><text class="s" x="594" y="55" text-anchor="middle">exakt · semantisch</text>
  <path class="acc-ln" d="M102 42 H112M210 42 H220M318 42 H328M426 42 H436M534 42 H544" marker-end="url(#pp-ah)"/>
  <path class="acc-ln" d="M642 42 H700 V70" marker-end="url(#pp-ah)"/><text class="s" x="704" y="36">Treffer</text>
  <path class="acc-ln" d="M594 64 V100" marker-end="url(#pp-ah)"/>
  <rect class="box" x="546" y="104" width="96" height="44" rx="5"/><text class="b" x="594" y="124" text-anchor="middle">Routing</text><text class="s" x="594" y="139" text-anchor="middle">Deployment wählen</text>
  <rect class="box" x="438" y="104" width="96" height="44" rx="5"/><text class="b" x="486" y="124" text-anchor="middle">Adapter</text><text class="s" x="486" y="139" text-anchor="middle">Anbieterformat</text>
  <rect class="solid" x="330" y="104" width="96" height="44" rx="5"/><text class="on" x="378" y="131" text-anchor="middle">Anbieter</text>
  <path class="acc-ln" d="M546 126 H536M438 126 H428" marker-end="url(#pp-ah)"/>
  <path class="ln" d="M378 104 C378 86 594 86 594 100"/><text class="s" x="460" y="92" text-anchor="middle">Retry · Fallback vor dem 1. Byte</text>
  <path class="acc-ln" d="M378 148 V180" marker-end="url(#pp-ah)"/>
  <rect class="box" x="330" y="184" width="96" height="44" rx="5"/><text class="b" x="378" y="204" text-anchor="middle">Stream</text><text class="s" x="378" y="219" text-anchor="middle">Chunk für Chunk</text>
  <rect class="soft" x="438" y="184" width="96" height="44" rx="5"/><text class="b" x="486" y="204" text-anchor="middle">Stream-Plugins</text><text class="s" x="486" y="219" text-anchor="middle">Ausgabe prüfen</text>
  <rect class="box" x="652" y="74" width="100" height="154" rx="5"/><text class="b" x="702" y="146" text-anchor="middle">Client</text><text class="s" x="702" y="162" text-anchor="middle">Eingangsformat</text>
  <path class="acc-ln" d="M426 206 H436M534 206 H648" marker-end="url(#pp-ah)"/>
  <rect class="box" x="114" y="184" width="200" height="44" rx="5"/><text class="b" x="214" y="204" text-anchor="middle">Abrechnen · Log</text><text class="s" x="214" y="219" text-anchor="middle">Usage, Kosten, Ring-Puffer</text>
  <path class="ln" d="M330 206 H318" marker-end="url(#pp-ah)"/>
</svg>
<figcaption>Weg einer Anfrage. Alle Entscheidungen kommen aus dem Konfigurations-Snapshot im Speicher.</figcaption>
</figure>
:::

## Weg einer Anfrage {#hot-path}

1. **Annahme:** Header lesen, den Body nur so weit auswerten wie nötig. Der Body wird erst nach
   gültiger Anmeldung gelesen; Größe und Header sind begrenzt.
2. **Anmeldung:** API-Key aus `Authorization`, `api-key` oder `x-api-key`, SHA-256 bilden und im
   Snapshot nachschlagen – oder ein signiertes Token gegen den konfigurierten Aussteller prüfen.
3. **Kontext:** Modell-Alias auflösen, Freigabe prüfen, Tool-Richtlinien anwenden. Die wirksame
   Policy (Organisation → Team → Key → Modellgruppe) ist beim Snapshot-Aufbau vorberechnet.
4. **Limits:** Zähler werden reserviert; bei Überschreitung folgt sofort `429`.
5. **Plugins vor der Anfrage:** Guardrails, PII-Maskierung, Header und Transformationen.
6. **Cache:** zuerst exakt, dann semantisch, sofern aktiviert.
7. **Routing:** ein Deployment aus der Modellgruppe wählen; Retries und Fallbacks nur, solange
   noch kein Byte zum Client gegangen ist.
8. **Übersetzung und Streaming:** Anbieterformat hin und zurück, Chunk für Chunk.
9. **Abrechnung:** Usage gleicht die Reservierung aus, schreibt Kosten fort und prüft Budgets.
10. **Log:** ein Ereignis geht nicht blockierend in einen begrenzten Kanal; der Proxy wartet nie
    auf Logs. Ist der Kanal voll, wird verworfen und gezählt.

## Konfigurations-Snapshot {#snapshot}

Jede Admin-Änderung läuft als Datenbanktransaktion, erhöht eine monotone Konfigurationsversion
und schreibt das Audit-Log. Jede Instanz hält einen **unveränderlichen Snapshot** mit
vorberechneten Indizes (Key-Hash → Kontext, Alias → Modellgruppe, zusammengesetzte
Plugin-Ketten). Laufende Anfragen behalten ihren Snapshot; neue sehen sofort den neuen.

- Mit SQLite wird nach dem Commit neu aufgebaut, mit Postgres per `LISTEN/NOTIFY` auf allen
  Instanzen; eine regelmäßige Versionsabfrage fängt verlorene Benachrichtigungen ab.
- Der Neubau ist **inkrementell**: Das Audit-Log dient als Änderungsjournal, nur betroffene
  Objekte werden neu geladen. Eine periodische Konsistenzprüfung vergleicht mit einem
  vollständigen Neubau.
- Optional schreibt ai-gw den Snapshot **verschlüsselt** (AES-256-GCM mit dem Master-Key) auf
  Platte. Ist die Datenbank beim Start nicht erreichbar, startet der Gateway mit diesem Stand und
  meldet sich über `/readyz` als `degraded`.

## Formate und Anbieter-Adapter {#formate}

Eingehende Anfragen werden in eine kanonische Zwischendarstellung übersetzt; jeder
Anbieter-Adapter übersetzt von dort in sein Format und zurück. Dadurch sind alle Kombinationen
aus Eingangsformat und Anbieter möglich, und Plugins, Cache und Abrechnung arbeiten nur auf einem
Modell. Unbekannte Felder bleiben erhalten, wo das Zielformat sie kennt.

## Streaming {#streaming}

- Bytes vom Anbieter laufen durch einen inkrementellen SSE-Decoder, werden zu Ereignissen der
  Zwischendarstellung und im Format des Clients wieder kodiert.
- **Backpressure:** gelesen wird nur, wenn der Client Daten abnimmt; es gibt keinen unbegrenzten
  Puffer.
- **Client-Abbruch** bricht die Anfrage zum Anbieter sofort ab; fehlt die Usage, wird sie
  geschätzt und als geschätzt markiert.
- Stream-Plugins arbeiten auf einem Gleitfenster; wer die ganze Antwort prüfen muss, schaltet
  die Route auf „gepuffert“.

## Limits, Zähler und Budgets {#zaehler}

Zähler sind austauschbar: **lokal** (je Instanz), **postgres-sync** (Abgleich alle ein bis zwei
Sekunden, leicht unscharf) und **redis** (exakt, verteilt). Fällt Redis aus, rechnet der Gateway
lokal weiter. Budgets können strikt (mit Reservierung vor der Anfrage) oder weich (Abrechnung
danach) sein.

## Datenhaltung und Hochverfügbarkeit {#datenhaltung}

SQLite ist Standard für eine Instanz. Für mehrere Instanzen hinter einem Load Balancer dient
Postgres als gemeinsame Datenbank; Zähler laufen dann über `postgres-sync` oder Redis, der
semantische Cache optional über pgvector oder Redis Search. Zugangsdaten zu Anbietern liegen mit
AES-256-GCM verschlüsselt in der Datenbank; der Master-Key liegt nie dort. Das Request-Log wird
gepuffert und gebündelt geschrieben und kann zusätzlich per OpenTelemetry oder als JSON-Lines
exportiert werden.

## Technik {#technik}

- **Gateway:** Rust (tokio, hyper/axum, tower, rustls mit aws-lc-rs), aufgeteilt in Crates für
  Kern und Zwischendarstellung, Proxy, Anbieter, ausgehende Verbindungen mit SSRF-Schutz,
  Token-Prüfung, Persistenz, Zähler, Kosten, Plugins und PII-Erkennung, WASM-Plugins, Cache,
  MCP, Beobachtung, Tokenizer, Webhooks und Admin-API.
- **Admin-UI:** Svelte 5, Vite, TypeScript, Bits UI und Tailwind; die TypeScript-Typen werden aus
  der OpenAPI-Spezifikation der Admin-API erzeugt.
- **Konfiguration:** YAML für Startkonfiguration und GitOps-Ressourcen, alle Startwerte auch als
  Umgebungsvariable `AIGW_…`.
- **Qualität:** Formatierung, Lints ohne Warnungen, Tests, `cargo deny`, OpenAPI-Abgleich,
  UI-Prüfungen und REUSE-Konformität in einer Prüfkette; Lizenzübersicht der Abhängigkeiten im
  Repository.

Vertiefung: [MCP-Gateway](doku/mcp-gateway.html) · [WASM-Plugins](doku/wasm-plugins.html) ·
[Workload- und Agent-Identitäten](doku/workload-identitaeten.html) ·
[Betrieb und Härtung](doku/betrieb.html).
