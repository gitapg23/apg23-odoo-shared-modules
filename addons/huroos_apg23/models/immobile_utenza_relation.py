from odoo import fields, models, api, Command, _
import logging

RELATION_TYPE_SELECTION = [
    ('1-Persona', '1-Persona'), ('2-Imm+Strutt', '2-Imm+Strutt'), ('3-Strutt+Persona', '3-Strutt+Persona'),
    ('6-Immobile+campoLibero', '6-Immobile+campoLibero'), ('7-aDisposizione', '7-aDisposizione'),
    ('8-Serv+Persona', '8-Serv+Persona'), ('ALTRO', 'ALTRO')
]
class ImmobiliUtenzeRelation(models.Model):
    _name = "immobile.utenza.relation"
    _description = "APG23 | Modello per le relazioni di utilizzo delle Utenze"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string="Nome",
        help="Nome della relazione",
    )
    utenza_id = fields.Many2one(
        comodel_name='immobile.utenza',
        string='Utenza',
        help='Utenza cui la relazione si applica.'
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Azienda',
        related='utenza_id.company_id',
        store=True,
        readonly=True, 
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Persona',
        help='persona cui l’utenza è associata'
    )
    immobile_id = fields.Many2one(
        comodel_name='immobile.immobile',
        string='Immobile',
        help='Unità catastale cui l’utenza è associata, vecchio campo non più utilizzato, se in futuro si vorrà poter legare l utenza alla singola unità catastale riattivarlo filtrando secondo l immobile'
    )
    immobile_codice_id = fields.Many2one(
        comodel_name='immobile.immobile.codice',
        string='Immobile',
        help='Immobile cui l’utenza è associata'
    )
    # "Serv": json formattato come segue che restituisce tag e relativa categoria dei tag assegnati all’utenza (servono sempre tag colorati e categorizzati) "[{'CategoriaTag': 'FORNITURA ACQUA', 'Tags': ['RETE IDRICA']}]",
    struttura_id = fields.Many2one(
        comodel_name='onlus.struttura',
        string='Struttura',
        help='Struttura cui l’utenza è associata'
    )
    vehicle_id = fields.Many2one(
        comodel_name='fleet.vehicle',
        string='Automezzo',
        help='Automezzo cui l’utenza è associata'
    )
    relation_type = fields.Selection(
        selection=RELATION_TYPE_SELECTION,
        string='Tipo di relazione',
        help='Tipo di relazione di analitica'
    )
    data_a_utilizzo = fields.Date(string='Data A utilizzo',
                                   help='Data di chiusura della validità dell’utilizzo dell’utenza (Immobile e/o Struttura e/o Persona)')
    data_da_utilizzo = fields.Date(string='Data Da utilizzo',
                                   help='Data di partenza della validità dell’utilizzo dell’utenza (Immobile e/o Struttura e/o Persona)')
    immobile_code = fields.Char(
        string="Codice Immobile",
        help="Registra il campo 'Immobile' del tracciato d'importazione, anche quando il record a cui punta è assente."
    )
    structure_code = fields.Char(
        string="Codice Struttura",
        help="Registra il campo 'Struttura' del tracciato d'importazione, anche quando il record a cui punta è assente."
    )
    project_id = fields.Many2one(
        comodel_name='project.project',
        string="Codice Progetto",
        help="Da compilare a mano per gestione progetti."
    )
    
    @api.depends('utenza_id', 'data_da_utilizzo', 'data_a_utilizzo')
    def _compute_name(self):
        for record in self:
            utenza_name = record.utenza_id.name if record.utenza_id else ""

            data_da = record.data_da_utilizzo.strftime('%d/%m/%Y') if record.data_da_utilizzo else ""
            data_a = record.data_a_utilizzo.strftime('%d/%m/%Y') if record.data_a_utilizzo else ""

            record.name = " - ".join(filter(None, [utenza_name, f"Da: {data_da}", f"A: {data_a}"]))