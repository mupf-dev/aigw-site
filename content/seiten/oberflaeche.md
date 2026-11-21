title: Die Oberfläche
summary: Aufnahmen der Admin-UI von ai-gw – Übersicht, Modellgruppen und Routing, Keys, Log-Explorer, Guardrail-Profile, YAML-Import, Audit-Log und Befehlspalette.
wide: ja
---
::: html
<p class="shot-intro">Die Admin-UI ist eine Svelte-5-Anwendung, die fest in das Binary eingebettet ist und von der Steuerebene (Standard-Port 4001, Pfad <code>/admin/</code>) ausgeliefert wird. Sie nutzt ausschließlich die öffentliche Admin-API – alles, was hier zu sehen ist, geht auch per API oder als YAML. Die Aufnahmen stammen aus der echten Oberfläche; Organisationen, Teams, Keys und Zahlen sind fiktive Beispiel- oder Testdaten.</p>
:::

> **Vorabversion – die Oberfläche kann sich ändern.** Die Aufnahmen zeigen den Entwicklungsstand vom November 2026. Die Oberfläche ist derzeit deutschsprachig.

## Übersicht {#uebersicht}

Requests, Tokens, Kosten, p95-Latenz, Fehlerquote und Cache-Treffer im gewählten Zeitraum, darunter Verlauf, Top-Modellgruppen, Verkehrsanteil und Zustand der Anbieter sowie die letzten Fehler.

::: html
<figure class="shot">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/img/ui/uebersicht-dunkel.webp" width="1200" height="1307">
    <img src="assets/img/ui/uebersicht-hell.webp" width="1200" height="1307" loading="lazy" decoding="async" alt="Übersicht der fiktiven Organisation Acme GmbH mit Kennzahlen für 24 Stunden, Verlaufsdiagramm der Requests, Tabelle der Top-Modellgruppen mit Requests, Tokens, Kosten und p95-Latenz, Verkehrsanteilen von Azure OpenAI, OpenAI, Anthropic, vLLM, AWS Bedrock, Mistral und Vertex AI sowie einer Liste der letzten Fehler.">
  </picture>
  <figcaption>Übersicht – folgt hell/dunkel der Systemeinstellung, genau wie diese Seite.</figcaption>
</figure>
:::

## Modellgruppen und Routing {#routing}

Eine Modellgruppe ist der öffentliche Modellname für die Clients. Dahinter stehen Deployments mit Priorität, Gewicht und Kapazität; Fallback-Kette, Wiederholungen und Circuit Breaker sind je Gruppe einstellbar.

::: html
<div class="shot-grid">
<figure class="shot">
  <img src="assets/img/ui/modellgruppe-dunkel.webp" width="1200" height="750" loading="lazy" decoding="async" alt="Detailseite der Modellgruppe gpt-4o im dunklen Modus: Strategie gewichtet, Fallback-Kette zu claude-sonnet bei Ratenlimit oder Nichtverfügbarkeit, Einstellungen für Wiederholungen und Circuit Breaker, zwei Deployments – Azure OpenAI mit Priorität 0 und OpenAI mit Priorität 1.">
  <figcaption>Modellgruppe mit zwei Deployments: reservierte Kapazität zuerst, Fallback auf ein anderes Modell.</figcaption>
</figure>
<figure class="shot">
  <img src="assets/img/ui/routing-hell.webp" width="1200" height="750" loading="lazy" decoding="async" alt="Dialog „Modellgruppe bearbeiten“ mit Routing-Strategie, Aliassen, Fähigkeiten Chat, Embeddings, Bilder, Transkription und Sprachausgabe, Fallback-Kette sowie Formular für Wiederholungen mit Versuchen, Backoff und Zeitbudget.">
  <figcaption>Routing-Einstellungen als Formular oder JSON – geprüft vom selben Parser wie die Datenebene.</figcaption>
</figure>
</div>
:::

## Keys {#keys}

Virtuelle API-Keys für Anwendungen, mit Team, freigegebenen Modellen, Budget, Ratenlimits, Ablauf und Status. Der Klartext wird nur beim Anlegen einmal angezeigt.

