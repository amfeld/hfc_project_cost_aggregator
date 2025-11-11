# -*- coding: utf-8 -*-
{
    'name': "HFC Projekt Kosten Aggregator",

    'summary': """
        Aggregierte Ansicht von Projektkosten: Rechnungen, Lieferantenrechnungen und Zeiterfassung""",

    'description': """
        Projekt Kosten Aggregator
        ==========================

        Dieses Modul bietet eine übersichtliche Auswertung aller projektbezogenen Kosten und Umsätze:

        **Funktionen:**
        * Aggregierte Ansicht von Ausgangsrechnungen (Umsatz) pro Projekt
        * Aggregierte Ansicht von Eingangsrechnungen (Material-/Fremdkosten) pro Projekt
        * Integration der Zeiterfassung (Personalkosten) pro Projekt
        * Berechnung von Deckungsbeitrag und Marge
        * Pivot- und Graph-Ansichten für detaillierte Analysen
        * Filterung nur auf aktive Projekte mit Buchungen

        **Voraussetzungen:**
        * Analytische Buchführung muss aktiviert sein
        * Projekte müssen als analytische Konten angelegt sein
        * Rechnungen müssen mit analytischen Konten verknüpft sein
    """,

    'author': "HFC",
    'website': "https://www.hfc.de",

    'category': 'Accounting/Accounting',
    'version': '18.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'account',
        'analytic',
        'hr_timesheet',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}