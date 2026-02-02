from odoo import fields, models, api


class StockLot(models.Model):
    _inherit = 'stock.lot'
    _barcode_field = 'default_code_and_lot'

    default_code_and_lot = fields.Char(compute="_compute_default_code_and_lot", store=True)

    @api.depends('name', 'product_id.default_code')
    def _compute_default_code_and_lot(self):
        for rec in self:
            rec.default_code_and_lot = ((rec.product_id.default_code or '') + (rec.name or '')).replace(" ", "")

    @api.model
    def _get_fields_stock_barcode(self):
        return ['default_code_and_lot', 'name', 'ref', 'product_id']