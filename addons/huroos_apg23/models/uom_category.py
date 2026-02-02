from odoo import fields, models, api


class UomCategory(models.Model):
    _inherit="uom.category"

    for_presence = fields.Boolean(string="Visibile per presenza")

class UomUom(models.Model):
    _inherit="uom.uom"

    for_presence = fields.Boolean(string="Visibile per presenza",related='category_id.for_presence',store=True)