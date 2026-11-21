title: Start
summary: ai-gw – quelloffenes, selbst gehostetes AI-Gateway in Rust. Ein OpenAI- und Anthropic-kompatibler Endpunkt vor vielen KI-Anbietern, mit Routing, Mandanten, Budgets, Guardrails, MCP-Gateway und Admin-UI in einem Binary.
hero: ja
---
::: html
<section class="hero" aria-labelledby="hero-titel">
  <div class="wrap hero-grid">
    <div>
      <p class="eyebrow">Open Source · Rust · AGPL-3.0 · Vorabversion</p>
      <h1 id="hero-titel">Ein Endpunkt.<br><span class="hl">Alle Modelle.</span></h1>
      <p class="lead"><strong>ai-gw</strong> ist ein selbst gehostetes AI-Gateway: Anwendungen und Agenten sprechen eine OpenAI- oder Anthropic-kompatible API, ai-gw verteilt die Anfragen auf OpenAI, Azure OpenAI, Anthropic, AWS Bedrock, Gemini, Mistral, Ollama, vLLM und weitere – mit Schlüsseln je Team, Limits, Budgets, Guardrails und vollständigem Log. Gateway, Admin-API und Admin-UI stecken in einem Binary.</p>
      <div class="buttons">
        <a class="btn primary" href="schnellstart.html">Schnellstart</a>
        <a class="btn" href="funktionen.html">Was ai-gw kann</a>
        <a class="btn" href="https://github.com/mupf-dev/ai-gw" rel="noopener">Quellcode</a>
      </div>
      <ol class="flow" aria-label="Weg einer Anfrage in Kurzform">
        <li><b>Anfrage</b></li><li>Key prüfen</li><li>Limits</li><li>Guardrails</li><li>Routing</li><li><b>Anbieter</b></li>
      </ol>
    </div>
    <div class="hero-art">
      <svg class="art" viewBox="0 0 520 400" role="img" aria-labelledby="art-t art-d">
        <title id="art-t">Anwendungen sprechen über ai-gw mit vielen KI-Anbietern</title>
        <desc id="art-d">Links eine Chat-Anwendung, ein KI-Agent und ein MCP-Client. Sie sind mit dem Gateway ai-gw in der Mitte verbunden, das nacheinander Anmeldung, Limits und Budgets, Guardrails, Cache, Routing und Protokollierung ausführt. Rechts ist das Gateway mit OpenAI, Anthropic, Azure OpenAI, AWS Bedrock, Vertex AI und lokalen Modellen über Ollama oder vLLM verbunden.</desc>
        <circle class="ring" cx="255" cy="200" r="118" style="transform-origin: 255px 200px"/>
        <!-- Clients -->
        <rect class="dev" x="8" y="80" width="124" height="52" rx="6"/><text class="t-strong" x="20" y="102">Chat-App</text><text x="20" y="120">OpenAI-SDK</text>
        <rect class="dev" x="8" y="174" width="124" height="52" rx="6"/><text class="t-strong" x="20" y="196">KI-Agent</text><text x="20" y="214">Key oder Agent-ID</text>
        <rect class="dev" x="8" y="268" width="124" height="52" rx="6"/><text class="t-strong" x="20" y="290">MCP-Client</text><text x="20" y="308">IDE · /mcp</text>
        <path class="wire" d="M132 106 C156 106 156 150 180 150"/><path class="wire" d="M132 200 H180"/><path class="wire" d="M132 294 C156 294 156 250 180 250"/>
        <path class="pulse" d="M132 106 C156 106 156 150 180 150"/><path class="pulse p2" d="M132 200 H180"/><path class="pulse p3" d="M132 294 C156 294 156 250 180 250"/>
        <!-- Gateway -->
        <g class="float">
          <rect class="cloud" x="180" y="62" width="150" height="276" rx="10"/>
          <text class="t-strong" x="255" y="86" text-anchor="middle">ai-gw</text>
          <rect class="dev-2" x="192" y="98" width="126" height="30" rx="4"/><text x="255" y="117" text-anchor="middle">Auth · Key · JWT</text>
          <rect class="dev-2" x="192" y="136" width="126" height="30" rx="4"/><text x="255" y="155" text-anchor="middle">Limits · Budgets</text>
          <rect class="dev-2" x="192" y="174" width="126" height="30" rx="4"/><text x="255" y="193" text-anchor="middle">Guardrails</text>
          <rect class="dev-2" x="192" y="212" width="126" height="30" rx="4"/><text x="255" y="231" text-anchor="middle">Cache</text>
          <rect class="dev-2" x="192" y="250" width="126" height="30" rx="4"/><text x="255" y="269" text-anchor="middle">Routing · Fallback</text>
          <rect class="dev-2" x="192" y="288" width="126" height="30" rx="4"/><text x="255" y="307" text-anchor="middle">Log · Metriken</text>
        </g>
        <!-- Anbieter -->
        <path class="wire" d="M330 200 C356 200 354 74 380 74"/><path class="wire" d="M330 200 C356 200 354 124 380 124"/><path class="wire" d="M330 200 C356 200 354 174 380 174"/>
        <path class="wire" d="M330 200 C356 200 354 224 380 224"/><path class="wire" d="M330 200 C356 200 354 274 380 274"/><path class="wire" d="M330 200 C356 200 354 324 380 324"/>
        <path class="pulse" d="M330 200 C356 200 354 74 380 74"/><path class="pulse p2" d="M330 200 C356 200 354 174 380 174"/><path class="pulse p3" d="M330 200 C356 200 354 274 380 274"/><path class="pulse p4" d="M330 200 C356 200 354 324 380 324"/>
        <rect class="dev" x="380" y="56" width="132" height="36" rx="5"/><text class="t-strong" x="392" y="79">OpenAI</text><circle class="led" cx="500" cy="74" r="3.5"/>
        <rect class="dev" x="380" y="106" width="132" height="36" rx="5"/><text class="t-strong" x="392" y="129">Anthropic</text><circle class="led l2" cx="500" cy="124" r="3.5"/>
        <rect class="dev" x="380" y="156" width="132" height="36" rx="5"/><text class="t-strong" x="392" y="179">Azure OpenAI</text><circle class="led l3" cx="500" cy="174" r="3.5"/>
        <rect class="dev" x="380" y="206" width="132" height="36" rx="5"/><text class="t-strong" x="392" y="229">AWS Bedrock</text><circle class="led l4" cx="500" cy="224" r="3.5"/>
        <rect class="dev" x="380" y="256" width="132" height="36" rx="5"/><text class="t-strong" x="392" y="279">Vertex · Gemini</text><circle class="led" cx="500" cy="274" r="3.5"/>
        <rect class="dev" x="380" y="306" width="132" height="36" rx="5"/><text class="t-strong" x="392" y="329">Ollama · vLLM</text><circle class="led l2" cx="500" cy="324" r="3.5"/>
        <text x="446" y="366" text-anchor="middle">und weitere</text>
      </svg>
    </div>
  </div>