::: html
<figure class="shot">
  <img src="assets/img/ui/keys-hell.webp" width="1200" height="1268" loading="lazy" decoding="async" alt="Liste von 14 virtuellen Keys der fiktiven Acme GmbH, etwa ci-evals, contract-review und support-bot-prod, jeweils mit Team, freigegebenen Modellen, Monatsbudget, RPM- und TPM-Limits, Ablaufdatum, letzter Nutzung und Status aktiv, abgelaufen oder widerrufen.">
  <figcaption>Keys mit Budgets und Limits je Anwendung.</figcaption>
</figure>
:::

## Log-Explorer {#logs}

Alle Requests über das Gateway – mit Modell, Anbieter, Key, Tokens, Kosten, Latenz, Cache-Treffern und Fallback-Versuchen. Inhalte werden nur gespeichert, wenn es konfiguriert ist, und dann maskiert.

::: html
<figure class="shot">
  <img src="assets/img/ui/logs-hell.webp" width="1200" height="750" loading="lazy" decoding="async" alt="Log-Explorer mit Live-Ansicht: Kennzahlen zu Requests, Fehlerquote, p95-Latenz und Kosten, darunter eine Tabelle mit Zeit, Status, Modell und Anbieter, Key, Tokens, Kosten, Latenz und Cache-Status je Anfrage.">
  <figcaption>Log-Explorer mit Filtern nach Status, Modell und Cache.</figcaption>
</figure>
:::

## Guardrail-Profile {#guardrails}

Profile bündeln empfohlene Guardrail-Einstellungen. Vor dem Anwenden auf eine Organisation, ein Team, einen Key oder eine Modellgruppe zeigt die UI, welche Plugin-Bindungen entstehen oder sich ändern.

::: html
<figure class="shot">
  <img src="assets/img/ui/guardrail-profil-hell.webp" width="1200" height="750" loading="lazy" decoding="async" alt="Dialog „Profil Basis anwenden“ auf Ebene Team: der Diff zeigt zwei neue Plugin-Bindungen, prompt-filter und pii, im Hintergrund die Beschreibungen der Profile Basis, Streng und Offen.">
  <figcaption>Profil „Basis“ auf ein Team anwenden – erst Diff, dann Anwenden.</figcaption>
</figure>
:::

## YAML-Import und Audit {#gitops}

Konfiguration lässt sich als YAML-Manifeste exportieren und wieder anwenden – erst als Trockenlauf mit Diff, dann in einer Transaktion. Jede Änderung landet im Audit-Log, dessen Hash-Kette sich in der UI prüfen lässt.

::: html
<div class="shot-grid">
<figure class="shot">
  <img src="assets/img/ui/gitops-hell.webp" width="1200" height="750" loading="lazy" decoding="async" alt="YAML-Import mit Manifesten für eine Modellgruppe gpt-4o und ein Team legal; der Trockenlauf meldet eine Neuanlage und eine Änderung und zeigt den Diff der Aliasse und der Routing-Strategie.">
  <figcaption>Trockenlauf mit Diff vor dem Anwenden.</figcaption>
</figure>
<figure class="shot">
  <img src="assets/img/ui/audit-hell.webp" width="1200" height="750" loading="lazy" decoding="async" alt="Audit-Log mit der Meldung „Audit-Kette unversehrt – 50 Einträge geprüft“, Filtern nach Objektart, Aktion, Akteur und Zeitraum sowie Einträgen zum Anlegen, Sperren, Entsperren und Widerrufen von API-Keys.">
  <figcaption>Audit-Log mit geprüfter Hash-Kette (Testdaten).</figcaption>
</figure>
</div>
:::

## Befehlspalette {#befehlspalette}

Mit Strg+K springt man zu Seiten, Aktionen, Modellen oder Keys – ohne die Hand von der Tastatur zu nehmen.

::: html
<figure class="shot">
  <img src="assets/img/ui/befehlspalette-hell.webp" width="1200" height="750" loading="lazy" decoding="async" alt="Geöffnete Befehlspalette über der Übersicht mit Suchfeld „Seite, Aktion, Modell oder Key suchen“ und einer Liste der Seiten von Übersicht bis Logs.">
  <figcaption>Befehlspalette (Strg+K).</figcaption>
</figure>
:::
