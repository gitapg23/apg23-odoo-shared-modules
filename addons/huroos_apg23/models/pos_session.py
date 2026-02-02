from odoo import models, _, fields
from odoo.exceptions import UserError


class PosSession(models.Model):
    _inherit = 'pos.session'

    # Modified for searching by default_code_and_lot
    def find_product_by_barcode(self, barcode):
        lot = self.env['stock.lot'].search([
            ('default_code_and_lot', '=', barcode),
            ('product_id.sale_ok', '=', True),
            ('product_id.available_in_pos', '=', True)
        ], order="id desc", limit=1)
        if lot:
            product = lot.product_id
        else:
            product = self.env['product.product'].search([
                ('barcode', '=', barcode),
                ('sale_ok', '=', True),
                ('available_in_pos', '=', True),
            ])
        if product:
            return {'product_id': [product.id]}

        packaging_params = self._loader_params_product_packaging()
        packaging_params['search_params']['domain'] = [['barcode', '=', barcode]]
        packaging = self.env['product.packaging'].search_read(**packaging_params['search_params'])
        if packaging:
            product_id = packaging[0]['product_id']
            if product_id:
                return {'product_id': [product_id[0]], 'packaging': packaging}
        return {}

    def _post_statement_difference(self, amount, is_opening):
        if amount:
            if self.config_id.cash_control:
                st_line_vals = {
                    'journal_id': self.cash_journal_id.id,
                    'amount': amount,
                    'date': self.statement_line_ids.sorted()[-1:].date or fields.Date.context_today(self),
                    'pos_session_id': self.id,
                }

            if amount < 0.0:
                if not self.cash_journal_id.loss_account_id:
                    raise UserError(
                        _('Please go on the %s journal and define a Loss Account. This account will be used to record cash difference.',
                          self.cash_journal_id.name))

                st_line_vals['payment_ref'] = _("Cash difference observed during the counting (Loss)") + (_(' - opening') if is_opening else _(' - closing'))
                #if not is_opening:
                st_line_vals['counterpart_account_id'] = self.cash_journal_id.loss_account_id.id
            else:
                # self.cash_register_difference  > 0.0
                if not self.cash_journal_id.profit_account_id:
                    raise UserError(
                        _('Please go on the %s journal and define a Profit Account. This account will be used to record cash difference.',
                          self.cash_journal_id.name))

                st_line_vals['payment_ref'] = _("Cash difference observed during the counting (Profit)") + (_(' - opening') if is_opening else _(' - closing'))
                #if not is_opening:
                st_line_vals['counterpart_account_id'] = self.cash_journal_id.profit_account_id.id

            self.env['account.bank.statement.line'].create(st_line_vals)