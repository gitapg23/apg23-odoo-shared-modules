from odoo import fields, models, _, api
import logging
from odoo.osv import expression

LIST_DIOCESI = [
    ("FOS", "FOS"), ("RIM", "RIM"), ("RSM", "RSM"), ("47900", "47900"),
    ("LUCCA", "LUCCA"), ("CUN", "CUN"), ("CES", "CES")]


class StructureCategory(models.Model):
    _name = 'structure.category'
    _description = 'Categoria Struttura'

    name = fields.Char(string='Nome')
    code = fields.Char(string="Codice")


class StructureZone(models.Model):
    _name = 'structure.zone'
    _description = 'Zona Struttura'

    name = fields.Char(string='Nome', required=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company.id)
    analytic_account_id = fields.Many2one('account.analytic.account') #viene ripreso in huroos_apg23_analitica


class OnlusStruttura(models.Model):
    _name = "onlus.struttura"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'apg.import.mixin']
    _description = "APG23 | Modello per gestione Strutture"

    name = fields.Char(
        string="Nome",
        help="Nome delLa Struttura",
    )

    company_id = fields.Many2one(
        "res.company", string="Azienda", default=lambda self: self.env.company
    )
    # todo: da rivedere deve mostrare i viaggi da accolto aperti nella struttura
    partner_ids = fields.Many2many(
        comodel_name="res.partner",
        string="Persone struttura"
    )

    immobile_code = fields.Char(
        string="Codice Immobile",
        help="Registra il campo 'Immobile' del tracciato d'importazione, anche quando il record a cui punta è assente.")
    immobile_id = fields.Many2one('immobile.immobile', string="Immobile")
    immobile_codice_id = fields.Many2one('immobile.immobile.codice', string="Immobile")
    date_close = fields.Date(string="Data chiusura", help="Data chiusura")
    date_open = fields.Date(string="Data apertura", help="Data apertura")
    capacity = fields.Integer(string="Capacità", help="Capacità")

    structure_category_id = fields.Many2one('structure.category', string="Categoria")
    structure_code = fields.Char(string="Codice Struttura")
    structure_zone_id = fields.Many2one('structure.zone', string="Zona")
    diocese = fields.Selection(selection=LIST_DIOCESI, string="Diocesi")

    city = fields.Char(string="Citta", help="Citta")
    zip = fields.Char(string="CAP", help="CAP")
    street = fields.Char(string="Strada", help="Strada")

    email = fields.Char(string="Email", help="Email")
    phone = fields.Char(string="Telefono", help="Telefono")

    id_intranet = fields.Char(string="ID Intranet")

    country_id = fields.Many2one(
        'res.country',
        string="Stato"
    )
    state_id = fields.Many2one(
        'res.country.state',
        string="Provincia",
        domain="[('country_id', '=?', country_id)]"
    )

    analytic_account_id = fields.Many2one('account.analytic.account')

    scheda_tetto_count = fields.Integer(
        string="Schede Tetto",
        compute="_compute_scheda_tetto_count"
    )

    def _compute_scheda_tetto_count(self):
        for rec in self:
            rec.scheda_tetto_count = self.env['scheda.tetto'].search_count([
                ('structure_id', '=', rec.id)
            ])

    def action_show_scheda_tetto(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Schede Tetto',
            'res_model': 'scheda.tetto',
            'view_mode': 'tree,form',
            'domain': [('structure_id', '=', self.id)],
            'context': {'default_structure_id': self.id},
        }
    
    @api.depends('id_intranet', 'city')
    def _compute_display_name(self):
        for rec in self:
            prefix = rec.name
            if prefix and rec.id_intranet:
                prefix += '-ID: ' + str(rec.id_intranet)
            if prefix and rec.state_id:
                prefix += f' {rec.state_id.code}'
            rec.display_name = prefix

    def name_get(self):
        result = list()
        for rec in self:
            name = f"{rec.name}{' - ' + rec.id_intranet if rec.id_intranet else ''}{' - ' + rec.state_id.code if rec.state_id else ''}"
            result.append((rec.id, name))
        return result

    @api.model
    def _name_search(self, name='', domain=None, operator='ilike', limit=100, order=None):
        domain = domain or []
        if name:
            domain = expression.AND([domain, ['|', '|', ('name', operator, name), ('id_intranet', operator, name),
                                              ('state_id', operator, name)]])  # Aggiungi qui i campi desiderati
        return self._search(domain, limit=limit, order=order)

    def get_address_string(self):
        state_name = self.state_id.name if self.state_id else ""
        name_list = [self.city, self.street, self.zip, state_name]
        address_str = ', '.join([x for x in name_list if x]) or "Non Definito"
        return address_str

    def to_odoo_dict(self, apg_dict, data_hash, unique_code, send_data_type, hash_upd=False):
        """OVERRIDE di apg.import.mixin"""
        # apg_dict = {
        #
        # WAITING
        #   - Non c'è sempre corrispondenza tra i valori del campo imm_code e i gli id del tracciato IMMOBILI
        #   - Il campo 'imm_code' punta a gli Id degli IMMOBILI o al CodiceImmobile degli IMMOBILI?
        #     Se puntasse al CodiceImmobile ci potrebbero essere valori come [202, 1345], di difficile gestione. Basterebbe uno dei due per fare il check?
        #   - Il campo company non è sempre valorizzato -> salto i record dove non è valorizzato
        #
        # IMPORTATI                                         # ODOO
        #   "diocese": "RIM",                               # diocese (selection)
        #   "structure_zone": "VMN",                        # structure_zone_id -> name
        #   "codice_categoria": "CA",                       # structure_category_id -> code
        #   "structure_category": "casa di accoglienza",    # structure_category_id -> name
        #   "structure_code": "0000000001",                 # unique_code
        #   "address_cap": "47853",                         # address_zip
        #   "address_locale": "coriano",                    # address_city
        #   "address_street": "guido rossa",                # address_street
        #   "address_street_number": "1",                   # address_number
        #   "capacity": "6",                                # capacity
        #   "date_close": "",                               # date_close
        #   "date_open": "1973-07-03",                      # open_date
        #   "dug": "via",                                   # dug
        #   "structure_email": "cec@apg23.org",             # email
        #   "structure_name": "casa betania",               # name
        #   "structure_phone": "0541657252",                # phone
        # }
        # --------------------------------------------------------------------------------------------------------------
        company = self.check_get_company(apg_dict, 'company', raise_exception=False)
        if not company:
            company = self.env.user.company_id
            logging.warning(f'Company: {apg_dict.get("company")} NOT FOUND. '
                            f'SET Company of current User -> {company.name}')

        # --------------------------------------------------------------------------------------------------------------
        dug = apg_dict.get('dug')
        addres = apg_dict.get('address_street')
        number = str(apg_dict.get('address_street_number'))
        street = " ".join(filter(None, [dug, addres, number]))

        # --------------------------------------------------------------------------------------------------------------
        structure_category_name = apg_dict.get('structure_category')
        structure_category_code = apg_dict.get('codice_categoria')
        structure_category = None
        if structure_category_name:
            structure_category_vals = {'name': structure_category_name, 'code': structure_category_code}
            structure_category = self.search_create_update('structure.category', 'name', structure_category_vals,
                                                           update=False)

        # --------------------------------------------------------------------------------------------------------------
        structure_zone_name = apg_dict.get('structure_zone')
        structure_zone = None
        if structure_zone_name:
            structure_zone_vals = {'name': structure_zone_name, 'company_id': company.id}
            structure_zone = self.search_create_update('structure.zone', 'name', structure_zone_vals, update=False)

        # --------------------------------------------------------------------------------------------------------------
        immobile_code = apg_dict.get('imm_code')
        immobile = None
        if immobile_code:
            # immobile_search_by_code = self.env['immobile.immobile'].search([('code_immobile_ids.code', '=', immobile_code)])
            immobile_search_by_id = self.env['immobile.immobile.codice'].search([('code', '=', immobile_code)])
            # if not immobile_search_by_code:
            #     msg = " - Found if search-by apg_id" if immobile_search_by_id else ""
            #     raise Exception(f"IMMOBILE({immobile_code}) search-by CodiceImmobile not found {msg}")
            #     # logging.warning(f'----------------------------- IMMOBILE: {immobile_code} NOT FOUND')
            # elif len(immobile_search_by_code) > 1:
            #     logging.warning(f'----------------------------- FOUND MULTIPLE IMMOBILE: {immobile_search_by_code.mapped(lambda x: x.id)}')
            #     immobile = immobile_search_by_code[0]
            immobile = immobile_search_by_id

        # --------------------------------------------------------------------------------------------------------------
        structure_code = apg_dict.get('structure_code')
        structure_name = apg_dict.get('structure_name')
        address_locale = apg_dict.get('address_locale')
        name_list = [str(structure_code), structure_name, address_locale]
        name = ' - '.join([x for x in name_list if x]) or "Non Definito"

        # --------------------------------------------------------------------------------------------------------------
        state = None
        country = self.sudo().env['res.country'].search([('code', '=', 'IT')], limit=1)
        state_code = apg_dict.get('address_province')
        if state_code:
            state = self.sudo().env['res.country.state'].search([('code', '=', state_code),
                                                                 ('country_id', '=', country.id)], limit=1)
        # --------------------------------------------------------------------------------------------------------------
        struttura_vals = {
            'name': name,
            'company_id': company.id if company else False,
            "date_open": self.get_date_obj(apg_dict, 'date_open'),
            "date_close": self.get_date_obj(apg_dict, 'date_close'),
            'capacity': int(apg_dict.get("capacity") or "0"),
            'city': address_locale,
            'zip': apg_dict.get('address_cap'),
            'street': street,
            'structure_code': structure_code,
            'structure_category_id': structure_category.id if structure_category else False,
            'structure_zone_id': structure_zone.id if structure_zone else False,
            'diocese': apg_dict.get('diocese'),
            'email': apg_dict.get('structure_email'),
            'phone': apg_dict.get('structure_phone'),
            'immobile_codice_id': immobile.id if immobile else False,
            'immobile_code': str(immobile_code),
            'state_id': state.id if state else False,
            'country_id': country.id if country else False,
            # -----
            'apg_id': unique_code,
            'data_hash': data_hash
        }
        return struttura_vals

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not 'name' in vals:
                structure_code = vals.get('structure_code')
                structure_name = 'Nome Struttura'
                address_locale = vals.get('address_locale')
                name_list = [structure_code, structure_name, address_locale]
                name = ' - '.join([x for x in name_list if x]) or "Non Definito"
                vals['name'] = name
        res = super().create(vals_list)
        return res
