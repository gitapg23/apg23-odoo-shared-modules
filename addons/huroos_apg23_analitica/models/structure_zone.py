from odoo import fields, models, api
from odoo.exceptions import UserError


class StructureZone(models.Model):
    _inherit = 'structure.zone'



    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('analytic_account_id'):
                #Se non è stato selezionato nessun conto analitico lo crea
                analytic_plan_id = self.env.ref('huroos_apg23.analytic_plan_zone')
                if not vals['name']:
                    raise UserError("Bisogna impostare un nome")
                name = str(vals['name']).upper()
                analytic_account_id = self.env['account.analytic.account'].sudo().search([('company_id', '=', vals['company_id'] if vals['company_id'] else self.env.company.id), ('plan_id', '=', analytic_plan_id.id), ('name', '=', name)])
                if not analytic_account_id:
                    vals['analytic_account_id'] = self.env['account.analytic.account'].sudo().create({
                        'company_id': vals['company_id'] if vals['company_id'] else self.env.company.id,
                        'name': name.upper(),
                        'plan_id': analytic_plan_id.id
                    }).id
                else:
                    vals['analytic_account_id'] = analytic_account_id.id

        res = super(StructureZone, self).create(vals_list)
        return res