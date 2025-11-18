# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools


class ProjectCostAggregator(models.Model):
    """Aggregierte Ansicht von Projekt-Kosten und Umsätzen"""
    _name = 'hfc.project.cost.aggregator'
    _description = 'Projekt Kosten Aggregator'
    _auto = False
    _order = 'gesamt_rechnungsbetrag desc'

    # Projekt-Identifikation
    projekt_id = fields.Many2one('account.analytic.account', string='Projekt', readonly=True)
    projekt_name = fields.Char(string='Projektname', readonly=True)
    projekt_code = fields.Char(string='Projektkürzel', readonly=True)

    # Ausgangsrechnungen (Umsatz)
    anzahl_rechnungen = fields.Integer(string='Anzahl Rechnungen', readonly=True)
    gesamt_rechnungsbetrag = fields.Monetary(string='Kundenrechnung (Brutto)', readonly=True, currency_field='currency_id')
    gesamt_gezahlt = fields.Monetary(string='Tatsächlich Bezahlt', readonly=True, currency_field='currency_id')
    gesamt_differenz = fields.Monetary(string='Differenz (Abzüge/Offen)', readonly=True, currency_field='currency_id')

    # Eingangsrechnungen (Kosten)
    anzahl_lieferantenrechnungen = fields.Integer(string='Anzahl Lieferantenrechnungen', readonly=True)
    gesamt_kosten = fields.Monetary(string='Gesamt Kosten', readonly=True, currency_field='currency_id')
    gesamt_offene_kosten = fields.Monetary(string='Offene Kosten', readonly=True, currency_field='currency_id')

    # Zeiterfassung
    gebuchte_stunden = fields.Float(string='Gebuchte Stunden', readonly=True, digits=(16, 2))
    kosten_gebuchte_stunden = fields.Monetary(string='Kosten Stunden', readonly=True, currency_field='currency_id')

    # Währung (für Monetary-Felder)
    currency_id = fields.Many2one('res.currency', string='Währung', readonly=True)

    def init(self):
        """Erstelle PostgreSQL View für aggregierte Projektkosten"""
        tools.drop_view_if_exists(self.env.cr, self._table)
        query = """
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    ROW_NUMBER() OVER (ORDER BY aaa.id) AS id,
                    aaa.id AS projekt_id,
                    aaa.name AS projekt_name,
                    aaa.code AS projekt_code,

                    -- Ausgangsrechnungen (Umsatz)
                    COUNT(DISTINCT CASE WHEN inv.move_type IN ('out_invoice', 'out_refund') THEN inv.id END) AS anzahl_rechnungen,
                    COALESCE(SUM(CASE WHEN inv.move_type IN ('out_invoice', 'out_refund')
                        THEN inv.amount_total * COALESCE((line.analytic_distribution->>aaa.id::text)::numeric / 100, 0)
                        ELSE 0 END), 0) AS gesamt_rechnungsbetrag,
                    COALESCE(SUM(CASE WHEN inv.move_type IN ('out_invoice', 'out_refund')
                        THEN (inv.amount_total - inv.amount_residual) * COALESCE((line.analytic_distribution->>aaa.id::text)::numeric / 100, 0)
                        ELSE 0 END), 0) AS gesamt_gezahlt,
                    COALESCE(SUM(CASE WHEN inv.move_type IN ('out_invoice', 'out_refund')
                        THEN inv.amount_residual * COALESCE((line.analytic_distribution->>aaa.id::text)::numeric / 100, 0)
                        ELSE 0 END), 0) AS gesamt_differenz,

                    -- Eingangsrechnungen (Kosten)
                    COUNT(DISTINCT CASE WHEN inv.move_type IN ('in_invoice', 'in_refund') THEN inv.id END) AS anzahl_lieferantenrechnungen,
                    COALESCE(SUM(CASE WHEN inv.move_type IN ('in_invoice', 'in_refund')
                        THEN inv.amount_total * COALESCE((line.analytic_distribution->>aaa.id::text)::numeric / 100, 0)
                        ELSE 0 END), 0) AS gesamt_kosten,
                    COALESCE(SUM(CASE WHEN inv.move_type IN ('in_invoice', 'in_refund')
                        THEN inv.amount_residual * COALESCE((line.analytic_distribution->>aaa.id::text)::numeric / 100, 0)
                        ELSE 0 END), 0) AS gesamt_offene_kosten,

                    -- Zeiterfassung
                    COALESCE(SUM(ts.unit_amount), 0) AS gebuchte_stunden,
                    COALESCE(SUM(ts.amount), 0) AS kosten_gebuchte_stunden,

                    -- Zusätzliche Info
                    MIN(inv.invoice_date) AS erste_rechnung,
                    MAX(inv.invoice_date) AS letzte_rechnung,

                    -- Währung
                    (SELECT currency_id FROM res_company WHERE id = aaa.company_id LIMIT 1) AS currency_id

                FROM account_analytic_account aaa

                -- Rechnungszeilen mit analytischer Verteilung
                LEFT JOIN account_move_line line
                    ON line.analytic_distribution ? aaa.id::text
                    AND line.display_type IS NULL

                -- Rechnungen
                LEFT JOIN account_move inv
                    ON inv.id = line.move_id
                    AND inv.move_type IN ('out_invoice', 'out_refund', 'in_invoice', 'in_refund')
                    AND inv.state = 'posted'

                -- Zeiterfassung
                LEFT JOIN account_analytic_line ts
                    ON ts.account_id = aaa.id

                WHERE
                    aaa.plan_id = (
                        SELECT id FROM account_analytic_plan
                        WHERE LOWER(name) LIKE LOWER('%%projekt%%')
                        LIMIT 1
                    )
                    AND aaa.active = TRUE

                GROUP BY
                    aaa.id,
                    aaa.name,
                    aaa.code,
                    aaa.company_id
            )
        """ % self._table
        self.env.cr.execute(query)