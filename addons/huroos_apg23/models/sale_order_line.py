from odoo import fields, models, api, Command
# TODO questo file si può spostare nel modulo apg_ddt

class APGSaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    line_n = fields.Integer(string=" ", readonly=True)

    def _compute_price_unit(self):
        super(APGSaleOrderLine, self)._compute_price_unit()

        for line in self.filtered(lambda line: line.order_id.pricelist_id.tax_included):
            # If the price list is tax included, change the price_unit
            if line.qty_invoiced > 0 or (line.product_id.expense_policy == 'cost' and line.is_expense):
                continue
            if not line.product_uom or not line.product_id:
                line.price_unit = 0.0
            else:
                line = line.with_company(line.company_id)
                price_with_tax = line._get_display_price()
                product_taxes = line.product_id.taxes_id._filter_taxes_by_company(line.company_id)
                taxes_included = product_taxes.with_context(force_price_include=True)

                tax_result = taxes_included.with_context(round_base=False).compute_all(
                    price_with_tax,
                    currency=line.currency_id or line.order_id.currency_id,
                    quantity=1.0,
                    product=line.product_id,
                    partner=line.order_id.partner_id
                )

                price_unit = tax_result['total_excluded']
                line.price_unit = price_unit