from odoo import fields, models, api, Command, _
import json

DIRITTO_LIST_SELECTION = [
    ('comodato', 'COMODATO'), ('diritto_sup', 'Diritto Sup.'),
    ('usufrutto', 'Usufrutto'), ('locazione', 'LOCAZIONE')
]

INVERSE_DIRITTO_LIST_SELECTION = {v: k for k, v in DIRITTO_LIST_SELECTION}


class CodImmobile(models.Model):
    # Immobili come raggruppamenti di unità catastali
    _name = 'immobile.immobile.codice'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "APG23 | Modello per gestione Immobili"

    code = fields.Char(string="Codice Immobile", help="Attuale codice su ARCA")
    name = fields.Char(string="Immobile")
    immobile_ids = fields.Many2many('immobile.immobile', 'codice_id', 'immobile_id', string="Unità catastali")
    street = fields.Char(string="Strada")
    zip = fields.Char(string="CAP")
    locality = fields.Char(string="Localita")
    city = fields.Char(string="Citta")
    state_id = fields.Many2one(
        'res.country.state',
        string="Provincia",
        domain="[('country_id', '=?', country_id)]"
    )
    country_id = fields.Many2one(
        'res.country',
        string="Stato"
    )

    catasto_count = fields.Integer(
        string="Unità Catastali",
        compute="_compute_catasto_count",
        store=False
    )

    structure_ids = fields.One2many(
        comodel_name='onlus.struttura',
        inverse_name="immobile_codice_id",
        string='Strutture',
        help='Strutture presenti sull immobile'
    )


    structure_count = fields.Integer(
        string="Strutture",
        compute="_compute_structure_count",
        store=False
    )

    @api.depends('immobile_ids')
    def _compute_catasto_count(self):
        for record in self:
            record.catasto_count = len(record.immobile_ids)

    @api.depends('structure_ids')
    def _compute_structure_count(self):
        for record in self:
            record.structure_count = len(record.structure_ids)

    def action_view_catasto(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Unità catastali Associate',
            'view_mode': 'tree,form',
            'res_model': 'immobile.immobile',
            'domain': [('id', 'in', self.immobile_ids.ids)],
            'context': self.env.context,
        }
    
    def action_view_structure_imm(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Strutture Associate',
            'view_mode': 'tree,form',
            'res_model': 'onlus.struttura',
            'domain': [('id', 'in', self.structure_ids.ids)],
            'context': self.env.context,
        }

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not 'name' in vals:
                province_code = vals.get('state_id.code')
                code = vals.get('code')
                street = vals.get('street')
                city = vals.get('city')
                name_list = [code, street, city, province_code]
                name = ' - '.join([x for x in name_list if x]) or "Non Definito"
                vals['name'] = name
        res = super().create(vals_list)
        return res


