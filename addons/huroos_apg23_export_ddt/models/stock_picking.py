from odoo import models, fields


class APGDDTStockPicking(models.Model):
    _inherit = 'stock.picking'

    export_ddt_info = fields.Boolean(string="Esportare tracciato dei DDT", default=False)
    installation_code = fields.Char(string="Codice impianto", related="partner_id.installation_code")