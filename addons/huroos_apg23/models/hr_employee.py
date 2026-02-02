from odoo import fields, models, api, Command
import logging

# M o F, gender other ??
MAP_GENDER_APG_ODOO = {'M': 'male','F': 'female'}

MAP_DIPENDENTE_TIPE_APG_ODOO = {'PROG': 'PROG', 'TIR': 'trainee', 'DIPE': 'employee', 'OCCA': 'OCCA'}

MAP_ACTIVE_APG_ODOO = {'VERO': True, 'FALSE': False, 'FALSO': False, "": False}

MAP_MARITAL_APG_ODOO = {'Celibe/nubile': 'single', 'Sposato/a': 'married', 'Coabitante legale': 'cohabitant',
                        'Vedovo': 'widower', 'Divorziato/a': 'divorced', "": ""}


class APGHrDepartment(models.Model):
    _inherit = 'hr.department'

    structure_id = fields.Many2one("onlus.struttura", string="Struttura")


class APGWorkLocation(models.Model):
    _inherit = 'hr.work.location'

    department_id = fields.Many2one("hr.department", string="Dipartimento")


class APGHrResumeLine(models.Model):
    _inherit = 'hr.resume.line'

    resource_calendar_id = fields.Many2one('resource.calendar', 'Ore di Lavoro')
    matricola = fields.Char(string='Matricola')
    parent_code = fields.Char(string="Supervisore Codice Arca")
    employee_type = fields.Selection(
        string="Tipo Lavoratore",
        selection=[
            ('employee', 'Impiegato'), ('student', 'Studente'), ('trainee', 'Tirocinio'), ('contractor', 'Contratto'),
            ('freelance', 'Freelancer'), ('PROG', "Lavoratore a Progetto"), ('OCCA', "Lavoratore Occasionale")],
        ondelete={'PROG': 'set default', 'OCCA': 'set default'}
    )
    marital = fields.Selection(
        string="Tipo Lavoratore",
        selection=[('single', 'Celibe/nubile'), ('married', 'Sposato/a'), ('cohabitant', 'Coabitante legale'),
                   ('widower', 'Vedovo'), ('divorced', 'Divorziato/a')],
        ondelete={'PROG': 'set default', 'OCCA': 'set default'}
    )


