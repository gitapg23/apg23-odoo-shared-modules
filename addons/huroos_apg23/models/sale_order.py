from odoo import fields, models, api, Command
# TODO questo file si può spostare nel modulo apg_ddt
PRODUCT_TYPE_LIST_SELECTION = [
    ('A', 'ABBONAMENTO'), ('P', 'PRODOTTO SINGOLO'),
]


class APGSaleOrderPayment(models.Model):
    _name = 'sale.order.payment'
    _description = 'Pagamento per Ordine di Vendita'

    code = fields.Char(string='Codice')
    name = fields.Char(string='Nome', required=True)
    order_ids = fields.One2many('sale.order', 'so_payment_id', string="Ordini")


class APGSaleOrderExpedition(models.Model):
    _name = 'sale.order.expedition'
    _description = 'Spedizione per Ordine di Vendita'

    code = fields.Char(string='Codice')
    name = fields.Char(string='Nome', required=True)
    order_ids = fields.One2many('sale.order', 'so_expedition_id', string="Ordini")


class APGSaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = ['sale.order', 'apg.import.mixin']

    prodotto_tipo = fields.Selection(string="Prodotto Tipo", selection=PRODUCT_TYPE_LIST_SELECTION)
    so_expedition_id = fields.Many2one('sale.order.expedition', string="Spedizione")
    so_payment_id = fields.Many2one('sale.order.payment', string="Pagamento")
    so_date_order = fields.Date()
    data_inizio_abb = fields.Date(string="Data Inizio Abb")
    data_fine_abb = fields.Date(string="Data Fine Abb")
    data_modifica = fields.Date(string="Data Modifica")
    disdetta_data = fields.Date(string="Disdetta Data")
    pagato = fields.Boolean()
    time_slot_id = fields.Many2one(
        comodel_name="time.slot",
        string="Fascia oraria"
    )

    line_n_qty = fields.Integer(string="Num", compute="_compute_line_n_qty")

    nso_order_ids = fields.Many2many(
        'nso.order', 'rel_sale_nso_allowed', 'sale_order_id', 'nso_order_id',
        string="Buoni d'ordine NSO collegati", readonly=True)

    def _compute_line_n_qty(self):
        for order in self:
            product_lines = order.order_line.filtered(lambda l: not l.display_type)
            lines_without_numeration = product_lines.filtered(lambda line: line.line_n == 0)
            if lines_without_numeration:
                other_lines = order.order_line.filtered(lambda l: l.display_type)
                for line in other_lines:
                    line.line_n = 0

                for idx, line in enumerate(product_lines.sorted(key=lambda l: (l.sequence, l.id if isinstance(l.id, int) else 0)), start=1):
                    line.line_n = idx

            order.line_n_qty = len(product_lines)

    def to_odoo_dict(self, apg_dict, data_hash, unique_code, send_data_type, hash_upd=False):
        """OVERRIDE di apg.import.mixin"""
        # apg_dict = {
        #
        # COMUNICARE:
        #   - Ci sono dei ClienteCodiceGedi con degli id non presenti nei tracciati gedi
        #   - Questi ordini sono da collegare alla company ERP o sono sovraziendali?
        #
        # WAITING:
        #   - Niente.
        #
        # NOTE
        #   Uniquecode: ["ClienteCodiceGedi", "OrdineCod"] | len: 86525
        #
        # ELIMINATI/NON IMPORTATI
        #   filtrorinn                            # direttive apg
        #   QuantitaRinnovo                       # direttive apg
        #   IsRinnovo                             # direttive apg
        #
        # AGGIUNTI                                # ODOO
        #   "DataFineAbb": "",                    # Salvato come data
        #   "DataInizioAbb": "",                  # Salvato come data
        #   "DataModifica": "",                   # Salvato come data
        #   "DisdettaData": "",                   # Salvato come data
        #   "ProdottoTipo": "A",                  # Salvato come selection
        #   "ModalitaPagCod": "",                 # code -> so_payment_id
        #   "ModalitaPagDesc": "",                # name -> so_payment_id
        #   "SpedizioneCod": "",                  # code -> so_expedition_id
        #   "SpedizioneDesc": "",                 # name -> so_expedition_id
        #   "ProdottoDesc": "Storie di amor",     # line_ids -> name
        #
        # FATTI                                   # ODOO
        #   "ClienteCodiceGedi": "105",           # partner -> modello res.partner -> search by 'codice_gedi'
        #   "ClientePagante": "",                 # Se diverso da ClienteCodiceGedi aggiungo in note chi ha pagato
        #   "OrdineCodDiRiferimento": "0",        # Se diverso da 0 aggiungo in note da che ordine è stato generato
        #   "DataInserimento": "2016-10-24",      # date_order
        #   "ImportoUnitario": "24.00",           # price_unit
        #   "ProdottoCod": "1",                   # product_id
        #   "OrdineNote": "",                     # note
        #   "Sconto": "0.00",                     # discount
        #   "Qt": "1",                            # product_uom_qty
        # }
        # --------------------------------------------------------------------------------------------------------------
        codice_gedi = apg_dict.get('ClienteCodiceGedi')
        if not codice_gedi:
            raise Exception("Field 'ClienteCodiceGedi' is void")
        partner = self.sudo().env['res.partner'].search([('codice_gedi', '=', codice_gedi)], limit=1)
        if not partner:
            raise Exception(f"Partner codice_gedi({codice_gedi}) not found")

        # --------------------------------------------------------------------------------------------------------------
        default_code = apg_dict.get('ProdottoCod')
        default_code_varianti = self.get_data_from_inner_field(apg_dict, 'RiferimentiInterni')
        if not default_code:
            raise Exception("Field 'ProdottoCod' is void")
        if default_code_varianti:
            default_code = default_code_varianti
        else:
            default_code = [default_code]
        product = self.sudo().env['product.product'].search([('default_code', 'in', default_code)])
        if not product:
            raise Exception(f"Product default_code({default_code}) not found")

        # --------------------------------------------------------------------------------------------------------------
        data_fine_abb = self.get_date_obj(apg_dict, 'DataFineAbb')
        data_modifica = self.get_date_obj(apg_dict, 'DataModifica')
        disdetta_data = self.get_date_obj(apg_dict, 'DisdettaData')
        data_inizio_abb = self.get_date_obj(apg_dict, 'DataInizioAbb')
        date_order = self.get_date_obj(apg_dict, 'DataInserimento')
        if not date_order:
            date_order = data_inizio_abb or data_modifica

        # --------------------------------------------------------------------------------------------------------------
        note = apg_dict.get('OrdineNote')
        product_uom_qty = apg_dict.get('Qt')
        price_unit = apg_dict.get('ImportoUnitario')
        product_name = apg_dict.get('ProdottoDesc')
        discount = apg_dict.get('Sconto')

        # Imponibile
        subtotal = float(apg_dict.get('ImportoUnitario')) * float(apg_dict.get('Qt'))
        price_unit = float(subtotal) / len(product) if product else 1

        # --------------------------------------------------------------------------------------------------------------
        company = self.sudo().env['res.company'].search([('code', '=', 'ERP')])

        # --------------------------------------------------------------------------------------------------------------
        cliente_pagante = apg_dict.get('ClientePagante')
        if cliente_pagante:
            note += f"\nPagato da cliente codice_gedi=  {cliente_pagante}"

        # --------------------------------------------------------------------------------------------------------------
        ordine_cod_riferimento = apg_dict.get('OrdineCodDiRiferimento')
        if ordine_cod_riferimento != '0':
            note += f"\nGenerato da ordine {ordine_cod_riferimento}"

        # --------------------------------------------------------------------------------------------------------------
        so_payment_name = apg_dict.get("ModalitaPagDesc")
        so_payment_code = apg_dict.get("ModalitaPagCod")
        so_payment = None
        if so_payment_name:
            so_payment_vals = {'name': so_payment_name, 'code': so_payment_code}
            so_payment = self.search_create_update('sale.order.payment', 'name', so_payment_vals)

        # --------------------------------------------------------------------------------------------------------------
        so_expedition_name = apg_dict.get("SpedizioneDesc")
        so_expedition_code = apg_dict.get("SpedizioneCod")
        so_expedition = None
        if so_expedition_name:
            so_expedition_vals = {'name': so_expedition_name, 'code': so_expedition_code}
            so_expedition = self.search_create_update('sale.order.expedition', 'name', so_expedition_vals)

        QuartoCampo = apg_dict.get('QuartoCampo', "")
        pagato = apg_dict.get('Pagato', "")
        if pagato == "S":
            pagato = True
        else:
            pagato = False



        # --------------------------------------------------------------------------------------------------------------
        user_id = self.sudo().env['res.users'].search([('name', '=', 'editoresempre')], limit=1)

        # --------------------------------------------------------------------------------------------------------------
        sale_order_vals = {
            'company_id': company.id,
            # 'state': 'sale',
            'partner_id': partner.id,
            'note': note,
            'date_order': date_order,
            'so_date_order': date_order,
            'warehouse_id': 26,
            'quarto_campo': QuartoCampo,
            'pagato': pagato,
            'product_bollettino_ids': [(5, ), (0, 0, {
                'product_id': product[0].product_tmpl_id.id if product else False,
                'qt': apg_dict.get('Qt'),
                'amount': apg_dict.get('ImportoUnitario'),
                'amount_subtotal': subtotal,
                'from_date': data_inizio_abb,
                'to_date': data_fine_abb,
                'is_annuale': False
            })],
            'order_line': [(5, )] + [(0, 0, {
                'product_id': x.id,
                'name': x.default_code if len(product) > 1 else product_name,
                'product_uom_qty': float(product_uom_qty),
                'qty_delivered': float(product_uom_qty),
                'price_unit': float(price_unit),
                'discount': float(discount),
                'commitment_date': self.calcola_data_programmata(
                    anno=self.get_attribute_value(x, 'ANNO'),
                    uscita=self.get_attribute_value(x, 'USCITA')
                ),
            }) for x in product],
            # -----
            "user_id": user_id.id if user_id else False,
            "prodotto_tipo": apg_dict.get('ProdottoTipo'),
            "so_payment_id": so_payment.id if so_payment else False,
            "so_expedition_id": so_expedition.id if so_expedition else False,
            "data_fine_abb": data_fine_abb,
            "data_inizio_abb": data_inizio_abb,
            "data_modifica": data_modifica,
            "disdetta_data": disdetta_data,
            # -----
            'apg_id': unique_code,
            'data_hash': data_hash
        }

        # Calcolo del totale delle righe e verifica della differenza
        order_lines = sale_order_vals['order_line'][1:]  # Escludi il comando (5, )
        total_order_lines = sum(round(float(round(line[2]['price_unit'], 2)) * float(line[2]['product_uom_qty']), 2) for line in order_lines)
        expected_total = subtotal

        if total_order_lines != expected_total:
            # Calcolo della differenza
            difference = expected_total - total_order_lines

            # Modifica il prezzo dell'ultima riga
            if order_lines:
                last_line = order_lines[-1][2]
                last_line['price_unit'] += difference / float(last_line['product_uom_qty'])


        return sale_order_vals




    def get_attribute_value(self, product, attribute_name):
        for attr_value in product.product_template_attribute_value_ids:
            if attr_value.attribute_id.name == attribute_name:
                return attr_value.name
        return None

    def calcola_data_programmata(self, anno, uscita):
        if anno and uscita:
            # Mapping tra il valore di "USCITA" e il primo giorno del mese
            uscita_to_date = {
                'GENNAIO-FEBBRAIO': '-01-01',
                'MARZO-APRILE': '-03-01',
                'MAGGIO-GIUGNO': '-05-01',
                'LUGLIO-AGOSTO': '-07-01',
                'SETTEMBRE-OTTOBRE': '-09-01',
                'NOVEMBRE-DICEMBRE': '-12-01',
            }
            return f"{anno}{uscita_to_date.get(uscita, '-01-01')}"  # Default a gennaio
        else:
            return False