</section>

<div class="wrap stats-band">
  <ul class="stats" aria-label="Eckdaten">
    <li><span class="ico" aria-hidden="true"><svg viewBox="0 0 24 24"><circle cx="12" cy="13" r="8"/><path d="M12 9v4l2.5 2.5M9 2h6"/></svg></span><div><b>≈ 0,3 ms</b><span>Aufschlag je Anfrage (Median, im Container gemessen)</span></div></li>
    <li><span class="ico" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M4 20V14M9.3 20V10M14.6 20V7M20 20V3"/></svg></span><div><b>&gt; 16.000 req/s</b><span>JSON-Anfragen auf zwei CPU-Kernen, fehlerfrei bis 500 Verbindungen</span></div></li>
    <li><span class="ico" aria-hidden="true"><svg viewBox="0 0 24 24"><rect x="4" y="6" width="16" height="12" rx="1"/><path d="M8 6V3M12 6V3M16 6V3M8 21v-3M12 21v-3M16 21v-3"/></svg></span><div><b>≈ 35 MiB</b><span>Speicher im Leerlauf, Start in unter einer Sekunde</span></div></li>
    <li><span class="ico" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M12 3l8 4.5v9L12 21l-8-4.5v-9z"/><path d="M12 12l8-4.5M12 12v9M12 12L4 7.5"/></svg></span><div><b>1 Binary</b><span>Gateway, Admin-API und Admin-UI; SQLite oder Postgres</span></div></li>
  </ul>
