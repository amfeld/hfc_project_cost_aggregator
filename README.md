# HFC Projekt Kosten Aggregator

Ein Odoo 18 Enterprise Modul zur Auswertung von Projektkosten und -umsätzen.

## Überblick

Dieses Modul bietet eine zentrale Übersicht über alle projektbezogenen finanziellen Kennzahlen. Es aggregiert Daten aus Ausgangsrechnungen, Eingangsrechnungen und der Zeiterfassung, um eine vollständige Kostenübersicht pro Projekt zu ermöglichen.

## Funktionen

### Aggregierte Datenauswertung

- **Ausgangsrechnungen (Umsatz)**
  - Anzahl der Rechnungen pro Projekt
  - Gesamter Rechnungsbetrag (Umsatz)
  - Offene Forderungen

- **Eingangsrechnungen (Kosten)**
  - Anzahl der Lieferantenrechnungen
  - Material- und Fremdkosten
  - Offene Verbindlichkeiten

- **Zeiterfassung (Personalkosten)**
  - Gebuchte Stunden pro Projekt
  - Kosten der gebuchten Stunden (Personalkosten)

### Automatische Berechnungen

- **Deckungsbeitrag**: Umsatz minus Gesamtkosten (Material + Personal)
- **Deckungsbeitrag %**: Prozentualer Anteil des Deckungsbeitrags am Umsatz
- Farbcodierung:
  - 🟢 Grün: DB > 20%
  - 🟡 Gelb: DB zwischen 0-20%
  - 🔴 Rot: DB < 0% (Verlust)

### Verschiedene Ansichten

1. **Listen-Ansicht (Tree View)**
   - Übersichtliche Tabelle mit allen Projekten
   - Summenzeilen für Gesamt-Auswertungen
   - Optional ein-/ausblendbare Spalten
   - Sortierung und Filterung möglich

2. **Pivot-Ansicht**
   - Mehrdimensionale Analyse
   - Flexible Gruppierung nach verschiedenen Kriterien
   - Export nach Excel möglich

3. **Diagramm-Ansicht (Graph View)**
   - Visuelle Darstellung als Balkendiagramm
   - Vergleich von Umsatz, Kosten und Deckungsbeitrag

## Voraussetzungen

### Odoo Module (Dependencies)

- `base` - Basis-Modul
- `account` - Rechnungswesen
- `analytic` - Analytische Buchführung
- `hr_timesheet` - Zeiterfassung

### Konfiguration in Odoo

1. **Analytische Buchführung muss aktiviert sein**
   - Einstellungen → Rechnungswesen → Analytische Buchführung

2. **Projekte als analytische Konten anlegen**
   - Rechnungswesen → Konfiguration → Analytische Pläne
   - Plan mit Name enthält "Projekt" erstellen
   - Analytische Konten (= Projekte) unter diesem Plan anlegen

3. **Rechnungen mit Projekten verknüpfen**
   - Bei Rechnungszeilen das Feld "Analytische Verteilung" ausfüllen
   - Projekt(e) auswählen und ggf. prozentuale Verteilung angeben

## Installation

### Methode 1: Über Kommandozeile

```bash
# Modul in Odoo Addons-Verzeichnis kopieren
cp -r hfc_project_cost_aggregator /pfad/zu/odoo/addons/

# Odoo mit Update-Parameter starten
odoo-bin -u hfc_project_cost_aggregator -d ihre_datenbank
```

### Methode 2: Über Odoo Benutzeroberfläche

1. Apps-Menü öffnen
2. "Apps-Liste aktualisieren" anklicken
3. Nach "HFC Projekt Kosten Aggregator" suchen
4. "Installieren" klicken

## Verwendung

Nach der Installation finden Sie das Modul im Hauptmenü:

```
Projektauswertung
└── Berichte
    └── Projekt Kostenübersicht
```

### Hinweise zur Datenqualität

- Nur **gebuchte** Rechnungen (`state = 'posted'`) werden berücksichtigt
- Nur Projekte mit **Aktivität** (Buchungen > 0) werden angezeigt
- Die analytische Verteilung wird prozentual berücksichtigt (bei 50% Zuordnung wird nur 50% des Betrags gezählt)

## Technische Details

### Datenmodell

- **Model Name**: `hfc.project.cost.aggregator`
- **Typ**: Read-only Model (`_auto = False`)
- **Datenbasis**: PostgreSQL View
- Die View wird bei der Modulinstallation automatisch erstellt

### Berechtigungen

- **Leserechte**: Alle internen Benutzer (`base.group_user`)
- **Erweiterte Rechte**: Buchhalter (`account.group_account_manager`)
- Erstellen/Bearbeiten/Löschen ist **nicht möglich** (read-only)

### Datenbankabfrage

Das Modul erstellt eine PostgreSQL View, die folgende Tabellen verknüpft:

- `account_analytic_account` - Analytische Konten (Projekte)
- `account_move` - Rechnungen (Ausgangs- und Eingangsrechnungen)
- `account_move_line` - Rechnungszeilen mit analytischer Verteilung
- `account_analytic_line` - Zeiterfassung

## Anpassungen und Erweiterungen

### Filter anpassen

Um die Projekt-Auswahl anzupassen, können Sie die `WHERE`-Bedingung in der `init()`-Methode ändern:

```python
# Beispiel: Nur Projekte eines bestimmten Plans
WHERE aaa.plan_id = <plan_id>
```

### Zusätzliche Felder hinzufügen

1. Feld im Model definieren (`models/models.py`)
2. Feld in der SQL-View hinzufügen (`init()` Methode)
3. Feld in der Tree-View anzeigen (`views/views.xml`)

### Zusätzliche Auswertungen

Sie können weitere Views hinzufügen:

- Kalender-Ansicht (nach Rechnungsdatum)
- Kanban-Ansicht
- Formular-Ansicht mit Detailauswertung

## Support und Weiterentwicklung

**Entwickler**: HFC
**Version**: 18.0.1.0.0
**Lizenz**: LGPL-3
**Odoo Version**: 18.0 Enterprise

## Changelog

### Version 18.0.1.0.0 (2025)
- Initiale Version
- Tree, Pivot und Graph Views
- Automatische Deckungsbeitragsberechnung
- Integration von Rechnungen und Zeiterfassung
- Deutsche Lokalisierung

## Bekannte Einschränkungen

- Das Modul setzt voraus, dass der analytische Plan "Projekt" im Namen enthält
- Multi-Company wird berücksichtigt, aber nicht explizit gefiltert
- Historische Daten werden bei jedem Zugriff neu berechnet (keine Caching)

## Häufig gestellte Fragen (FAQ)

**F: Warum sehe ich keine Daten?**
A: Stellen Sie sicher, dass:
- Analytische Buchführung aktiviert ist
- Projekte als analytische Konten angelegt sind
- Rechnungen mit Projekten verknüpft sind (analytische Verteilung)
- Rechnungen gebucht sind (Status = "Gebucht")

**F: Kann ich die Daten exportieren?**
A: Ja, über die Listen-Ansicht können Sie alle Daten nach Excel exportieren.

**F: Werden Gutschriften berücksichtigt?**
A: Ja, sowohl Ausgangs- als auch Eingangs-Gutschriften werden in die Berechnung einbezogen.

**F: Wie oft werden die Daten aktualisiert?**
A: Die Daten werden in Echtzeit berechnet - bei jedem Aufruf der Ansicht.
