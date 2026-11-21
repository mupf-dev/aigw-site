title: Tool-Inventar und Tool-Richtlinien
summary: ai-gw erfasst jedes Tool, das Anwendungen in Modellanfragen mitschicken, erkennt geänderte oder verdächtige Beschreibungen und setzt Richtlinien durch – vom Entfernen einzelner Tools bis zur Freigabe im Einzelfall.
group: konzept
order: 20
quelle: Konzept 16 „Tool-Inventar und Tool-Richtlinien“
---
Anwendungen schicken mit jeder Modellanfrage die Tools mit, die das Modell aufrufen darf –
Coding-Assistenten etwa alle Tools ihrer MCP-Server als `mcp__<server>__<tool>`. Das Gateway
führt diese Tools nicht aus, sieht sie aber vollständig. Genau das nutzt ai-gw:

- **Inventar:** jedes Tool mit Name, Art, vermuteter Herkunft, Client, Organisation, Team und
  Key, erster und letzter Sichtung, Zahl der Anfragen und der Aufrufe durch das Modell.
- **Änderungen und Verdacht:** geänderte Beschreibungen oder Schemas bekannter Tools („Rug Pull“)
  und Beschreibungen mit Prompt-Injection-Signalen werden markiert, auditiert und gemeldet.
- **Richtlinien:** erlauben, entfernen, ablehnen, beobachten oder „erst nach Freigabe“ – auch
  für Tool-Aufrufe in der Antwort.

## Platz in der Pipeline {#pipeline}

```text
Anmeldung ─► Body ─► Modellfreigabe ─► [Tool-Richtlinien + Inventar] ─► Limits/Budgets
          ─► Guardrails ─► Cache ─► Routing
          ─► [Tool-Aufruf-Filter] ─► Ausgabe-Guardrails ─► Client
```

- **Vor Limits und Guardrails:** entfernte Tools zählen nicht zur Token-Schätzung, Guardrails und
  Webhooks sehen nur noch erlaubte Tools, eine Ablehnung belegt kein Kontingent.
- **Tool-Aufruf-Filter als innerste Antwortschicht:** Ausgabe-Guardrails sehen bereits gefilterte
  Antworten; auch Cache-Treffer laufen durch den Filter.
- Gilt für Chat Completions, Messages, Responses und den Playground. Ohne Tools in der Anfrage
  entfällt der Schritt vollständig.

## Inventar {#inventar}

| Merkmal | Herkunft |
|---|---|
| Name | Name der Funktion bzw. des Anbieter-Tools |
| Art | Funktion mit JSON-Schema, versioniertes Server-Tool eines Anbieters oder eingebautes Tool |
| Herkunft | MCP-Server aus dem Namensmuster (`mcp__<server>__<tool>` oder `<server>__<tool>`), sonst „client“ |
| Client | konfigurierbarer Header (z. B. `x-aigw-client`), sonst `User-Agent` |
| Zuordnung | Organisation, Team, Key und Name – je Anwendung ein Eintrag |

Für Beschreibung und Schema speichert ai-gw je einen Hash; das Schema wird dabei als JSON-Baum
gehasht, unabhängig von Leerzeichen und Schlüsselreihenfolge. Die **Inhalte** werden nur
gespeichert, wenn die Payload-Richtlinie des Keys es erlaubt – vollständig oder maskiert. Geprüft
wird die Beschreibung immer, im Speicher.

Im heißen Pfad kostet das Inventar wenig: Bekannte Definitionen werden über einen schnellen,
je Prozess zufällig geschlüsselten Fingerabdruck erkannt; nur neue oder geänderte Definitionen
werden kopiert. Ein Hintergrund-Task schreibt das Inventar gebündelt in die Datenbank – nie im
Anfragepfad. Mehrere Instanzen schreiben additiv in dieselben Einträge.

## Geänderte und verdächtige Tools {#aenderungen}

- **Geändert:** Weicht ein Hash vom gespeicherten Stand ab, wird der Eintrag markiert, der
  Verlauf fortgeschrieben, ein Audit-Eintrag geschrieben und das Ereignis `tool.changed` an die
  Ereignis-Webhooks gesendet. Auf Wunsch sperrt ai-gw das Tool für diesen Key automatisch, bis
  jemand die Änderung bestätigt.
