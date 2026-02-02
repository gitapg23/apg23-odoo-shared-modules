from odoo import fields, models, api
from odoo.exceptions import UserError

class ImmobileUtenza(models.Model):
    _inherit = 'immobile.utenza'

    analytic_account_id = fields.Many2one('account.analytic.account')

    @api.model_create_multi
    def create(self, vals_list):
        """ Si assicura che ci sia un conto analitico collegato. """
        records = super(ImmobileUtenza, self).create(vals_list)
        for record in records.filtered(lambda r: not r.analytic_account_id):
            analytic_account = record._get_or_create_analytic_account()
            if analytic_account:
                record.analytic_account_id = analytic_account
        return records

    def write(self, vals):
        """
        - Se cambia il company_id, crea un nuovo conto analitico nella nuova azienda.
        - Se cambia solo il nome, aggiorna il nome dell'account analitico esistente.
        """
        res = super(ImmobileUtenza, self).write(vals)

        if 'company_id' in vals:
            for record in self:
                analytic_account = record._get_or_create_analytic_account()
                if analytic_account:
                    record.analytic_account_id = analytic_account
        elif 'name' in vals:
            for record in self.filtered('analytic_account_id'):
                record.analytic_account_id.sudo().write({'name': str(record.name).upper()})

        return res

    def _get_or_create_analytic_account(self):
        """
        Trova un conto analitico esistente basato su name e company_id
        one crea uno nuovo.
        """
        self.ensure_one()
        analytic_plan = self.env.ref('huroos_apg23_analitica.analytic_plan_utenze', raise_if_not_found=False)
        if not self.name or not analytic_plan:
            return self.env['account.analytic.account']

        name = str(self.name).upper()
        company_id = self.company_id.id or self.env.company.id

        domain = [
            ('company_id', '=', company_id),
            ('plan_id', '=', analytic_plan.id),
            ('name', '=', name)
        ]
        analytic_account = self.env['account.analytic.account'].sudo().search(domain, limit=1)

        if not analytic_account:
            analytic_account = self.env['account.analytic.account'].sudo().create({
                'company_id': company_id,
                'name': name,
                'plan_id': analytic_plan.id
            })

        return analytic_account