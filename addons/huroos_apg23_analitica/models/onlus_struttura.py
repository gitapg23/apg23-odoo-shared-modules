from odoo import fields, models, api
from odoo.exceptions import UserError


class OnlusStruttura(models.Model):
    _inherit = 'onlus.struttura'



    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('analytic_account_id'):
                #Se non è stato selezionato nessun conto analitico lo crea - modifica ORIOLI: il codice immobile non è obbligatorio e non deve essere inserito nel conto analitico
                analytic_plan_id = self.env.ref('huroos_apg23_analitica.analytic_plan_strutture')
                if not vals['name']:
                    raise UserError("Bisogna impostare il codice immobile e un nome")
                name = str(vals['name']).upper()
                analytic_account_id = self.env['account.analytic.account'].sudo().search([('company_id', '=', vals['company_id']), ('plan_id', '=', analytic_plan_id.id), ('name', '=', name)])
                if not analytic_account_id:
                    vals['analytic_account_id'] = self.env['account.analytic.account'].sudo().create({
                        'company_id': vals['company_id'],
                        'name': name.upper(),
                        'plan_id': analytic_plan_id.id
                    }).id
                else:
                    vals['analytic_account_id'] = analytic_account_id.id

        res = super(OnlusStruttura, self).create(vals_list)
        return res