class APGHrEmployee(models.Model):
    _name = 'hr.employee'
    _inherit = ['hr.employee', 'apg.import.mixin']

    employee_type = fields.Selection(
        selection_add=[('PROG', "Lavoratore a Progetto"),
                       ('OCCA', "Lavoratore Occasionale")],
        ondelete={'PROG': 'set default', 'OCCA': 'set default'}
    )
    commessa_netto = fields.Char(string='Commessa Netto', help="Campo per Analitica")
    commessa_costo = fields.Char(string='Commessa Costo', help="Campo per Analitica")
    matricola = fields.Char(string='Matricola')
    # data_avvio_contratto = fields.Date(string='Data Avvio Contratto')  # Già messo in resume_lines
    # data_uscita = fields.Date(string="Data Uscita")                    # Già messo in resume_lines
    codice_persona = fields.Char(string="Codice Persona")
    contatto_di_lavoro_name = fields.Char(string='Contatto Di Lavoro Name')
    scadenza_prossima_attivita = fields.Date(string='Scadenza Prossima Attività')
    provincia_di_nascita = fields.Many2one(
        'res.country.state', string="Provincia di Nascita"
    )

    # OVERRIDE
    def to_odoo_dict(self, apg_dict, data_hash, unique_code, send_data_type, hash_upd=False):
        """OVERRIDE di apg.import.mixin"""
        # apg_dict = {
        #
        # WAITING
        #   1) nella chiave "PersonaCod" ci sono duplicati
        #
        # NOTE
        #   - Uniquecode: PersonaCod | len: 1172 | duplicated: 23 | duplicated-set: 10
        #   - Non effettuare la creazione dello User.
        #   - I contatti creati hanno codice_apg: "DIPENDENTE: {codice_persona}"
        #   - Fine import -> Togliere riferimenti a Supervisore “se stesso” e mettere l’impiegato come suo supervisore
        #
        # MANCANTI/DUBBI
        #   "CopiaCartaIdentit\u00e0": "", # non importato - SEMPRE '' - sarebbe un char?
        #   "PatenteDiGuida": "",          # non importato - SEMPRE '' - sarebbe un char?
        #
        # ELIMINATI/NON IMPORTATI
        #   "Istruttore":                             # direttive apg
        #   "adcodazi":                               # direttive apg
        #   "NrSSN":                                  # direttive apg
        #   "Attivit\u00e0":                          # direttive apg
        #   "StatoCivile":                            # direttive apg
        #
        # AGGIUNTI                                    # ODOO
        #   "Matricola": "957.0",                     # matricola
        #   "ProvinciaDiNascita": "",                 # country_of_birth
        #   "DataAvvioContratto": "2021-10-01",       # data_avvio_contratto
        #   "DataDiUscita": "",                       # data_uscita
        #   "ContattoDiLavoroName": "SEVERI DANIELE", # contatto_di_lavoro_name    - SEMPRE = a NomeDipendente
        #   "ScadenzaProssimaAttivit\u00e0": "",      # scadenza_prossima_attivita - SEMPRE ''
        #   "CommessaNetto": "RMG01331",              # commessa_netto
        #   "CommessaCosto": "VNT00642",              # commessa_costo
        #
        # IMPORTATI                                   # ODOO
        #   "PersonaCod": "0000003797",               # codice_persona, uniquecode
        #   "TipoDiDipendente": "DIPE",               # employee_type
        #   "Note": "",                               # notes
        #   "NVisto": "",                             # visa_no
        #   "NomeDipendente": "SEVERI DANIELE",       # name
        #   "Cognome": "DANIELE",                     # Salvato per res.partner -> firstname
        #   "Nome": "SEVERI",                         # Salvato per res.partner -> lastname
        #   "CodiceFiscale": "SVRDNL66E04Z133T",      # Salvato per res.partner -> fiscalcode
        #   "cap": "47121",                           # private_zip
        #   "Nazione": "ITA",                         # private_country_id e country_id
        #   "provincia": "FC",                        # private_state
        #   "cellulare": "FC (ITA)",                  # private_phone
        #   "CittaPrivata": "FORLI'",                 # private_city
        #   "StradaPrivata": "VIALE BIDENTE 241",     # private_street
        #   "EmailPrivata": "chiodoni@studio.it",     # private_email
        #   "LuogoDiNascita": "",                     # place_of_birth
        #   "NazioneDiNascita": "CHE",                # country_of_birth
        #   "DataDiNascita": "1966-05-04",            # birthday
        #   "Sesso": "M",                             # gender <-- MAP_GENDER_APG_ODOO
        #   "Azienda": "EAO",                         # company_id
        #   "Attivo": "VERO",                         # active
        #   "TelefonoUfficio": "",                    # work_phone
        #   "CellulareUfficio": "",                   # mobile_phone
        #   "DocIdentificativo": "",                  # identification_id <- è un char
        #   "DistanzaCasaLavoro": "",                 # km_home_work
        #   "IndirizzoLavoro": "EAO",                 # address_id
        #   "Dipartimento": "0000001331",             # department_id
        #   "ContattoTelefono": "0543779429",         # emergency_phone
        #   "EmailLavoro": "dsapg23@gmail.com",       # work_email - quando è assente non posso creare l'utente
        #   "Supervisore": "SEVERI DANIELE",          # parent_id
        #   "SupervisoreCodArca": "0000003797",       # parent_id
        #   "PosizioneLavorativa": "COOPERATIVE SOCIALI - LIV D2 EX 6\u00b0LIV - EDUCATORE PROFESSIONALE",  # job_name
        # }
        # --------------------------------------------------------------------------------------------------------------
        # Estraggo i campi custom aggiunti sul modello
        scadenza_prossima_attivita = self.get_date_obj(apg_dict, 'ScadenzaProssimaAttivit\u00e0')
        contatto_di_lavoro_name = apg_dict.get('ContattoDiLavoroName')
        # data_avvio_contratto = self.get_date_obj(dati_contratto_last, 'DataAvvioContratto')
        # data_uscita = self.get_date_obj(dati_contratto_last, 'DataDiUscita')

        # --------------------------------------------------------------------------------------------------------------
        # Estraggo le relative all'ultimo contratto
        dati_contratto = self.get_data_from_inner_field(apg_dict, 'DatiContratto')
        dati_contratto_last = dati_contratto[-1] if dati_contratto else None
        dati_contratto_last = self.from_listdict_to_dict(dati_contratto_last)
        matricola = dati_contratto_last.get('Matricola')
        job_name = dati_contratto_last.get('PosizioneLavorativa')
        parent_code = dati_contratto_last.get('SupervisoreCodArca')
        weekly_work_hours = dati_contratto_last.get('OreContratto')
        employee_type_apg = dati_contratto_last.get('TipoDiDipendente')
        employee_type = MAP_DIPENDENTE_TIPE_APG_ODOO.get(employee_type_apg)

        # --------------------------------------------------------------------------------------------------------------
        name = apg_dict.get('NomeDipendente')
        codice_persona = apg_dict.get('PersonaCod')
        fiscalcode = apg_dict.get('CodiceFiscale')

        # --------------------------------------------------------------------------------------------------------------
        company = self.check_get_company(apg_dict, 'Azienda')
        company2 = self.check_get_company(apg_dict, 'IndirizzoLavoro')
        address_id = company2.partner_id.id or None
        birthday = self.get_date_obj(apg_dict, 'DataDiNascita')

        # --------------------------------------------------------------------------------------------------------------
        private_country, private_state = self.get_country_and_state(apg_dict, 'Nazione', 'provincia')
        country = private_country
        country_of_birth, state_of_birth = self.get_country_and_state(apg_dict, 'NazioneDiNascita',
                                                                      'ProvinciaDiNascita')
        code = (country or country_of_birth).code if (country or country_of_birth) else None
        lang = 'it_IT' if code == 'IT' else 'en_US'

        # --------------------------------------------------------------------------------------------------------------
        rsrc_calendar = None
        if weekly_work_hours not in ["0", "0.0", "nan", "NaN", "None"]:
            rsrc_calendar_vals = {"name": f"{weekly_work_hours} ore/settimana"}
            rsrc_calendar = self.search_create_update('resource.calendar', 'name', rsrc_calendar_vals, update=False)

        # --------------------------------------------------------------------------------------------------------------
        job = None
        if job_name:
            job_vals = {'name': job_name, 'company_id': company.id}
            job = self.search_create_update('hr.job', 'name', job_vals, update=False)

        # --------------------------------------------------------------------------------------------------------------
        parent_name = apg_dict.get('Supervisore')
        parent_code_str = 'DIP' + str(parent_code)
        if company:
            parent_code_str = parent_code_str + '_' + company.code
        if parent_code_str == unique_code:  # Se la risorsa ha come supervisore "se stesso" uso un placeholder da sostituire
            parent = self.env.ref('huroos_apg23.hr_employee_parent_placeholder')
        elif parent_code:
            parent_name = parent_name or parent_code_str
            parent_other_vals = {'employee_type': 'employee', 'company_id': company.id, 'codice_persona': parent_code}
            parent = self.sudo().search_create_by_apg_id('hr.employee', parent_name, parent_code_str, parent_other_vals)
        else:
            parent = False

        iban = apg_dict.get('IBAN')
        command_bank_ids = None
        if iban:
            bank = self.env.ref('huroos_apg23.res_bank_placeholder')
            command_bank_ids = [Command.create({'bank_id': bank.id, 'acc_number': iban})]

        # --------------------------------------------------------------------------------------------------------------
        # if ash_upd: # TODO-hash_upd: check {unique_code} also write
        #     ex_employee = self.sudo().search([('apg_id', '=', unique_code)], limit=1)
        #     partner = ex_employee.work_contact_id
        # else:
        #     .... il codice seguente
        partner_vals = {
            'state_id': private_state.id if private_state else False,
            'country_id': private_country.id if private_country else False,
            'fiscalcode': fiscalcode,
            'is_company': False,
            'bank_ids': command_bank_ids,
            'name': name,
            'function': job_name,
            'comment': apg_dict.get('Note'),
            'codice_apg': f'DIPENDENTE: {codice_persona}',
            # ---------
            'apg_id': unique_code,
            'data_hash': f"creato da impiegato apg_id {unique_code}"
        }
        partner = self.sudo().env['res.partner'].search([('fiscalcode', '=', fiscalcode)])
        if partner and fiscalcode:
            for rec in partner:
                # Delete empty key from partner_vals
                filtered_partner_vals = {k: v for k, v in partner_vals.items() if not rec[k]}
                if rec['is_company']:
                    filtered_partner_vals['is_company'] = rec['is_company']
                    filtered_partner_vals['lastname'] = rec['lastname']
                rec.sudo().write(filtered_partner_vals)
                msg = f"Trovato stesso CF({fiscalcode}) in DIPENDENTI"
                self.sudo().write_chatter_note(msg, rec.id, rec._name)
        else:
            partner_vals['parent_id'] = company.partner_id.id if company else False
            partner = self.sudo().env['res.partner'].create(partner_vals)

        # --------------------------------------------------------------------------------------------------------------
        structure_code = apg_dict.get('Dipartimento')
        structure = None
        department = None
        work_location = None
        if structure_code:
            structure = self.env['onlus.struttura'].sudo().search([('apg_id', '=', structure_code)])
            if not structure:
                raise Exception(f"structure {structure_code} not found")
        if structure:
            department_vals = {'name': structure.name, 'company_id': company.id, 'structure_id': structure.id}
            department = self.search_create_update('hr.department', 'name', department_vals, update=False)
        if department and structure:
            work_location_vals = {
                'name': structure.get_address_string(),
                'company_id': company.id,
                'department_id': department.id,
                'address_id': company.partner_id.id
            }
            work_location = self.search_create_update('hr.work.location', 'name', work_location_vals, update=False)

        # --------------------------------------------------------------------------------------------------------------
        employee_vals = {
            'job_id': job.id if job else False,
            'parent_id': parent.id if parent else False,
            'company_id': company.id if company else False,
            # 'country_id': country.id if country else False,
            'department_id': department.id if department else False,
            'work_location_id': work_location.id if work_location else False,
            'private_state_id': private_state.id if private_state else False,
            'private_country_id': private_country.id if private_country else False,
            'country_of_birth': country_of_birth.id if country_of_birth else False,
            'resource_calendar_id': rsrc_calendar.id if rsrc_calendar else False,
            'lang': lang,
            'name': name,
            'gender': MAP_GENDER_APG_ODOO[apg_dict.get('Sesso')],  # C'è sempre. M o F, gender other ??,
            'active': MAP_ACTIVE_APG_ODOO[apg_dict.get('Attivo')],
            'visa_no': apg_dict.get('NVisto'),
            'birthday': birthday,
            'address_id': address_id,
            'employee_type': employee_type,
            'place_of_birth': apg_dict.get('LuogoDiNascita'),
            'work_email': apg_dict.get('EmailLavoro'),
            'private_email': apg_dict.get('EmailPrivata'),
            'private_zip': apg_dict.get('cap'),
            'private_city': apg_dict.get('CittaPrivata'),
            'private_street': apg_dict.get('StradaPrivata'),
            'private_phone': apg_dict.get('cellulare'),  # Telefono,
            'mobile_phone': apg_dict.get('CellulareUfficio'),  # Cellulare ufficio
            'work_phone': apg_dict.get('TelefonoUfficio'),  # Telefono ufficio
            'emergency_phone': apg_dict.get('ContattoTelefono'),  # Contatto telefono
            'identification_id': apg_dict.get('DocIdentificativo'),
            'km_home_work': apg_dict.get('DistanzaCasaLavoro'),
            'notes': apg_dict.get('Note'),
            'sinid': fiscalcode,
            'work_contact_id': partner[0].id,
            'marital': MAP_MARITAL_APG_ODOO[apg_dict.get('StatoCivile')],
            # -----
            'scadenza_prossima_attivita': scadenza_prossima_attivita,
            'contatto_di_lavoro_name': contatto_di_lavoro_name,
            # 'data_avvio_contratto': data_avvio_contratto, # Già messo in resume_lines
            # 'data_uscita': data_uscita,                   # Già messo in resume_lines
            'provincia_di_nascita': state_of_birth.id if state_of_birth else False,
            'matricola': matricola,
            'codice_persona': codice_persona,
            'commessa_netto': apg_dict.get('CommessaNetto'),
            'commessa_costo': apg_dict.get('CommessaCosto'),
            # -----
            'apg_id': unique_code,
            'data_hash': data_hash
        }

        return employee_vals

    def manage_after_creation(self, send_data_type, apg_dict):
        """Metodo eseguito dopo la creazione o sul obj_id recuperato tramite hashcode,
         serve per modificare i campi del record non gestibili tramite write e create"""

        dati_contratto = self.get_data_from_inner_field(apg_dict, 'DatiContratto')
        self.resume_line_ids.unlink()
        resume_lines = []
        for contratto in dati_contratto:
            contratto = self.from_listdict_to_dict(contratto)
            matricola = contratto.get('Matricola')
            description = contratto.get('PosizioneLavorativa')
            parent_code = contratto.get('SupervisoreCodArca')
            date_end = self.get_date_obj(contratto, 'DataDiUscita')
            date_start = self.get_date_obj(contratto, 'DataAvvioContratto')
            employee_type_apg = contratto.get('TipoDiDipendente')
            employee_type = MAP_DIPENDENTE_TIPE_APG_ODOO.get(employee_type_apg)
            weekly_work_hours = contratto.get('OreContratto')
            rsrc_calendar = None
            if weekly_work_hours not in ["0", "0.0", "nan", "NaN", "None"]:
                rsrc_calendar_vals = {"name": f"{weekly_work_hours} ore/settimana"}
                rsrc_calendar = self.search_create_update('resource.calendar', 'name', rsrc_calendar_vals, update=False)

            resume_line_vals = {
                'date_end': date_end,
                'date_start': date_start,
                'name': description,
                'line_type_id': 1,
                'resource_calendar_id': rsrc_calendar.id if rsrc_calendar else False,
                'matricola': matricola,
                'parent_code': parent_code,
                'employee_type': employee_type,
                'employee_id': self.id,
            }
            resume_lines.append(resume_line_vals)
        self.sudo().env['hr.resume.line'].create(resume_lines)

