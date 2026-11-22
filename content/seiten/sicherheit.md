title: Guardrails & Sicherheit
summary: Wie ai-gw Prompts und Antworten prüft – PII, Prompt-Injection, System-Prompt-Lecks, Datenabfluss über Links, Sprachen, strukturierte Ausgaben, externe Inhaltsprüfung – und welche Schutzmaßnahmen im Gateway selbst greifen.
toc: ja
---
Ein AI-Gateway sieht jede Anfrage und jede Antwort. Das macht es zum richtigen Ort für
Schutzregeln – und verpflichtet es, selbst sorgfältig mit Daten, Schlüsseln und ausgehenden
Verbindungen umzugehen. Beides beschreibt diese Seite.

## Guardrails als Plugins {#guardrails}

Guardrails sind normale Plugins der Kette. Sie werden global, je Organisation, Team, Key oder
Modellgruppe gebunden, erben nach innen, lassen sich gegen Überschreiben sperren und haben ein
festgelegtes Verhalten bei Fehlern (`failMode: closed` lehnt ab, `open` lässt durch). Eine
typische Reihenfolge: zuerst billige Prüfungen, die früh ablehnen, dann Maskierung, dann externe
Dienste auf dem bereits maskierten Text.

| Plugin | Phase | Zweck |
|---|---|---|
| `prompt-filter` | Anfrage, wahlweise Antwort und Stream | Wort- und Phrasenlisten, Regex-Regeln, Prompt-Injection-Heuristik, Grenzen für Länge und Anzahl, unsichtbare Unicode-Zeichen |
| `pii` | Anfrage, Antwort, Stream | personenbezogene Daten und Geheimnisse erkennen; maskieren, entfernen, ablehnen, pseudonymisieren (mit Rückübersetzung) oder zählen |
| `prompt-leak` | Anfrage, Antwort, Stream | Lecks des System-Prompts über ein Canary-Token, optional wörtliche Auszüge |
| `link-guard` | Antwort, Stream, optional Anfrage | Datenabfluss über Links und Bilder zu fremden Domains verhindern |
| `language` | Anfrage, wahlweise Antwort | erlaubte bzw. gesperrte Sprachen |
| `schema-guard` | Antwort, Stream | strukturierte Ausgaben (JSON-Schema, JSON-Modus, erzwungene Tools) gegen ihr Schema prüfen |
| `content-safety` | Anfrage, Antwort, Stream | externe Prüfung über Azure AI Content Safety, OpenAI Moderation oder ein eigenes Prüfmodell |

Abgelehnte Antworten kommen im Format des Clients zurück (z. B. `finish_reason: content_filter`
bzw. eine Ablehnung im Anthropic-Format) und tragen den Header `x-aigw-guardrail` mit dem
auslösenden Plugin.

## PII und Geheimnisse {#pii}

Die PII-Erkennung ist eine eigene, regelbasierte Engine ohne externes Modell. Sie erkennt
E-Mail-Adressen, Telefonnummern (international und deutsch), IBAN (mit Prüfsumme für 75 Länder),
Kreditkarten (BIN-Bereiche und Luhn), deutsche Steuer-ID, Sozialversicherungs-, Ausweis- und
Passnummern (jeweils mit Prüfziffer), IP-Adressen, Zugangsdaten in URLs sowie API-Keys und Tokens
gängiger Dienste – ergänzt um eine Entropie-Heuristik für unbekannte Geheimnisse.

- **Aktionen je Kategorie:** maskieren (`[EMAIL_1]`), entfernen, ablehnen, pseudonymisieren mit
  Rückübersetzung in der Antwort oder nur zählen.
- **Allowlist** für bekannte, unkritische Werte (etwa die eigene Support-Adresse).
- **Schnell:** ein Prompt von 4 KB mit Funden wird in etwa 23 µs geprüft (Median, ein Kern).
- Dieselbe Engine maskiert auf Wunsch die Inhalte im Request-Log.

Namen und Postadressen erkennt die Engine bewusst nicht – ohne Sprachmodell wären sie zu
fehleranfällig. Dafür lässt sich ein externer Dienst oder ein Prüfmodell über `content-safety`
oder einen Webhook einbinden.

## Prompt-Injection und unsichtbare Zeichen {#injection}

Der `prompt-filter` gewichtet bekannte Injection-Signale („ignoriere alle vorherigen
Anweisungen“, Rollenwechsel, Chat-Template-Tokens …) und lehnt ab einer Schwelle ab oder markiert
nur. Zusätzlich erkennt er **unsichtbare Unicode-Zeichen** – Tag-Zeichen („ASCII-Schmuggel“),
Zero-Width-, Bidi- und Formatzeichen – und entfernt sie oder lehnt ab; legitime Fälle wie
Emoji-Sequenzen oder Verbindungszeichen in persischer und indischen Schriften bleiben erhalten.
Wort- und Regex-Regeln können auch die Ausgabe prüfen, im Stream über Chunk-Grenzen hinweg.

## System-Prompt-Lecks {#prompt-leak}

`prompt-leak` setzt ein zufälliges **Canary-Token** in den System-Prompt – je Anfrage neu oder
stabil, damit das Prompt-Caching der Anbieter wirksam bleibt. Taucht das Token in Antwort,
Stream, Tool-Argumenten oder Reasoning auf, wird blockiert oder entfernt; das Token erreicht nie
den Client oder das Log. Optional erkennt das Plugin wörtliche Auszüge des System-Prompts über
Wort-N-Gramme.

## Datenabfluss über Links {#link-guard}

