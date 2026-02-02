from odoo import fields, models, api
from odoo.exceptions import UserError
import logging
import json


class Sector(models.Model):
    _name = 'sector.sector'

    name = fields.Char(string="Nome")
    descrizione_settore = fields.Char(string="Descrizione settore")
    id_settore = fields.Char(string="ID settore")
    analytic_account_id = fields.Many2one('account.analytic.account', string="Conto analitico")
    company_id = fields.Many2one('res.company', string="Azienda")
    utenza_ids = fields.One2many('immobile.utenza', 'sector_id', string="Utenze collegate")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('analytic_account_id'):
                #Se non è stato selezionato nessun conto analitico lo crea
                analytic_plan_id = self.env.ref('huroos_apg23_analitica.analytic_plan_settori')
                if not vals['name']:
                    raise UserError("Bisogna impostare un nome")
                name = str(vals['name']).upper()
                analytic_account_id = self.env['account.analytic.account'].sudo().search([
                    ('plan_id', '=', analytic_plan_id.id),
                    ('name', '=', name),
                    ('company_id', '=', vals.get('company_id', False))
                ], limit=1)
                if not analytic_account_id:
                    vals['analytic_account_id'] = self.env['account.analytic.account'].sudo().create({
                        'name': name.upper(),
                        'plan_id': analytic_plan_id.id,
                        'company_id': vals.get('company_id', False),
                    }).id
                else:
                    vals['analytic_account_id'] = analytic_account_id.id

        res = super(Sector, self).create(vals_list)
        return res

    def write(self, vals):
        """
        Override write to keep the analytic account synchronized.
        """
        res = super(Sector, self).write(vals)
        if 'name' in vals or 'company_id' in vals:
            for sector in self:
                if sector.analytic_account_id:
                    analytic_vals = {}
                    if 'name' in vals:
                        analytic_vals['name'] = (sector.name or '').upper()
                    if 'company_id' in vals:
                        analytic_vals['company_id'] = sector.company_id.id
                    if analytic_vals:
                        sector.analytic_account_id.sudo().write(analytic_vals)
        return res


