from odoo import models, fields


class APGDDTResPartner(models.Model):
    _inherit = 'res.partner'

    export_ddt_info = fields.Boolean(string="Esportare tracciato dei DDT", default=False)
    installation_code = fields.Char(string="Codice impianto")