Eine eingeschleuste Anweisung – etwa in einem Tool-Ergebnis oder einem Dokument – kann ein
Modell dazu bringen, vertrauliche Daten in eine Bild-URL zu schreiben. Der Chat-Client lädt das
Bild beim Anzeigen ohne Klick, und die Daten landen beim Angreifer. `link-guard` entfernt Bilder
zu fremden Domains und kann Links, Query-Parameter oder lange Pfade entschärfen; erlaubte Domains
werden ausdrücklich konfiguriert.

## Sprachen und strukturierte Ausgaben {#language}

`language` lässt nur erlaubte Sprachen zu oder sperrt einzelne (ISO 639-1) – auf der Eingabe, auf
Wunsch auch auf der Ausgabe. Erkannt wird lokal ohne externen Dienst; zu kurze oder unsichere
Texte lassen sich über Mindestlänge und Mindestkonfidenz ausnehmen.

`schema-guard` prüft Antworten, für die der Client ein JSON-Schema verlangt hat (OpenAI
`response_format`, Anthropic `output_config.format`), JSON-Modus-Antworten auf gültiges JSON und
die Argumente erzwungener Tool-Aufrufe gegen deren Parameterschema. Bei einem Verstoß wird die
Antwort markiert, abgelehnt oder bis zu dreimal neu angefordert; Wiederholungen werden als
Plugin-Kosten abgerechnet. Schemas sind in Größe und Tiefe begrenzt und werden ohne Netz- oder
Dateizugriff ausgewertet.

## Externe Inhaltsprüfung {#content-safety}

`content-safety` fragt Azure AI Content Safety (per API-Key oder Microsoft Entra ID), OpenAI
Moderation oder ein **eigenes Prüfmodell** (z. B. Llama Guard) über eine Modellgruppe des
Gateways. Schwellen je Kategorie, Prüfung von Eingabe, Ausgabe oder beidem, Ausgabe gepuffert
oder satzweise im Stream; auch Tool-Call-Argumente werden geprüft. Kosten des Prüfmodells werden
erfasst und lassen sich begrenzen.

## Standard-Profile {#profile}

| Profil | Inhalt |
|---|---|
| **Basis** | Injection-Heuristik mit Ablehnung, Größengrenzen, unsichtbare Zeichen entfernen; PII-Maskierung für E-Mail, Telefon, IBAN, Karten, API-Keys und URL-Zugangsdaten |
| **Streng** | gesperrte Bindungen: strengere Schwelle, unsichtbare Zeichen ablehnen, Canary-Token, Karten und Geheimnisse ablehnen, weitere PII maskieren, Bilder zu fremden Domains entfernen, optional externe Inhaltsprüfung; Payload-Logging höchstens maskiert |
| **Offen** | nur großzügige Größengrenzen; Payload-Logging nur Metadaten |

Profile werden per UI oder Admin-API auf eine Ebene angewendet – mit Diff und Trockenlauf.

## Tools und MCP {#tools}

Anwendungen schicken die Tools, die ein Modell aufrufen darf, mit jeder Anfrage mit. ai-gw
inventarisiert sie, erkennt nachträglich geänderte Beschreibungen („Rug Pull“), prüft
Beschreibungen auf Injection-Signale und setzt **Tool-Richtlinien** durch: erlauben, entfernen,
ablehnen, beobachten oder erst nach Freigabe – auch für Tool-Aufrufe in der Antwort. MCP-Server
hinter dem Gateway sind standardmäßig für niemanden sichtbar; Freigaben gelten je Team und Key
bis auf einzelne Tools. Mehr: [Tool-Richtlinien](doku/tool-richtlinien.html),
[MCP-Gateway](doku/mcp-gateway.html).

## Sicherheit des Gateways {#gateway}

- **Geheimnisse:** Zugangsdaten verschlüsselt (AES-256-GCM), Master-Key nie in der Datenbank,
  Rotation per `aigw config rekey`. API-Keys nur als Hash; Logs enthalten nie `Authorization`-
  oder Key-Header, eingehende Tokens werden nie an Anbieter weitergereicht.
- **Ausgehende Verbindungen:** gemeinsamer Baustein mit **SSRF-Schutz** – Prüfung der URL beim
  Speichern und der Zieladresse bei jedem Verbindungsaufbau nach der Namensauflösung (gegen
  DNS-Rebinding), keine Weiterleitungen, Größen- und Zeitlimits. Private Ziele nur nach
  ausdrücklicher, eng gefasster Freigabe durch globale Admins.
- **Listener:** Höchstzahl gleichzeitiger Verbindungen, Lese-Timeouts gegen Slowloris,
  HTTP/2-Grenzen, Body-Limits; laufende Streams bleiben unberührt.
- **Admin-Zugang:** OIDC mit PKCE, Session-Cookies mit `__Host-`-Präfix, `SameSite=Strict` und
  CSRF-Token, Rollenmodell mit Team-Grenzen, einmaliges Bootstrap-Token nur bis zum ersten Admin.
- **Plugins in der Sandbox:** WASM-Module ohne Dateisystem, Netz und Umgebung, mit Grenzen für
  CPU, Zeit und Speicher und optionaler Ed25519-Signaturpflicht – siehe
  [WASM-Plugins](doku/wasm-plugins.html).
- **Nachvollziehbarkeit:** Audit-Log mit Hash-Kette, prüfbar per API, UI und `aigw audit verify`.
- **Lieferkette:** `cargo deny` mit Lizenz- und Advisory-Prüfung, festgelegte UI-Abhängigkeiten
  mit Mindestalter für neue Pakete, Lizenzübersicht aller Abhängigkeiten.

Das Projekt hat ein internes Sicherheitsreview durchlaufen; die daraus abgeleiteten
Betriebsempfehlungen stehen unter [Betrieb und Härtung](doku/betrieb.html). Sicherheitslücken
bitte vertraulich melden: [Sicherheitslücke melden](mitmachen.html#sicherheit).