</div>

<section class="section" aria-labelledby="funktionen-kurz">
  <div class="wrap">
    <div class="section-head">
      <p class="eyebrow">Funktionen</p>
      <h2 id="funktionen-kurz">Alles, was zwischen Anwendung und Modell gehört.</h2>
      <p>Wer KI-Modelle in mehreren Teams einsetzt, braucht Schlüsselverwaltung, Kostenkontrolle, Ausfallsicherheit, Schutz vor Datenabfluss und Nachvollziehbarkeit. ai-gw bündelt das an einer Stelle – im eigenen Netz und unter eigener Kontrolle.</p>
    </div>
    <ul class="features">
      <li><span class="ico" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M8 8l-4 4 4 4M16 8l4 4-4 4M14 5l-4 14"/></svg></span><h3>Ein Format, viele Anbieter</h3><p>OpenAI- und Anthropic-kompatible Endpunkte für Chat, Responses, Embeddings, Bilder und Audio. Übersetzung über eine gemeinsame Zwischendarstellung – inklusive Tools, Vision und Streaming.</p></li>
      <li><span class="ico" aria-hidden="true"><svg viewBox="0 0 24 24"><circle cx="6" cy="6" r="2"/><circle cx="6" cy="18" r="2"/><circle cx="18" cy="12" r="2"/><path d="M8 6h3a3 3 0 0 1 3 3v0a3 3 0 0 0 2 2.8M8 18h3a3 3 0 0 0 3-3v0a3 3 0 0 1 2-2.8"/></svg></span><h3>Routing und Resilienz</h3><p>Modellgruppen mit Aliasen, gewichtete Verteilung, geringste Latenz oder Last, Prioritäten (z. B. reservierte Kapazität zuerst), Retries, Fallback-Ketten und Circuit Breaker.</p></li>
      <li><span class="ico" aria-hidden="true"><svg viewBox="0 0 24 24"><circle cx="9" cy="8" r="3"/><path d="M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6M16 4a3 3 0 0 1 0 6M18 14c2 .7 3 2.8 3 6"/></svg></span><h3>Mandanten, Limits, Budgets</h3><p>Organisationen, Teams und virtuelle API-Keys mit Modellfreigaben, Anfrage- und Token-Limits, Budgets mit Warnschwellen und Kosten je Modell, Team und Key.</p></li>
      <li><span class="ico" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/><path d="M9 12l2 2 4-4"/></svg></span><h3>Guardrails</h3><p>PII-Erkennung und -Maskierung, Prompt-Injection-Heuristik, Wort- und Regex-Regeln, Canary-Token gegen System-Prompt-Lecks, Link-Schutz, Sprachfilter und externe Inhaltsprüfung.</p></li>
      <li><span class="ico" aria-hidden="true"><svg viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="8.5" y="14" width="7" height="7" rx="1"/><path d="M6.5 10v2h11v-2M12 12v2"/></svg></span><h3>MCP-Gateway und Tool-Richtlinien</h3><p>MCP-Server hinter einem Endpunkt, Freigaben je Team und Key bis auf Tool-Ebene, Inventar aller Tools, die Anwendungen mitschicken, und Richtlinien gegen riskante Tools.</p></li>
      <li><span class="ico" aria-hidden="true"><svg viewBox="0 0 24 24"><rect x="5" y="11" width="14" height="10" rx="1"/><path d="M8 11V7a4 4 0 0 1 8 0v4M12 15v2"/></svg></span><h3>Agent-Identitäten</h3><p>KI-Agenten melden sich mit signierten Access-Tokens an, etwa aus Microsoft Entra Agent ID – ohne verteilten Gateway-Key. Es gelten dieselben Regeln wie für den zugeordneten Key.</p></li>
      <li><span class="ico" aria-hidden="true"><svg viewBox="0 0 24 24"><ellipse cx="12" cy="6" rx="7" ry="3"/><path d="M5 6v12c0 1.7 3.1 3 7 3s7-1.3 7-3V6M5 12c0 1.7 3.1 3 7 3s7-1.3 7-3"/></svg></span><h3>Antwort-Cache</h3><p>Exakter Cache im Speicher oder in Redis, semantischer Cache mit eigenem HNSW-Index, pgvector oder Redis Search – immer getrennt je Team.</p></li>
      <li><span class="ico" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M3 12h4l3-8 4 16 3-8h4"/></svg></span><h3>Beobachtung und GitOps</h3><p>Request-Log mit Kosten, Prometheus-Metriken, OpenTelemetry-Traces, Audit-Log mit Hash-Kette und deklarative Konfiguration als YAML mit Diff und Trockenlauf.</p></li>
    </ul>
    <p class="note">Ausführlich: <a href="funktionen.html">Funktionsumfang</a> · <a href="sicherheit.html">Guardrails &amp; Sicherheit</a> · <a href="doku/index.html">Dokumentation</a>.</p>
  </div>