- **Verdächtig:** Die Prompt-Injection-Signale des `prompt-filter` laufen über jede neue oder
  geänderte Beschreibung. Treffer werden mit den Signalnamen gespeichert, auditiert und als
  `tool.suspicious` gemeldet; gesperrt wird nicht automatisch.

## Richtlinien {#richtlinien}

```yaml
apiVersion: aigw/v1alpha1
kind: ToolPolicy
metadata: {name: block-destructive}
spec:
  scope: {level: global}               # global | organization | team | api-key | model-group
  tools: ["*delete*", "!delete_draft"] # Glob-Muster, !Ausschluss; leer = alle
  servers: [github]                    # Herkunft; leer = jede
  action: block-strip                  # allow | block-strip | block-reject | observe | require-approval
  locked: true                         # gilt auch gegen spezifischere allow-Regeln
  description: Zerstörerische Tools nie an Modelle geben
```

Ein Muster passt auf den vollen Namen oder auf den Namen ohne Server-Präfix. Entschieden wird je
Tool im Kontext der Anfrage:

1. Eine passende **gesperrte** Sperre gewinnt immer, gleich auf welcher Ebene.
2. Sonst gilt die passende `allow`- oder `block-*`-Richtlinie der **spezifischsten Ebene**
   (Key vor Modellgruppe vor Team vor Organisation vor global); auf gleicher Ebene die strengere.
3. Ohne solche Richtlinie greift eine passende `require-approval`-Richtlinie: Das Tool ist nicht
   freigegeben, bis eine `allow`-Richtlinie es erfasst.
4. Sonst ist das Tool erlaubt. `observe` ändert nichts, protokolliert aber und zählt.

| Wirkung | Anfrage | Antwort |
|---|---|---|
| erlauben | unverändert | – |
| entfernen (`block-strip`) | Tool aus der Anfrage entfernt; ein darauf erzwungenes `tool_choice` wird zu `auto` | Aufrufe dieses Tools unterbunden |
| ablehnen (`block-reject`) | `403` mit Code `tool_blocked` im Format des Eingangs | – |

Ruft ein Modell trotzdem ein nicht erlaubtes Tool auf – halluziniert, aus dem Verlauf oder als
eingebautes Anbieter-Tool –, behandelt ai-gw das wie eine Ausgabe-Ablehnung der Guardrails:
`finish_reason: content_filter` bzw. `stop_reason: refusal` und Header
`x-aigw-guardrail: tool-policy`. Im Stream werden ab diesem Aufruf keine Inhalte mehr
weitergegeben; bereits gesendeter Text bleibt, die Usage wird abgerechnet.

## Freigeben und Sperren aus dem Inventar {#freigabe}

In Admin-UI und Admin-API zeigt jeder Inventareintrag seinen Status: neu, freigegeben, gesperrt
oder wartend. „Freigeben“ und „Sperren“ schreiben normale `ToolPolicy`-Ressourcen je Ebene – mit
Audit, sofortiger Wirkung über den Snapshot und Export per GitOps. Die Rechte folgen denen der
Plugin-Bindungen: Team-Admins entscheiden im eigenen Team, globale Ebenen bleiben globalen
Admins vorbehalten; eingeschränkte Rollen sehen das Inventar nur in ihrem Bereich.

## Messwerte {#messwerte}

Gemessen mit 30 Tools je Anfrage (Beschreibung rund 600 Zeichen, Schema mit acht Feldern), ein
Kern:

| Fall | µs je Anfrage |
|---|---|
| ohne Tools | 0,02 |
| 30 Tools, ohne Inventar und Richtlinien | 2,6 |
| 30 Tools, 6 Richtlinien | 7,9 |
| 30 Tools, Inventar (bekannte Definitionen) | 13,2 |
| 30 Tools, Inventar und 6 Richtlinien | 18,0 |

Zum Vergleich: Schon das Dekodieren eines solchen Bodys von rund 40 KB kostet ein Vielfaches.

## Grenzen {#grenzen}

- Tool-Ergebnisse in der Anfrage und Aufrufe über das [MCP-Gateway](mcp-gateway.html) prüft
  dieser Baustein nicht – dafür sind Guardrails bzw. MCP-Freigaben zuständig.
- Mehrere Clients mit demselben Key teilen sich einen Inventareintrag.
- Automatisches Sperren wirkt ab dem nächsten Snapshot; Anfragen im selben Schreibintervall gehen
  noch durch.
