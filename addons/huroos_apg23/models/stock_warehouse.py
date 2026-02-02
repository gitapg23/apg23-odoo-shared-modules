from odoo import fields, models


class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    structure_id = fields.Many2one("onlus.struttura", string="Struttura")