</section>

<section class="section alt" aria-labelledby="oberflaeche-kurz">
  <div class="wrap split">
    <div>
      <p class="eyebrow">Admin-UI</p>
      <h2 id="oberflaeche-kurz" class="h2-plain">Verkehr, Kosten und Zustand auf einen Blick.</h2>
      <p class="muted-lead">Die Admin-Oberfläche ist in das Binary eingebettet. Sie zeigt Anfragen, Tokens, Kosten, Latenz, Fehler und Cache-Treffer je Team und Modell, verwaltet Modelle, Keys, Guardrails und MCP-Server und folgt hell/dunkel der Systemeinstellung.</p>
      <ul class="checks">
        <li><strong>Log-Explorer</strong> mit Fallback-Versuchen, Cache-Treffern und Kosten je Anfrage</li>
        <li><strong>Playground</strong> im Namen eines Keys – mit dessen Limits und Guardrails</li>
        <li><strong>Guardrail-Profile</strong> (Basis, Streng, Offen) mit Diff vor dem Anwenden</li>
        <li><strong>YAML-Import/-Export</strong> mit Trockenlauf, Anmeldung per OIDC, Rollen</li>
      </ul>
      <p class="note">Weitere Aufnahmen: <a href="oberflaeche.html">Die Oberfläche</a>.</p>
    </div>
    <figure class="shot">
      <picture>
        <source media="(prefers-color-scheme: dark)" srcset="assets/img/ui/uebersicht-dunkel.webp" width="1200" height="1307">
        <img src="assets/img/ui/uebersicht-hell.webp" width="1200" height="1307" loading="lazy" decoding="async" alt="Übersicht der Admin-UI für die fiktive Organisation Acme GmbH: 2,6 Millionen Requests, 2,5 Milliarden Tokens, Kosten, p95-Latenz, Fehlerquote 0,8 Prozent und Cache-Trefferquote 26,8 Prozent in 24 Stunden, darunter Verlauf, Top-Modellgruppen und Verkehrsanteile der Anbieter.">
      </picture>
      <figcaption>Übersicht – echte Oberfläche, fiktive Beispieldaten.</figcaption>
    </figure>
  </div>
</section>

