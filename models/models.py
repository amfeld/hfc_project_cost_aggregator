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
    gesamt_rechnungsbetrag = fields.Monetary(string='Gesamt Rechnungsbetrag', readonly=True, currency_field='currency_id')
    gesamt_offener_betrag = fields.Monetary(string='Offener Betrag', readonly=True, currency_field='currency_id')

    # Eingangsrechnungen (Kosten)
    anzahl_lieferantenrechnungen = fields.Integer(string='Anzahl Lieferantenrechnungen', readonly=True)
    gesamt_kosten = fields.Monetary(string='Gesamt Kosten', readonly=True, currency_field='currency_id')
    gesamt_offene_kosten = fields.Monetary(string='Offene Kosten', readonly=True, currency_field='currency_id')

    # Zeiterfassung
    gebuchte_stunden = fields.Float(string='Gebuchte Stunden', readonly=True, digits=(16, 2))
    kosten_gebuchte_stunden = fields.Monetary(string='Kosten Stunden', readonly=True, currency_field='currency_id')

    # Berechnete Felder
    deckungsbeitrag = fields.Monetary(string='Deckungsbeitrag', readonly=True, compute='_compute_margins', store=False, currency_field='currency_id')
    deckungsbeitrag_prozent = fields.Float(string='DB %', readonly=True, compute='_compute_margins', store=False, digits=(16, 2))

    # Zusätzliche Info
    erste_rechnung = fields.Date(string='Erste Rechnung', readonly=True)
    letzte_rechnung = fields.Date(string='Letzte Rechnung', readonly=True)

    # Währung (für Monetary-Felder)
    currency_id = fields.Many2one('res.currency', string='Währung', readonly=True)

    @api.depends('gesamt_rechnungsbetrag', 'gesamt_kosten', 'kosten_gebuchte_stunden')
    def _compute_margins(self):
        """Berechne Deckungsbeitrag und Marge"""
        for record in self:
            gesamt_kosten = (record.gesamt_kosten or 0) + (record.kosten_gebuchte_stunden or 0)
            record.deckungsbeitrag = (record.gesamt_rechnungsbetrag or 0) - gesamt_kosten

            if record.gesamt_rechnungsbetrag and record.gesamt_rechnungsbetrag != 0:
                record.deckungsbeitrag_prozent = (record.deckungsbeitrag / record.gesamt_rechnungsbetrag) * 100
            else:
                record.deckungsbeitrag_prozent = 0

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
                    COUNT(DISTINCT CASE WHEN am.move_type IN ('out_invoice', 'out_refund') THEN am.id END) AS anzahl_rechnungen,
                    SUM(CASE WHEN am.move_type IN ('out_invoice', 'out_refund')
                        THEN am.amount_total * COALESCE((aml.analytic_distribution->>aaa.id::text)::numeric / 100, 0)
                        ELSE 0 END
                    ) AS gesamt_rechnungsbetrag,
                    SUM(CASE WHEN am.move_type IN ('out_invoice', 'out_refund')
                        THEN am.amount_residual * COALESCE((aml.analytic_distribution->>aaa.id::text)::numeric / 100, 0)
                        ELSE 0 END
                    ) AS gesamt_offener_betrag,

                    -- Eingangsrechnungen (Kosten)
                    COUNT(DISTINCT CASE WHEN am.move_type IN ('in_invoice', 'in_refund') THEN am.id END) AS anzahl_lieferantenrechnungen,
                    SUM(CASE WHEN am.move_type IN ('in_invoice', 'in_refund')
                        THEN am.amount_total * COALESCE((aml.analytic_distribution->>aaa.id::text)::numeric / 100, 0)
                        ELSE 0 END
                    ) AS gesamt_kosten,
                    SUM(CASE WHEN am.move_type IN ('in_invoice', 'in_refund')
                        THEN am.amount_residual * COALESCE((aml.analytic_distribution->>aaa.id::text)::numeric / 100, 0)
                        ELSE 0 END
                    ) AS gesamt_offene_kosten,

                    -- Zeiterfassung
                    COALESCE(SUM(aal.unit_amount), 0) AS gebuchte_stunden,
                    COALESCE(SUM(aal.amount), 0) AS kosten_gebuchte_stunden,

                    -- Zusätzliche Info
                    MIN(am.invoice_date) AS erste_rechnung,
                    MAX(am.invoice_date) AS letzte_rechnung,

                    -- Währung (aus Company)
                    (SELECT currency_id FROM res_company WHERE id = am.company_id LIMIT 1) AS currency_id

                FROM account_analytic_account aaa

                -- Rechnungszeilen mit diesem analytischen Konto
                INNER JOIN account_move_line aml
                    ON aml.analytic_distribution ? aaa.id::text
                    AND aml.display_type IS NULL

                -- Rechnung
                INNER JOIN account_move am
                    ON am.id = aml.move_id
                    AND am.move_type IN ('out_invoice', 'out_refund', 'in_invoice', 'in_refund')
                    AND am.state = 'posted'

                -- Zeiterfassung (Analytic Lines)
                LEFT JOIN account_analytic_line aal
                    ON aal.account_id = aaa.id
                    AND aal.project_id IS NOT NULL

                WHERE
                    aaa.plan_id = (
                        SELECT id FROM account_analytic_plan
                        WHERE name ILIKE '%%projekt%%'
                        LIMIT 1
                    )

                GROUP BY
                    aaa.id,
                    aaa.name,
                    aaa.code,
                    am.company_id

                HAVING
                    SUM(am.amount_total *
                        COALESCE((aml.analytic_distribution->>aaa.id::text)::numeric / 100, 0)
                    ) > 0
            )
        """ % self._table
        self.env.cr.execute(query)