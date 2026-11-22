title: Mitmachen und Lizenz
summary: Wie man zu ai-gw beitragen kann, unter welchen Lizenzen Code und Dokumentation stehen und wie Sicherheitslücken gemeldet werden.
toc: ja
---
## Mitmachen {#mitmachen}

ai-gw wird offen entwickelt; Quellcode, Konzepte und Betriebshandbuch liegen im Repository
[github.com/mupf-dev/ai-gw](https://github.com/mupf-dev/ai-gw). Willkommen sind insbesondere:

- **Erfahrungsberichte und Fehlermeldungen** als Issue – mit Version, Startkonfiguration (ohne
  Geheimnisse) und, wenn möglich, einem nachvollziehbaren Beispiel.
- **Anbieter und Formate:** Abweichungen einzelner Anbieter, neue Modellfähigkeiten,
  Interoperabilität mit Clients und SDKs, MCP-Clients.
- **Guardrails:** Falsch-Positive und -Negative der PII-Erkennung und der Injection-Heuristik,
  neue Erkennungsregeln, Beispiel-Plugins als WebAssembly-Komponente.
- **Betrieb:** Erfahrungen mit Kubernetes, Postgres, Redis, OpenTelemetry und großen
  Installationen; Lastmessungen auf anderer Hardware.
- **Code** in Rust für Gateway und Admin-API, Svelte und TypeScript für die Admin-UI,
  Dokumentation und Übersetzungen.

## Regeln für Beiträge {#regeln}

- **Prüfkette grün:** `scripts/check.sh` bündelt Formatierung, Lints ohne Warnungen, Tests,
  `cargo deny` (Lizenzen und Sicherheitsmeldungen der Abhängigkeiten), Abgleich der
  OpenAPI-Spezifikation, Typprüfung und Build der UI sowie REUSE. Die CI führt dieselben
  Prüfungen bei Pull Requests aus.
- **Admin-API geändert?** OpenAPI-Spezifikation und TypeScript-Typen der UI neu erzeugen und
  mit einchecken.
- **Jede Datei trägt SPDX-Lizenzangaben** (REUSE-konform).
- **Neue Abhängigkeiten** nur nach Prüfung von Lizenz, Wartungsstand und Nutzen; die
  Lizenzübersicht `THIRD-PARTY.md` wird mit einem Skript erzeugt.
- **Konzept vor Code:** Größere Änderungen beginnen mit einem Abschnitt in `docs/konzept/` –
  mit Begründung, Sicherheitsbetrachtung und Messwerten, wo der heiße Pfad betroffen ist.
- **Changelog** im Abschnitt „Unreleased“ pflegen, inkompatible Änderungen ausdrücklich
  kennzeichnen.

```sh
# typischer Ablauf
git clone https://github.com/mupf-dev/ai-gw.git && cd ai-gw
scripts/setup-tools.sh        # Toolchain und Prüfwerkzeuge in festen Versionen
scripts/check.sh              # alle Prüfungen lokal
scripts/runtime-smoke.sh      # Release-Binary mit UI bauen, starten und prüfen
```

## Lizenz {#lizenz}

| Bestandteil | Lizenz |
|---|---|
| Code: Gateway, Admin-API, Admin-UI, Werkzeuge | FSL-1.1-ALv2 (Functional Source License) |
| Plugin-Schnittstelle (WIT) und Beispiel-Plugins | Apache-2.0 |
| Dokumentation: `docs/`, README, CHANGELOG | CC BY 4.0 |
| Diese Website: Inhalte | CC BY 4.0 |
| Diese Website: Generator, Prüfskript, Stylesheet, Skript | GNU AGPL-3.0-or-later |

Die [Functional Source License](https://fsl.software/) erlaubt jede Nutzung – auch kommerziell,
im eigenen Unternehmen und mit Änderungen –, ausgenommen ein konkurrierendes kommerzielles Produkt
oder einen konkurrierenden Dienst. Jede Version wird zwei Jahre nach ihrer Veröffentlichung
automatisch zusätzlich unter Apache-2.0 freigegeben. Kommerzielle Lizenzen für andere Nutzungen
vergibt der Rechteinhaber (siehe `LICENSE` im Repository). Stände bis 21.11.2026 stehen unter AGPL-3.0-or-later.
Das Repository ist REUSE-konform; die Lizenzen der Abhängigkeiten stehen in `THIRD-PARTY.md` und
werden mit `cargo deny` gegen eine Positivliste geprüft.

## Sicherheitslücke melden {#sicherheit}

Bitte **keine öffentlichen Issues, Pull Requests oder Diskussionen** für Sicherheitsprobleme.
Meldungen bitte vertraulich per E-Mail an die im [Impressum](impressum.html) genannte Adresse –
mit Beschreibung, betroffener Version bzw. Commit und, wenn möglich, einem Nachweis. Ein
vertraulicher Meldeweg direkt auf GitHub und eine Sicherheitsrichtlinie im Repository folgen mit
dem ersten Release.

Es gelten die üblichen Regeln koordinierter Offenlegung: Eingang wird bestätigt, die Lücke
gemeinsam bewertet, behoben und danach mit Dank an die meldende Person veröffentlicht, sofern
gewünscht.
