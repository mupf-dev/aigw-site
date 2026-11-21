#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 ai-gw contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Website von ai-gw (AI-Gateway) – Angaben der Website; der Generator ist der gemeinsame Kern site-kit (kit/sitekit.py).

Aufruf:  python3 build.py            # baut nach docs/
         python3 build.py --out DIR  # anderes Zielverzeichnis
Aufbau der Inhalte, Kopffelder und Prüfungen: README.md und tools/INHALTSREGELN.md.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "kit"))
import sitekit  # noqa: E402  (Kopie aus site-kit, siehe kit/README.md)

SITE_NAME = "ai-gw"
SITE_SHORT = "AI-Gateway"
# Öffentliche Adresse (nur für Open-Graph-Angaben; alle Links der Seiten bleiben relativ)
SITE_URL = "https://mupf-dev.github.io/aigw-site/"
REPO_URL = "https://github.com/mupf-dev/ai-gw"
# Pfad der Website auf dem Server (nur für die 404-Seite, die GitHub Pages unter beliebigen Pfaden ausliefert).
# hreflang-/canonical-Links sind relativ, damit die Website ohne festen Host funktioniert.
BASE_PATH = "/aigw-site/"

LANGS = {
    "de": {
        "dir": "",
        "docs": "doku",
        "search": "suche.html",
        "index_json": "suche-index.json",
        "nav": [
            ("index.html", "Start"),
            ("funktionen.html", "Funktionen"),
            ("oberflaeche.html", "Oberfläche"),
            ("architektur.html", "Architektur"),
            ("sicherheit.html", "Sicherheit"),
            ("doku/index.html", "Doku"),
            ("schnellstart.html", "Schnellstart"),
            ("roadmap.html", "Roadmap"),
            ("mitmachen.html", "Mitmachen"),
        ],
        "groups": [("konzept", "Konzepte"), ("betrieb", "Betrieb und Messwerte")],
        "t": {
            "skip": "Zum Inhalt springen", "menu": "Menü", "mainnav": "Hauptnavigation",
            "search": "Suche", "search_ph": "Suchen …", "home_label": "Startseite",
            "toc_label": "Inhalt dieser Seite", "toc_title": "Auf dieser Seite",
            "anchor": "Link zu diesem Abschnitt", "crumbs": "Brotkrumen", "start": "Start",
            "docs": "Dokumentation", "pager": "Weitere Seiten", "source": "Aufbereitet aus",
            "switch": "English", "switch_short": "EN", "switch_label": "English version of this page",
            "tagline": "Quelloffenes, selbst gehostetes AI-Gateway in Rust – ein Endpunkt für viele KI-Anbieter.",
            "og_title": "ai-gw – Selbst gehostetes AI-Gateway",
            "foot_license": 'Dokumentation unter <a href="https://creativecommons.org/licenses/by/4.0/deed.de" rel="license noopener">CC BY 4.0</a>, Code unter AGPL-3.0-or-later. Keine Cookies, kein Tracking, keine externen Ressourcen.',
            "foot_links": [("mitmachen.html#lizenz", "Lizenz"), ("mitmachen.html#sicherheit", "Sicherheitslücke melden"), (REPO_URL, "Quellcode"),
                           ("suche.html", "Suche"), ("impressum.html", "Impressum"), ("datenschutz.html", "Datenschutz")],
            "foot_nav": "Rechtliches und Service",
            "prefix_note": "Ein Binary für Gateway, Admin-API und Admin-UI.",
            "docs_lead": "Aufbereitete Fassungen der Konzepte und des Betriebshandbuchs von ai-gw. Die vollständigen Dokumente liegen im Repository unter <code>docs/</code>.",
            "docs_desc": "Konzepte, Betrieb und Messwerte von ai-gw (AI-Gateway).",
            "docs_index_s": "Übersicht aller Konzepte und Betriebsthemen",
            "pages": "Seiten",
            "search_label": "Suchbegriff", "search_btn": "Suchen", "search_desc": "Volltextsuche",
            "search_noscript": 'Die Suche benötigt JavaScript. Alternativ: <a href="doku/index.html">Dokumentationsübersicht</a>.',
            "nf_title": "Seite nicht gefunden",
        },
    },
    "en": {
        "dir": "en/",
        "docs": "docs",
        "search": "search.html",
        "index_json": "search-index.json",
        "nav": [
            ("index.html", "Home"),
            ("features.html", "Features"),
            ("admin-ui.html", "Admin UI"),
            ("architecture.html", "Architecture"),
            ("security.html", "Security"),
            ("docs/index.html", "Docs"),
            ("quickstart.html", "Quickstart"),
            ("roadmap.html", "Roadmap"),
            ("contribute.html", "Contribute"),
        ],
        "groups": [("konzept", "Concepts"), ("betrieb", "Operations and measurements")],
        "t": {
            "skip": "Skip to content", "menu": "Menu", "mainnav": "Main navigation",
            "search": "Search", "search_ph": "Search …", "home_label": "Home",
            "toc_label": "Contents of this page", "toc_title": "On this page",
            "anchor": "Link to this section", "crumbs": "Breadcrumb", "start": "Home",
            "docs": "Docs", "pager": "More pages", "source": "Adapted from",
            "switch": "Deutsch", "switch_short": "DE", "switch_label": "Deutsche Fassung dieser Seite",
            "tagline": "Open-source, self-hosted AI gateway in Rust – one endpoint for many AI providers.",
            "og_title": "ai-gw – Self-hosted AI gateway",
            "foot_license": 'Documentation under <a href="https://creativecommons.org/licenses/by/4.0/deed.en" rel="license noopener">CC BY 4.0</a>, code under AGPL-3.0-or-later. No cookies, no tracking, no third-party resources.',
            "foot_links": [("contribute.html#license", "License"), ("contribute.html#security", "Report a vulnerability"), (REPO_URL, "Source code"),
                           ("search.html", "Search"), ("legal-notice.html", "Legal notice"), ("privacy.html", "Privacy policy")],
            "foot_nav": "Legal and service",
            "prefix_note": "One binary for gateway, admin API and admin UI.",
            "docs_lead": "Condensed public editions of ai-gw's concept documents and operations handbook. The full documents (German) live in the repository under <code>docs/</code>.",
            "docs_desc": "Concepts, operations and measurements of ai-gw (AI gateway).",
            "docs_index_s": "Overview of all concepts and operations topics",
            "pages": "Pages",
            "search_label": "Search term", "search_btn": "Search", "search_desc": "Full-text search",
            "search_noscript": 'Search needs JavaScript. Alternatively, browse the <a href="docs/index.html">documentation overview</a>.',
            "nf_title": "Page not found",
        },
    },
}

LOGO_SVG = (
    '<svg class="logo" viewBox="0 0 32 32" width="28" height="28" aria-hidden="true" focusable="false">'
    '<rect width="32" height="32" rx="6" class="logo-bg"/>'
    '<path d="M9.5 25V15a6.5 6.5 0 0 1 13 0v10" class="logo-cloud" stroke-linecap="round"/>'
    '<path d="M4 11h4M4 16h4M24 16h4M24 11h4" class="logo-wire" stroke-linecap="round"/>'
    '<g class="logo-dots"><circle cx="16" cy="17" r="2.2"/></g></svg>'
)

# Umbruchstellen der Kopfzeile (px): kompakt, enger, Menü-Schalter – abhängig von der Länge der Navigation
NAV_BREAKPOINTS = (1320, 1220, 1140)

sitekit.configure(
    root=ROOT, site_name=SITE_NAME, site_short=SITE_SHORT, base_path=BASE_PATH,
    site_url=SITE_URL,
    og_image="assets/img/ui/uebersicht-dunkel.webp",
    nav_breakpoints=NAV_BREAKPOINTS, langs=LANGS, logo_svg=LOGO_SVG,
)

if __name__ == "__main__":
    sys.exit(sitekit.run())
