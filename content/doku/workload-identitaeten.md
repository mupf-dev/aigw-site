title: Workload- und Agent-Identitäten
summary: KI-Agenten und Dienste melden sich mit signierten Access-Tokens an – vor allem aus Microsoft Entra Agent ID – statt mit einem verteilten Gateway-Key. Das Token wirkt genau wie der Key, dem die Identität zugeordnet ist.
group: konzept
order: 40
quelle: Konzept 18 „Workload- und Agent-Identitäten“
---
Virtuelle API-Keys sind einfach, müssen aber verteilt, sicher abgelegt und rotiert werden. Für
KI-Agenten und Dienste mit eigener Identität ist das unnötig: Sie können bei ihrem
Identitätsanbieter ein kurzlebiges Access-Token holen. ai-gw nimmt solche **signierten Tokens
(JWT)** auf der Datenebene – OpenAI- und Anthropic-Eingang, Embeddings, Bilder, Audio,
Modell-Liste – und im MCP-Gateway als `Authorization: Bearer …` an.

Hauptfall ist **Microsoft Entra Agent ID**: KI-Agenten mit eigener Entra-Identität melden sich
ohne Gateway-Key an. Dasselbe Verfahren trägt allgemein für Workload-Identitäten wie Service
Principals, Managed Identities oder andere OAuth-2.0-Aussteller.

```text
Agent ──Client Credentials / On-Behalf-Of──► Entra ID: Token für die Gateway-API
  └─ Authorization: Bearer eyJ… ─► ai-gw
        1. Signatur, Aussteller, Zielgruppe, Laufzeit, Tenant, ggf. Rolle/Scope prüfen
        2. (Aussteller, Kennung) → zugeordneter API-Key
        3. ab hier wie mit dem Key: Freigaben, Limits, Budgets, Guardrails, Tools, MCP
  Anbieter: nur die Zugangsdaten des Deployments – nie das Token
```

## Konfiguration der Aussteller {#aussteller}

Vertrauenswürdige Aussteller stehen in der Startkonfiguration des Betreibers, nicht in der
Admin-API:

```yaml
auth:
  jwt:
    issuers:
      - name: entra-prod
        profile: entra                         # generic | entra
        tenant_id: "<tenant-guid>"
        audiences: ["api://ai-gw", "<client-id-des-gateways>"]
        required_roles: [Gateway.Invoke]       # optional
        # required_scopes: [access_as_user]    # optional, für delegierte Tokens
        # require_agent: true                  # nur Agent-Identitäten
```

Das Profil `entra` leitet Aussteller (Token-Version 1 und 2) und Schlüsselquelle aus der
Tenant-ID ab. Generische Aussteller nennen ihre Schlüsselquelle fest oder per
OpenID-Discovery.

## Zuordnung zu Keys {#zuordnung}

Statt einer neuen Ressourcenart erweitert ai-gw den **virtuellen Key**: Ein Key trägt eine Liste
von Identitäten aus Aussteller und Kennung (standardmäßig die App-ID der Agent-Identität). Ein
Token mit passender Kombination wirkt **genau wie dieser Key** – Modellfreigaben, Limits,
Budgets, Team und Organisation, Guardrail-Bindungen, Tool-Richtlinien, MCP-Freigaben,
Payload-Richtlinie und Zuordnung im Request-Log gelten ohne Sonderlogik.

- Jede Identität gehört höchstens zu **einem** aktiven Key; Admin-API und GitOps prüfen das.
- Unbekannte Identitäten werden abgelehnt (`403`) – es gibt **kein automatisches Anlegen**. Die
  Microsoft-Dokumentation rät ausdrücklich davon ab, allein wegen eines Agent-Claims zu
  autorisieren.
- Ein Key kann mehrere Identitäten tragen, etwa alle Instanzen eines Agenten; sie teilen sich
  dann Limits und Budgets.
- Gesperrte oder abgelaufene Keys sperren auch die Token-Anmeldung; beim Rotieren eines Keys
  ziehen die Identitäten mit um.

## Prüfung {#pruefung}

- Ein Bearer-Wert im JWT-Format wird als Token behandelt, alles andere als API-Key; virtuelle
  Keys enthalten nie Punkte.
- Größenlimit vor jeder Auswertung; nur **RS256 und ES256**. `none`, symmetrische Verfahren und
  kritische Header-Erweiterungen werden nie angenommen, Schlüssel nie aus Token-Angaben
  nachgeladen – nur aus der konfigurierten Quelle.
- Signaturprüfung mit aws-lc-rs, keine eigene Kryptografie. Aussteller exakt, Zielgruppe aus der
  Liste, Ablauf Pflicht, Uhrenabweichung konfigurierbar, bei Entra zusätzlich der Tenant.
- Schlüsselsätze werden über den gemeinsamen Baustein für ausgehende Verbindungen geladen (nur
  HTTPS, keine Weiterleitungen, Größen- und Zeitlimits), zwischengespeichert und bei unbekannter
  Schlüssel-ID gedrosselt neu geladen. Ist der Aussteller nicht erreichbar, bleiben die bekannten
  Schlüssel in Gebrauch.
- Geprüfte Tokens liegen bis zu ihrem Ablauf in einem begrenzten Cache; die Zuordnung zum Key
  läuft trotzdem bei jeder Anfrage gegen den aktuellen Konfigurations-Snapshot.

Der OIDC-Login der Admin-UI nutzt dieselben Prüfbausteine.

## Nachvollziehbarkeit {#attribution}

Das Request-Log hält fest, wer angefragt hat: Aussteller, Kennung, Art (Anwendung, delegiert,
Agent-Nutzerkonto), ob es eine Agent-Identität ist, bei delegierten Tokens den Nutzer und den
Blueprint des Agenten – nie das Token selbst. Die Nutzerkennung sehen nur Admins und Auditoren.
Traces und OpenTelemetry-Logs tragen Aussteller, Kennung und Art. Metrik-Labels je Agent gibt es
bewusst nicht, weil die Zahl der Identitäten unbegrenzt ist.

## Sicherheit und Grenzen {#grenzen}

- **Tokens gehen nie an Anbieter:** Ausgehende Anfragen werden aus den Zugangsdaten des
  Deployments bzw. MCP-Servers gebaut; eingehende Header werden nicht durchgereicht.
- **Widerruf:** Tokens sind bis zu ihrem Ablauf gültig; ai-gw fragt beim Aussteller keinen
  Widerruf ab. Sofort wirksam ist, die Identität vom Key zu entfernen oder den Key zu sperren.
- **Tenant-weite Tokens:** Ohne Rollen- oder Scope-Pflicht kann jede Anwendung des Tenants ein
  Token für die Gateway-API holen – zugeordnet werden aber nur eingetragene Identitäten.
  Empfehlung: eine App-Rolle (z. B. `Gateway.Invoke`) definieren, Zuweisung erzwingen und
  `required_roles` setzen.
- Fehlerantworten verraten keine Details (`401` bzw. `403`); Gründe stehen ohne Token im
  Debug-Log.

In der Admin-UI werden Identitäten am Key gepflegt; angeboten werden nur konfigurierte
Aussteller. Siehe auch [MCP-Gateway](mcp-gateway.html) und
[Guardrails & Sicherheit](../sicherheit.html).
