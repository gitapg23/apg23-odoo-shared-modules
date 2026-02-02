from odoo import fields, models, api


class StockMove(models.Model):
    _inherit = 'stock.move'

    line_n = fields.Integer(string=" ", readonly=True)
    ddt_date = fields.Date(string="Data DDT", computed="_compute_ddt_date", store=True)

    @api.depends('ddt_ids', 'ddt_ids.date')
    def _compute_ddt_date(self):
        for move in self:
            # Prende la data del primo DDT, se esiste
         move.ddt_date = move.ddt_ids[0].date.date() if move.ddt_ids and move.ddt_ids[0].date else False


    def action_create_packages(self):
        res = self.env['wizard.create.packages'].sudo().create({
            'move_id': self.id,
        })

        return {
            'type': 'ir.actions.act_window',
            'name': 'Crea Colli',
            'res_model': 'wizard.create.packages',
            'view_mode': 'form',
            'target': 'new',
            'res_id': res.id,
        }