<section class="section" aria-labelledby="ablauf">
  <div class="wrap">
    <div class="section-head">
      <p class="eyebrow">So läuft eine Anfrage</p>
      <h2 id="ablauf">Alles aus dem Speicher – keine Datenbank im heißen Pfad.</h2>
      <p>Schlüssel, Freigaben, Limits und Plugin-Ketten liegen als unveränderlicher Konfigurations-Snapshot im RAM. Änderungen werden in unter einer Sekunde auf allen Instanzen wirksam; fällt die Datenbank aus, läuft der Gateway mit dem letzten Stand weiter.</p>
    </div>
    <ol class="steps">
      <li><h3>Anmelden</h3><p>API-Key (nur als Hash gespeichert) oder signiertes Token eines Agenten. Ergebnis: Organisation, Team, Freigaben und Limits.</p></li>
      <li><h3>Prüfen</h3><p>Modellfreigabe, Tool-Richtlinien, Limits und Budgets werden reserviert; Guardrails prüfen und maskieren den Prompt.</p></li>
      <li><h3>Weiterleiten</h3><p>Cache-Treffer antworten sofort. Sonst wählt das Routing ein Deployment, übersetzt ins Anbieterformat und streamt Chunk für Chunk zurück.</p></li>
      <li><h3>Abrechnen</h3><p>Usage gleicht die Reservierung aus, Kosten werden fortgeschrieben, das Log-Ereignis geht nicht blockierend in den Batch-Writer.</p></li>
    </ol>
    <p class="note">Details: <a href="architektur.html">Architektur</a> · Messwerte: <a href="doku/leistung.html">Leistung und Lastvergleich</a>.</p>
  </div>
</section>

<section class="section alt" aria-labelledby="anbieter">
  <div class="wrap">
    <div class="section-head">
      <p class="eyebrow">Anbieter</p>
      <h2 id="anbieter">Eigene Zugangsdaten, eigene Verträge.</h2>
      <p>ai-gw ruft die Anbieter mit den hinterlegten Zugangsdaten des Betreibers auf. Geheimnisse liegen verschlüsselt (AES-256-GCM) in der Datenbank oder werden aus Umgebung und Dateien gelesen.</p>
    </div>
    <div class="svc">
      <div class="table-wrap"><table>
        <caption class="sr-only">Unterstützte Anbieter und Anmeldearten</caption>
        <thead><tr><th scope="col">Anbieter</th><th scope="col">Anmeldung</th></tr></thead>
        <tbody>
          <tr><td>OpenAI</td><td>API-Key</td></tr>
          <tr><td>Azure OpenAI, Claude in Azure AI Foundry</td><td>API-Key oder Microsoft Entra ID (Client-Secret, Zertifikat, Workload Identity, Managed Identity)</td></tr>
          <tr><td>Anthropic</td><td>API-Key</td></tr>
          <tr><td>AWS Bedrock</td><td>SigV4 oder API-Key</td></tr>
          <tr><td>Google Gemini API, Vertex AI</td><td>API-Key bzw. Service-Account</td></tr>
          <tr><td>Mistral</td><td>API-Key</td></tr>
          <tr><td>Ollama, vLLM, OpenAI-kompatible Endpunkte</td><td>optional API-Key; private Adressen nur nach ausdrücklicher Freigabe</td></tr>
        </tbody>
      </table></div>
    </div>
  </div>
</section>

<section class="section cta" aria-labelledby="start-cta">
  <div class="wrap">
    <div>
      <p class="eyebrow">Ausprobieren</p>
      <h2 id="start-cta">In fünf Minuten zum ersten Request.</h2>
      <p>Image bauen, Master-Key erzeugen, Container starten – die Admin-UI führt durch Organisation, Zugangsdaten, Modellgruppe und API-Key. Alternativ alles als YAML anwenden.</p>
      <div class="buttons">
        <a class="btn primary" href="schnellstart.html">Schnellstart</a>
        <a class="btn" href="https://github.com/mupf-dev/ai-gw" rel="noopener">Repository auf GitHub</a>
        <a class="btn" href="mitmachen.html">Mitmachen</a>
      </div>
    </div>
    <div class="status">
      <p><span class="tag">Projektstand · November 2026</span></p>
      <p>Der Funktionsumfang der ersten Version (0.1) ist umgesetzt und getestet; das erste Release mit fertigen Container-Images steht noch aus. Bis 1.0 können sich Konfiguration und Admin-API inkompatibel ändern.</p>
      <p><a href="roadmap.html">Status &amp; Roadmap</a></p>
    </div>
  </div>
</section>
:::
