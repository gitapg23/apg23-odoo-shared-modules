from odoo import models, fields
from odoo.exceptions import UserError
import base64
import re
import io


class APGDDTHuroosDDT(models.Model):
    _inherit = 'huroos.delivery.note'

    export_ddt_info = fields.Boolean(related="partner_id.export_ddt_info")
    installation_code = fields.Char(string="Codice impianto", related="partner_shipping_id.installation_code")
    txt_id = fields.Many2one("huroos.delivery.note.txt", string="TXT esportato", readonly=True)

    def _get_records(self):
        records = []
        for move in self.stock_move_ids:
            order = move.sale_line_id.order_id
            product = move.product_id
            seller = product.seller_ids[0] if move.product_id.seller_ids else False
            customer = product.sh_product_customer_ids[0] if move.product_id.sh_product_customer_ids else False
            # No code alert
            if not customer or not customer.product_code:
                raise UserError(
                    f"Il prodotto [{product.default_code}] {product.name} non ha un codice cliente associato. "
                    "Aggiungerlo nel tab Vendite della scheda prodotto."
                )

            lot = move.lot_ids[0] if move.lot_ids else False
            records.append([
                self.installation_code or "", # COD_IMPIANTO
                self.name, # NUMERO_DDT
                self.create_date.strftime('%Y%m%d') if self.create_date else "", # DATA_DDT
                self.date.strftime('%Y%m%d') if self.date else "", # DATA_CONSEGNA
                customer.product_code if customer and customer.product_code else "", # COD_ARTICOLO
                customer.product_name if customer and customer.product_name else "", # DESCR_ARTICOLO
                # seller.product_code if seller and seller.product_code else "", # COD_ARTICOLO_FORNITORE
                # seller.product_name if seller and seller.product_name else "", # DESCR_ARTICOLO_FORNITORE
                product.default_code or "",  # COD_ARTICOLO_FORNITORE
                product.with_context(lang='it_IT').name or "",  # DESCR_ARTICOLO_FORNITORE
                move.with_context(lang='it_IT').product_uom.name if move.product_uom.name else "", # UM_FORNITORE
                int(move.unit_price * 10000), # PREZZO
                1, # COLLI
                int(move.product_qty * 1000), # QTA
                seller.partner_id.name if seller and seller.partner_id.name else "", # MARCHIO
                move.date_deadline.strftime('%Y%m%d') if move.date_deadline else "", # SCADENZA
                lot.name if lot and lot.name else "", # LOTTO
                order.client_order_ref or "", # NUMERO_ORDINE
            ])

        return records

    def _create_file(self, records):
        content = "TM\n"
        for rec in records:
            content += "|".join(re.sub(r" {2,}", "", str(field)) for field in rec) + "||\n"
        content += f"FM|{len(records):04d}|\n"

        file_bytes = content.encode("utf-8")

        return io.BytesIO(file_bytes), base64.b64encode(file_bytes), f"{self.name}.txt"

    def btn_export_ddt_info(self):
        records = self._get_records()
        file_io, file_data, file_name = self._create_file(records)

        wizard = self.env['wizard.export.txt'].create({
            "ddt_id": self.id,
            "file_io": file_data,
            "file_data": file_data,
            "file_name": file_name,
        })

        return {
            "type": "ir.actions.act_window",
            "name": "File TXT",
            "res_model": "wizard.export.txt",
            "view_mode": "form",
            "res_id": wizard.id,
            "target": "new",
        }