class ActivitySpecific(models.Model):
    _name = 'specific.activity'

    name = fields.Char(string="Nome")
    descrizione_attivita = fields.Char(string="Descrizione attivita")
    id_attivita = fields.Char(string="ID attivita")
    data_inizio_commessa = fields.Date(string="Data inizio commessa")
    data_fine_commessa = fields.Date(string="Data fine commessa")
    sector_id = fields.Many2one('sector.sector', string="Settore")
    analytic_account_id = fields.Many2one('account.analytic.account', string="Conto analitico")
    company_id = fields.Many2one('res.company', string="Azienda")
    utenza_ids = fields.One2many('immobile.utenza', 'specific_activity_id', string="Utenze collegate")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('analytic_account_id'):
                # Se non è stato selezionato nessun conto analitico lo crea
                analytic_plan_id = self.env.ref('huroos_apg23_analitica.analytic_plan_attivita_specifiche')
                if not vals['name']:
                    raise UserError("Bisogna impostare un nome")
                name = str(vals['name']).upper()
                analytic_account_id = self.env['account.analytic.account'].sudo().search([
                    ('plan_id', '=', analytic_plan_id.id),
                    ('name', '=', name),
                    ('company_id', '=', vals.get('company_id', False))
                ], limit=1)
                if not analytic_account_id:
                    vals['analytic_account_id'] = self.env['account.analytic.account'].sudo().create({
                        'name': name.upper(),
                        'plan_id': analytic_plan_id.id,
                        'company_id': vals.get('company_id', False),
                    }).id
                else:
                    vals['analytic_account_id'] = analytic_account_id.id

        res = super(ActivitySpecific, self).create(vals_list)
        return res

    def write(self, vals):
        """
        Override write to keep the analytic account synchronized.
        """
        res = super(ActivitySpecific, self).write(vals)
        if 'name' in vals or 'company_id' in vals:
            for activity in self:
                if activity.analytic_account_id:
                    analytic_vals = {}
                    if 'name' in vals:
                        analytic_vals['name'] = (activity.name or '').upper()
                    if 'company_id' in vals:
                        analytic_vals['company_id'] = activity.company_id.id
                    if analytic_vals:
                        activity.analytic_account_id.sudo().write(analytic_vals)
        return res

    def import_sector_activity(self):
        """
        Importa o aggiorna i settori e le attività specifiche da apg.send.data.
        Questa versione è ottimizzata per ridurre le query al database.
        """
        apg_data_ids = self.env['apg.send.data'].search([('type', '=', 'SETTORI'), ('active', '=', True)])
        if not apg_data_ids:
            logging.info("Nessun dato 'SETTORI' da importare.")
            return

        Sector = self.env['sector.sector']
        Activity = self.env['specific.activity']

        for apg_data in apg_data_ids:
            try:
                json_data = json.loads(apg_data.json)
            except json.JSONDecodeError:
                logging.error(f"Errore nel parsing del JSON per apg.send.data ID: {apg_data.id}")
                continue
            
            # Pre-carica le aziende per evitare query multiple nel ciclo
            company_codes = {rec.get('Azienda') for rec in json_data if rec.get('Azienda')}
            companies = {c.code: c.id for c in self.env['res.company'].search([('code', 'in', list(company_codes))])}

            # 1. Raccogli tutti gli ID dal JSON
            sector_ids_json = {rec['id_settore'] for rec in json_data if rec.get('id_settore')}
            activity_ids_json = {rec['id_commessa'] for rec in json_data if rec.get('id_commessa')}

            # 2. Cerca in blocco i record esistenti
            existing_sectors = {s.id_settore: s for s in Sector.search([('id_settore', 'in', list(sector_ids_json))])}
            existing_activities = {a.id_attivita: a for a in Activity.search([('id_attivita', 'in', list(activity_ids_json))])}

            sectors_to_create = []
            activities_to_create = []

            for record in json_data:
                # 3. Gestione Settori
                sector_id_json = record.get('id_settore')
                sector_name = record.get('desc_settore')
                company_code = record.get('Azienda')
                if not sector_id_json or not sector_name:
                    continue

                company_id = companies.get(company_code)
                sector_vals = {
                    'name': sector_name,
                    'descrizione_settore': sector_name,
                    'id_settore': sector_id_json,
                    'company_id': company_id,
                }
                sector = existing_sectors.get(sector_id_json)
                if not sector:
                    # Aggiungi alla lista per la creazione in blocco
                    sectors_to_create.append(sector_vals)
                else:
                    sector.write(sector_vals)

            # Crea i nuovi settori in blocco e aggiorna la mappa
            if sectors_to_create:
                new_sectors = Sector.create(sectors_to_create)
                for s in new_sectors:
                    existing_sectors[s.id_settore] = s
                logging.info(f"ASSET: Creati {len(new_sectors)} nuovi settori.")

            # 4. Gestione Attività
            for record in json_data:
                activity_id_json = record.get('id_commessa')
                activity_name = record.get('desc_commessa')
                sector_id_json = record.get('id_settore')
                company_code = record.get('Azienda')
                if not activity_id_json or not activity_name or not sector_id_json:
                    continue

                sector = existing_sectors.get(sector_id_json)
                company_id = companies.get(company_code)
                activity_vals = {
                    'name': activity_name,
                    'descrizione_attivita': activity_name,
                    'id_attivita': activity_id_json,
                    'data_inizio_commessa': record.get('data_inizio_commessa') or False,
                    'data_fine_commessa': record.get('data_fine_commessa') or False,
                    'sector_id': sector.id if sector else False,
                    'company_id': company_id,
                }

                activity = existing_activities.get(activity_id_json)
                if not activity:
                    activities_to_create.append(activity_vals)
                else:
                    activity.write(activity_vals)

            if activities_to_create:
                Activity.create(activities_to_create)
                logging.info(f"ASSET: Create {len(activities_to_create)} nuove attività.")

            apg_data.write({'active': False})