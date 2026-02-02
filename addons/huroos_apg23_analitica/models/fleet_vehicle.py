from odoo import fields, models, api


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    analytic_account_id = fields.Many2one('account.analytic.account')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('analytic_account_id'):
                #Se non è stato selezionato nessun conto analitico lo crea
                analytic_plan_id = self.env.ref('huroos_apg23_analitica.analytic_plan_automezzi')
                analytic_account_id = self.env['account.analytic.account'].sudo().search([('company_id', '=', vals['company_id']), ('plan_id', '=', analytic_plan_id.id), ('name', '=', vals['license_plate'].upper())])
                if not analytic_account_id:
                    vals['analytic_account_id'] = self.env['account.analytic.account'].sudo().create({
                        'company_id': vals['company_id'],
                        'name': vals['license_plate'].upper(),
                        'plan_id': analytic_plan_id.id
                    }).id
                else:
                    vals['analytic_account_id'] = analytic_account_id.id

        res = super(FleetVehicle, self).create(vals_list)
        return res