from odoo import fields, models, api, Command, _
import logging
import json
from datetime import date as datetime_date


class UtenzaCategoria(models.Model):
    _name = "utenza.categoria"

    name = fields.Char(string="Nome")
    tag_ids = fields.One2many('utenza.categoria.tag', 'category_id', string="Etichette")
    color = fields.Selection(
        [
            ('0', 'Nessun Colore'),
            ('1', 'Rosso'),
            ('2', 'Arancione'),
            ('3', 'Giallo'),
            ('4', 'Verde'),
            ('5', 'Blu'),
            ('6', 'Viola'),
            ('7', 'Rosa'),
            ('8', 'Marrone'),
            ('9', 'Grigio'),
        ],
        string="Colore",
        default='0',
        help="Colore associato alla categoria"
    )



class UtenzaCategoriaTag(models.Model):
    _name = "utenza.categoria.tag"

    name = fields.Char(string="Nome")
    utenze_ids = fields.Many2many('immobile.utenza', string="Utenze")
    category_id = fields.Many2one('utenza.categoria', string="Categoria")
    color = fields.Selection(
        related="category_id.color",
        string="Colore",
        store=True,
        readonly=True,
        help="Colore derivato dalla categoria"
    )


class ImmobiliUtenze(models.Model):
    _name = "immobile.utenza"
    _description = "APG23 | Modello per gestione Utenze"
    _inherit = ['apg.import.mixin', 'mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string="Nome",
        help="Nome dell'Utenza",
        compute="_compute_name",
        store=True
    )
    code = fields.Char(
        string="Codice",
        help="Codice Odoo dell'Utenza",
    )
    tag_ids = fields.Many2many(
        comodel_name='utenza.categoria.tag',
        string='Etichette',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Azienda',
        default=lambda s: s.env.company,
        help='Azienda intestataria dell’utenza',
    )
    company_tetto_id = fields.Many2one(
        comodel_name='res.company',
        string='Azienda Competenza',
        default=lambda s: s.env.company,
        help='azienda che deve avere il costo (in rarissimi casi differisce da Azienda). Il costo va eventualmente rifatturato.',
    )
    contract_code = fields.Char(
        string='Codice Contratto',
        help='codice del contratto su Arca',
    )
    fornitore_id = fields.Many2one(
        comodel_name='res.partner',
        string='Fornitore',
        help='Fornitore dell’utenza'
    )
    fornitore_desc = fields.Char(
        string='Descrizione Fornitore',
        help='nome del fornitore dell’utenza'
    )

    utenza_cod_arca = fields.Char(
        string='Utenza Codice su Arca',

    )

    company_code = fields.Char(
        string='Codice azienda'
    )
    utenza_cod_fornitore = fields.Char(
        string='Codice del fornitore',
        help='Servirà per la suddivisione dei costi e ricavi dell’analitica',

    )
    data_Attivazione = fields.Date(string='Data Attivazione', help='Data di attivazione dell’utenza', )
    data_chiusura = fields.Date(string='Data Chiusura', help='Data di chiusura dell’utenza', )
    data_disdetta = fields.Date(string='Data Disdetta', help='Data di disdetta dell’utenza', )
    data_richiesta = fields.Date(string='Data Richiesta', help='Data di richiesta dell’utenza', )
    data_richiestaRID = fields.Date(string='Data Richiesta RID', help='Data di richiesta RID dell’utenza', )
    data_scadenza = fields.Date(string='Data Scadenza', help='Data di scadenza dell’utenza', )
    data_utile_disdetta = fields.Date(string='Data Utile Disdetta', help='Data utile per la disdetta dell’utenza', )
    relation_ids = fields.One2many(
        comodel_name='immobile.utenza.relation',
        inverse_name='utenza_id',
        string='Utilizzo dell’utenza',
        help='Competenza dell’utilizzo dell’utenza.',
    )
    #aggiungo campi per compilare analitica, basati sull'utilizzo più recente
    struttura_id = fields.Many2one(
        comodel_name='onlus.struttura',
        string='Struttura',
        compute='_compute_utilizzo_relations',
        store=True,
        help='Struttura di utilizzo più recente',
    )

    immobile_id = fields.Many2one(
        comodel_name='immobile.immobile.codice',
        string='Immobile',
        compute='_compute_utilizzo_relations',
        store=True,
        help='Immobile di utilizzo più recente',
    )
    vehicle_id = fields.Many2one(
        comodel_name='fleet.vehicle',
        string='Automezzo',
        compute='_compute_utilizzo_relations',
        store=True,
        help='Automezzo di utilizzo più recente',
    )

    category_ids = fields.Many2many(
        comodel_name='utenza.categoria',
        string="Categorie",
        compute="_compute_category_ids",
        store=True
    )
    project_id = fields.Many2one(
        comodel_name='project.project',
        string="Codice Progetto",
        compute='_compute_utilizzo_relations',
        store=True,
        help="Progetto di utilizzo più recente",
    )

    sector_id = fields.Many2one('sector.sector', string="Settore", )
    specific_activity_id = fields.Many2one('specific.activity', string="Attività Specifica", )

    @api.depends('tag_ids.category_id')
    def _compute_category_ids(self):
        for record in self:
            record.category_ids = record.tag_ids.mapped('category_id')

    @api.depends('relation_ids.data_a_utilizzo', 'relation_ids.struttura_id', 'relation_ids.immobile_codice_id', 'relation_ids.vehicle_id', 'relation_ids.project_id')
    def _compute_utilizzo_relations(self):
        for record in self:
            relations = record.relation_ids
            if relations:
                selected_relation = relations.sorted(key=lambda r: (r.data_a_utilizzo or datetime_date.max, r.data_da_utilizzo or datetime_date.min, r.create_date), reverse=True)[0]
                record.struttura_id = selected_relation.struttura_id or False
                record.immobile_id = selected_relation.immobile_codice_id or False
                record.vehicle_id = selected_relation.vehicle_id or False
                record.project_id = selected_relation.project_id.id or False
            else:
                record.struttura_id = False
                record.immobile_id = False
                record.vehicle_id = False
                record.project_id = False

    @api.depends('relation_ids.data_a_utilizzo', 'relation_ids.data_da_utilizzo')
    def _compute_data_utilizzo(self):
        for record in self:
            valid_relations = record.relation_ids.filtered(
                lambda rel: not rel.data_a_utilizzo or rel.data_a_utilizzo > fields.Date.today()
            )
            if valid_relations:
                selected_relation = valid_relations.sorted(key=lambda r: r.data_da_utilizzo or fields.Date.today())[0]
                record.data_da_utilizzo = selected_relation.data_da_utilizzo
                record.immobile_codice_id = selected_relation.immobile_codice_id
                record.struttura_id = selected_relation.struttura_id
                record.partner_id = selected_relation.partner_id
            else:
                record.data_da_utilizzo = False
                record.immobile_codice_id = False
                record.struttura_id = False
                record.partner_id = False

    @api.depends('code', 'tag_ids', 'fornitore_id', 'utenza_cod_fornitore')
    def _compute_name(self):
        for record in self:
            code = record.code or ""
            
            tags = ", ".join(record.tag_ids.mapped('name')) if record.tag_ids else ""

            fornitore = record.fornitore_id.name if record.fornitore_id else ""

            cod_fornitore = record.utenza_cod_fornitore or f"da-definire-{record.utenza_cod_arca}"

            record.name = " - ".join(filter(None, [code, tags, fornitore, cod_fornitore]))


    def to_odoo_dict(self, apg_dict, data_hash, unique_code, send_data_type, hash_upd=False):
        # "Azienda": "EAO",
        # "AziendaTetto": "EAO",
        # "CodiceContratto": "4",
        # "DataAttivazione": "2007-01-01",
        # "DataChiusura": "",
        # "DataDaUtilizzo": "2007-01-01",
        # "DataDisdetta": "",
        # "DataRichiesta": "",
        # "DataRichiestaRID": "",
        # "DataScadenza": "",
        # "DataUtileDisdetta": "",
        # "FornitoreDescr": "HERA SPA",
        # "Immobile": "1.0",
        # "PersonaCodArca": "",
        # "Serv": "[{'CategoriaTag': 'FORNITURA ACQUA', 'Tags': ['RETE IDRICA']}]",
        # "Struttura": "1.0",
        # "TipoRelazione": "2-Imm+Strutt",
        # "UtenzaCodiceArca": "4",
        # "UtenzaCodiceFornitore": "['3000144481']"
        # --------------------------------------------------------------------------------------------------------------

        # NUOVI CAMPI NON PRESENTI NEI PRECEDENTI IMPORT
        # "DataAUtilizzo": "",
        # "FornitoreCfPiva": "[]",
        # "Immobile": 0,
        # "PersonaCodArca": 0,
        # "Struttura": 0,
        # "UtenzaCodiceArca": 4,

        company = self.check_get_company(apg_dict, 'Azienda')
        company_tetto = self.check_get_company(apg_dict, 'AziendaTetto', raise_exception=False)
        contract_code = apg_dict.get('CodiceContratto')
        fornitore_desc = apg_dict.get('FornitoreDescr')
        relation_type = apg_dict.get('TipoRelazione')
        utenza_cod_fornitore = apg_dict.get('UtenzaCodiceFornitore')
        if isinstance(utenza_cod_fornitore, str) and len(utenza_cod_fornitore) >= 4:
            utenza_cod_fornitore = utenza_cod_fornitore[2:-2]
        else:
            utenza_cod_fornitore = f"da-definire-{unique_code}"


        # da abilitare quando passiamo i cf dei fornitori--------------------------------------------------------------------------------------------------------------
        # partner_forn_code = apg_dict.get('FornitoreCfPiva')
        # # partner_code_fix = partner_code.zfill(10)
        # partner_forn = None
        # if partner_forn_code:
        #     partner_forn = self.env['res.partner'].sudo().search([('fiscalcode', '=', partner_forn_code)])
        #     num = len(partner_forn)
        #     logging.warning(f"Trovati {num} fornitori per {partner_forn_code}")
        #     if len(partner_forn) > 1:
        #         logging.warning(f"Più partner con stesso codice fiscale {partner_forn_code} --> Uso principale/beneficiario o il primo")
        #         partner_filtered = partner_forn.filtered(lambda p: p.partner_type_id.name in ['principale', 'beneficiari'])
        #         partner_forn = partner_filtered if partner_filtered else partner_forn[0]
        #     # if not partner_forn: 
        #     #     raise Exception(f"Field partner_forn_code {partner_forn_code} not found")


        fornitore_code = apg_dict.get('FornitoreCfPiva')
        fornitore_id = None
        try:
            if fornitore_code:
                fornitore_record = self.env['res.partner'].sudo().search([('fiscalcode', '=', fornitore_code)])
                logging.warning(f"Trovati {len(fornitore_record)} partner fornitore")
                
                if len(fornitore_record) > 1:
                    logging.warning(f"Più partner con stesso codice fiscale {fornitore_code} --> Uso principale/beneficiario o il primo")
                    fornitore_filtered = fornitore_record.filtered(lambda p: p.partner_type_id.name in ['principale', 'beneficiari'])
                    fornitore_record = fornitore_filtered if fornitore_filtered else fornitore_record[0]
                
                if fornitore_record:
                    fornitore_id = fornitore_record.id  # Passa solo l'ID
                else:
                    logging.warning(f"Field partner_code {fornitore_code} not found")
        except Exception as e:
            logging.error(f"Errore durante la ricerca del fornitore con codice fiscale {fornitore_code}: {e}", exc_info=True)



        # --------------------------------------------------------------------------------------------------------------
        partner_code = apg_dict.get('PersonaCodArca')
        # partner_code_fix = partner_code.zfill(10)
        try:
            partner = None
            if partner_code:
                partner = self.env['res.partner'].sudo().search([('hosted_id', '=', partner_code)])
                if len(partner) > 1:
                    logging.warning(f"Più partner con stesso hosted_id {partner_code} --> Uso principale/beneficiario")
                    partner_filtered = partner.filtered(lambda p: p.partner_type_id.name in ['principale', 'beneficiari'])[0]
                    partner = partner_filtered if partner_filtered else partner[0]
                if not partner:
                    logging.warning(f"Field partner_code {partner_code} not found")
        except Exception as e:
            logging.error(f"Errore durante la ricerca del partner con codice partner_code  {partner_code}: {e}", exc_info=True)

        # --------------------------------------------------------------------------------------------------------------
        structure_code = apg_dict.get('Struttura')
        structure = None
        if structure_code:
            structure = self.env['onlus.struttura'].sudo().search([('apg_id', '=', structure_code)])
            # if not structure:
            #     raise Exception(f"Field structure_code {structure_code} not found")

        # --------------------------------------------------------------------------------------------------------------
        immobile_code = apg_dict.get('Immobile')
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
        # --------------------------------------------------------------------------------------------------------------
        targa_code = apg_dict.get('Targa')
        veicolo = None
        try:
            if targa_code:
                veicolo_search_by_id = self.env['fleet.vehicle'].search([('license_plate', '=', targa_code)])
                if not veicolo_search_by_id:
                    logging.warning(f"Nessun veicolo trovato con targa {targa_code}")
                    veicolo = None
                elif len(veicolo_search_by_id) > 1:
                    logging.warning(f"Trovati più veicoli con la stessa targa {targa_code}: {[v.id for v in veicolo_search_by_id]}")
                    veicolo = veicolo_search_by_id[0]  # prende il primo
                else:
                    veicolo = veicolo_search_by_id  # singleton
        except Exception as e:
            logging.error(f"Errore durante la ricerca del veicolo con targa {targa_code}: {e}", exc_info=True)

        # --------------------------------------------------------------------------------------------------------------targa_id
        servs_str = apg_dict.get('Serv')
        servs_pt1 = servs_str.replace("RESPONSABILITA'", "RESPONSABILITA")
        servs_pt2 = servs_pt1.replace("PUBBLICITA'", "PUBBLICITA")
        servs_pt3 = servs_pt2.replace("\n", "'")
        servs_pt4 = servs_pt3.replace("'", '"')
        servs = json.loads(servs_pt4)
        tag_list = []
        for serv in servs:
            category_name = serv.get('CategoriaTag')
            tag_name_list = serv.get('Tags')
            tag_list = []
            category = self.search_create_update('utenza.categoria', 'name', {'name': category_name})
            for tag_name in tag_name_list:
                UtenzeCategoriaTag = self.env['utenza.categoria.tag']
                tag = UtenzeCategoriaTag.sudo().search([('name', '=', tag_name), ('category_id', '=', category.id)])
                if not tag:
                    tag_vals = {'name': tag_name, 'category_id': category.id}
                    tag = UtenzeCategoriaTag.sudo().create(tag_vals)
                tag_list.append(tag)

        # --------------------------------------------------------------------------------------------------------------
        # Creazione dei valori per immobile.utenza
        utenze_vals = {
            'name': self.env['ir.sequence'].next_by_code('immobile.utenza') or _('New'),
            'tag_ids': [Command.link(tag.id) for tag in tag_list],
            'company_id': company.id if company else None,
            'company_code': company.code if company else None,
            'company_tetto_id': company_tetto.id if company_tetto else None,
            'contract_code': contract_code,
            'fornitore_desc': fornitore_desc,
            'fornitore_id': fornitore_id,
            'utenza_cod_arca': unique_code,
            'utenza_cod_fornitore': utenza_cod_fornitore,
            'data_Attivazione': self.get_date_obj(apg_dict, 'DataAttivazione'),
            'data_chiusura': self.get_date_obj(apg_dict, 'DataChiusura'),
            'data_disdetta': self.get_date_obj(apg_dict, 'DataDisdetta'),
            'data_richiesta': self.get_date_obj(apg_dict, 'DataRichiesta'),
            'data_richiestaRID': self.get_date_obj(apg_dict, 'DataRichiestaRID'),
            'data_scadenza': self.get_date_obj(apg_dict, 'DataScadenza'),
            'data_utile_disdetta': self.get_date_obj(apg_dict, 'DataUtileDisdetta'),
            'apg_id': unique_code,
            'data_hash': data_hash
        }

        # Creazione dei valori per immobile.utenza.relation
        relation_vals = {
            'partner_id': partner.id if partner else None,
            # 'immobile_id': immobile.id if immobile else None,
            'immobile_codice_id': immobile.id if immobile else None,
            'struttura_id': structure.id if structure else None,
            'relation_type': relation_type,
            'data_a_utilizzo': self.get_date_obj(apg_dict, 'DataAUtilizzo'),
            'data_da_utilizzo': self.get_date_obj(apg_dict, 'DataDaUtilizzo'),
            'immobile_code': immobile_code,
            'structure_code': structure_code, 
            'vehicle_id': veicolo.id if veicolo else None,
        }

        utenze_vals['relation_vals'] = relation_vals


        return utenze_vals

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for vals in vals_list:
            if not 'code' in vals:
                vals['code'] = self.env['ir.sequence'].next_by_code('immobile.utenza') or _('New')
        return res

    # TODO forse questo metodo va spostato nel modulo huroos_apg23_analitica
    def manage_after_creation(self, send_data_type, apg_dict):
        analytic_account = self.analytic_account_id
        if self.company_id != analytic_account.company_id:
            UTENZE_PIANO_ANALITICO = self.env['account.analytic.plan'].search([('name', '=', 'UTENZE')])

            if not UTENZE_PIANO_ANALITICO:
                raise Exception("Piano analitico UTENZE not found")

            new_analytic_account = self.env['account.analytic.account'].create({
                'name': self.name,
                'company_id': self.company_id.id,
                'plan_id': UTENZE_PIANO_ANALITICO.id
            })
            self.analytic_account_id = new_analytic_account
        else:
            analytic_account.write({
                'name': self.name
            })