class ImmobileImmobile(models.Model):
    # Immobili come unità catastali
    _name = 'immobile.immobile'
    _inherit = ['apg.import.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = "APG23 | Modello per gestione Catasto Immobili"

    zip = fields.Char(string="CAP")
    city = fields.Char(string="Citta")
    name = fields.Char(string="Unità catastale", )
    sheet = fields.Char(string="Foglio")
    street = fields.Char(string="Indirizzo")
    mappale = fields.Char(string="Mappale")
    locality = fields.Char(string="Localita")
    subalterno = fields.Char(string="Subalterno")
    code_comune_catastale = fields.Char(string="Codice Comune Catastale")
    type = fields.Selection([('terreno', 'Terreno'), ('immobile', 'Immobile')], string="Tipologia")
    owner_company = fields.Many2one('res.company', string="Proprietario")
    owner_from = fields.Date(string="Proprieta Da")
    owner_to = fields.Date(string="Proprieta A")
    owner_code_contract = fields.Char(
        string="Codice Contratto Proprietà",
        help="Elenco dei codici contratto relativi alla proprietà su ARCA")
    owner_millesimi = fields.Integer(string="Proprietario Millesimi")
    diritto_company = fields.Many2one('res.company', string="Azienda Diritto")
    diritto_from = fields.Date(string="Diritto Da")
    diritto_to = fields.Date(string="Diritto A")
    diritto_code_contract = fields.Char(
        string="Codice Contratto Diritto",
        help="Elenco dei codici contratto relativi a quel diritto su ARCA")
    diritto_millesimi = fields.Integer(string="Diritto Millesimi")
    code_immobile_ids = fields.Many2many(
        'immobile.immobile.codice',
        'immobile_id',
        'codice_id',
        string="Immobili",
        help="Immobile di cui fa parte questa unità catastale"
    )
    diritto = fields.Selection(
        string="Diritto",
        selection=DIRITTO_LIST_SELECTION
    )
    country_id = fields.Many2one(
        'res.country',
        string="Stato"
    )
    state_id = fields.Many2one(
        'res.country.state',
        string="Provincia",
        domain="[('country_id', '=?', country_id)]"
    )
    immobile_count = fields.Integer(
        string="Immobili",
        compute="_compute_immobile_count",
        store=False
    )


    @api.depends('code_immobile_ids')
    def _compute_immobile_count(self):
        for record in self:
            record.immobile_count = len(record.code_immobile_ids)

    def action_view_immobili(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Immobili Associati',
            'view_mode': 'tree,form',
            'res_model': 'immobile.immobile.codice',
            'domain': [('id', 'in', self.code_immobile_ids.ids)],
            'context': self.env.context,
        }

    def to_odoo_dict(self, apg_dict, data_hash, unique_code, send_data_type, hash_upd=False):
        """OVERRIDE di apg.import.mixin"""
        # apg_dict = {
        #
        # WAITNG:
        #   - "CodiceImmobile"                # Al momento salvato come char.
        #   - "Diritto/CodiceContratto'       # Al momento salvato come char.
        #   - "Proprietario/CodiceContratto'  # Al momento salvato come char.
        #
        # NOTE:
        #   Uniquecode: id
        #
        # FATTI
        #   "id": "602"                       # unique_code
        #   "Cap": "33061",                   # zip
        #   "Citta": "RIVIGNANO TEOR",        # city
        #   "Foglio": "27",                   # sheet
        #   "Mappale": "162",                 # mappale
        #   "SubAlterno": "",                 # subalterno
        #   "Locality": "MERCATALE",          # locality
        #   "Indirizzo": "VIA CUNZADIS 40",   # street
        #   "TipologiaImmobile": "terreno",   # type
        #   "CodComuneCatastale": "M317",     # code_comune_catastale
        #   "CodiceImmobile": "[1126]",       # code_immobile
        #   "Provincia": "UD",                # state_id
        #   "Diritto": "{
        #     'Diritto': 'COMODATO',          # diritto
        #     'AziendaDiritto': 'EAO',        # diritto_company
        #     'DirittoDa': '2013-04-24',      # diritto_from
        #     'DirittoA': None,               # diritto_to
        #     'Millesimi_dir': '1000',        # diritto_millesimi
        #     'CodiceContratto': [1208]       # diritto_code_contract
        #   }",
        #   "Proprietario": "{
        #     'Proprietario': 'EAS',          # owner_company
        #     'ProprietaDa': '2024-07-03',    # owner_from
        #     'ProprietaA': None,             # owner_to
        #     'Millesimi_prop': '1000',       # owner_millesimi
        #     'CodiceContratto': [2357]       # owner_code_contract
        #   }",
        # }
        # --------------------------------------------------------------------------------------------------------------
        code_immobile_str = apg_dict.get('CodiceImmobile')
        code_immobile_str_list = json.loads(code_immobile_str)
        code_immobile_ids = []
        if code_immobile_str_list:
            for code_immobile_code in code_immobile_str_list:
                code_immobile_vals = {'code': code_immobile_code}
                code_immobile = self.search_create_update('immobile.immobile.codice', 'code', code_immobile_vals)
                code_immobile_ids.append(code_immobile)

        # --------------------------------------------------------------------------------------------------------------
        country, state = None, None
        country_code = 'IT'
        state_code = apg_dict.get('Provincia')
        if country_code:
            country = self.env['res.country'].search([('code', '=', country_code)], limit=1)
        if state_code and country:
            state = self.env['res.country.state'].search([('code', '=', state_code), ('country_id', '=', country.id)],
                                                         limit=1)
        # --------------------------------------------------------------------------------------------------------------
        owner_dict = self.get_data_from_inner_field(apg_dict, 'Proprietario')
        owner_company, owner_from, owner_to, owner_millesimi, owner_code_contract = None, None, None, None, None
        if owner_dict:
            owner_code = owner_dict.get('Proprietario')
            if owner_code:
                owner_company = self.sudo().env['res.company'].search([('code', '=', owner_code)])
            owner_from = self.get_date_obj(owner_dict, 'ProprietaDa')
            owner_to = self.get_date_obj(owner_dict, 'ProprietaA')
            owner_millesimi = owner_dict.get('Millesimi_prop')
            owner_code_contract = owner_dict.get('CodiceContratto')

        # --------------------------------------------------------------------------------------------------------------
        diritto_dict = self.get_data_from_inner_field(apg_dict, 'Diritto')
        diritto_company, diritto_from, diritto_to, diritto_millesimi, diritto_code_contract, diritto = None, None, None, None, None, None
        if diritto_dict:
            diritto_code = diritto_dict.get('AziendaDiritto')
            if diritto_code:
                diritto_company = self.sudo().env['res.company'].search([('code', '=', diritto_code)])
            diritto_from = self.get_date_obj(diritto_dict, 'DirittoDa')
            diritto_to = self.get_date_obj(diritto_dict, 'DirittoA')
            diritto = INVERSE_DIRITTO_LIST_SELECTION.get(diritto_dict.get('Diritto'))
            diritto_millesimi = diritto_dict.get('Millesimi_dir')
            diritto_code_contract = diritto_dict.get('CodiceContratto')

        immobile_vals = {
            'zip': apg_dict['Cap'],
            'city': apg_dict['Citta'],
            'code_immobile_ids': [Command.link(x.id) for x in code_immobile_ids],
            'state_id': state.id if state else False,
            'country_id': country.id if country else False,
            'sheet': apg_dict['Foglio'],
            'type': apg_dict['TipologiaImmobile'],
            'street': apg_dict['Indirizzo'],
            'mappale': apg_dict['Mappale'],
            'locality': apg_dict['Localita'],
            'subalterno': apg_dict['SubAlterno'],
            'code_comune_catastale': apg_dict['CodComuneCatastale'],
            'owner_company': owner_company.id if owner_company else False,
            'owner_from': owner_from,
            'owner_to': owner_to,
            'owner_millesimi': owner_millesimi,
            'owner_code_contract': owner_code_contract,
            'diritto_company': diritto_company.id if diritto_company else False,
            'diritto_from': diritto_from,
            'diritto_to': diritto_to,
            'diritto': diritto,
            'diritto_millesimi': diritto_millesimi,
            'diritto_code_contract': diritto_code_contract,
            # -----
            'apg_id': unique_code,
            'data_hash': data_hash,
        }
        return immobile_vals

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        res.name = res.env['ir.sequence'].next_by_code('immobile.immobile') or _('New')
        return res
