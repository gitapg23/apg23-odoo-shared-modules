import json
from odoo import fields, models, api, Command
import datetime
# solo test commit dodiane new
LIST_FUEL_TYPE = [('MISCELA', 'Miscela'),
                  ('BENZINA VERDE', 'Benzina Verde'),
                  ('G.P.L.', 'G.P.L'),
                  ('BENZINA SUPER', 'Benzina Super'),
                  ('METANO', 'Metano'),
                  ('Non Determinato', 'Non Determinato'),
                  ('DIESEL-GASOLIO', 'Diesel-Gasolio'),
                  ('IBRIDO', 'Ibridio'),
                  ('ELETTRICO', 'Elettrico')]

LIST_TYPE_CONTRACT = [
    ('PRESTITO', 'Prestito'),
    ('COMODATO', 'Comodato'),
    ('ACQUISTO', 'Acquisto'),
    ('LEASING', 'Leasing'),
    ('NOLEGGIO', 'Noleggio')]


class APGFleetVehicleModel(models.Model):
    _inherit = 'fleet.vehicle.model'

    default_fuel_type = fields.Selection(
        selection=LIST_FUEL_TYPE,
    )
    displacement = fields.Float(
        string="Cilindrata (cc)", help="Cilindrata (cc)"
    )
    massa = fields.Float(
        string="Massa (kg)", help="Massa (kg)"
    )

class APGFleetVehicleLogContract(models.Model):
    _inherit = 'fleet.vehicle.log.contract'

    type = fields.Selection(
        selection=LIST_TYPE_CONTRACT,
        string="Tipologia Contratto",
    )


class APGFleetVehicle(models.Model):
    _name = 'fleet.vehicle'
    _inherit = ['fleet.vehicle', 'apg.import.mixin']

    fuel_type = fields.Selection(
        selection=LIST_FUEL_TYPE,
    )
    displacement = fields.Float(
        string="Cilindrata (cc)", help="Cilindrata (cc)"
    )
    massa = fields.Float(
        string="Massa (kg)", help="Massa (kg)"
    )

    struttura_id = fields.Many2one(
        'onlus.struttura', string="Struttura"
    )

    evidenza = fields.Char(string="Evidenza")
    ZonaPr = fields.Char(string="ZonaPr")
    ZonaSt = fields.Char(string="ZonaSt")
    tipo = fields.Char(string="tipo")
    proprietario_id = fields.Many2one('res.company', string='Proprietario')
    proprietario_desc = fields.Char(string='Proprietario Descrizione',
                                    help="Campo che compare in aiuto quando proprietario_id non è un azienda interna.")

    def to_odoo_dict(self, apg_dict, data_hash, unique_code, send_data_type, hash_upd=False):
        """OVERRIDE di apg.import.mixin"""
        # apg_dict = {
        #
        # COMUNICARE:
        #  2) Campo AZCODAHE non sempre valorizzato, quando non valorizzato salto il record.
        #
        # WAITING:
        #   1) Mancano delle "company" esempio record: 4153, 2742, 4004 ... --> Attesa secondo invio
        #
        # NOTE
        #   Uniquecode: Automezzo | len: 85 | duplicati: 0
        #
        # ELIMINATI/NON IMPORTATI
        #   "AziInCarico":                  # direttive apg
        #   "Proprieta": "C ... COOP",      # Non usata, basta ProprietarioCod
        #
        # AGGIUNTI                          # ODOO
        #   "Cilindrata": "8.5",            # displacement
        #   "Massa": "222.1",               # massa
        #   "StrutturaCod": "0000000319",   # apg_id --> struttura_id
        #   "Struttura": "... PRONTO S",    # name ----> struttura_id
        #   "ZonaPr": "VNT",                # ZonaPr - campo di analitica
        #   "ZonaSt": "RIC",                # ZonaSt - campo di analitica
        #   "tipo": "00001",                # tipo   - campo di analitica
        #   "Evidenza": "In Demolizione",   # evidenza
        #
        # IMPORTATI                         # ODOO
        #   "Azienda": "ECP",               # company_id
        #   "Automezzo": "0000001576",      # unique_code
        #   "ProprietarioCod": "ECP",       # proprietario_id
        #   "Targa": "8ZCN8",               # license_plate
        #   "telaio": "0017954",            # vin_sn
        #   "Immatricolazione": "",         # acquisition_date
        #   "Persona": "... BARTOLOMEO",    # name ----> driver_id
        #   "PersonaCod": "0000000347",     # apg_id --> driver_id
        #   "Modello": "SALIM",             # name --------------> model_id
        #   "KW": "14.5",                   # power -------------> model_id
        #   "Alimentazione": "MISCELA",     # default_fuel_type -> model_id
        #   "Marca": "PIAGGIO",             # name -> brand_id --> model_id
        #   "Contratto": "0000001298",      # name --------------------> log_contracts
        #   "dal": "2003-09-15",            # start_date --------------> log_contracts
        #   "al": "",                       # expiration_date ---------> log_contracts
        #   "TipoContratto": "ACQUISTO",    # name -> cost_subtype_id -> log_contracts
        # }
        # --------------------------------------------------------------------------------------------------------------
        company = self.check_get_company(apg_dict, 'Azienda')

        # --------------------------------------------------------------------------------------------------------------
        fleet_service_type = apg_dict.get('Contratto')  # c'è sempre
        fleet_service_type_vals = {'name': fleet_service_type, 'category': 'contract'}
        fs_type = self.sudo().search_create_update('fleet.service.type', 'name', fleet_service_type_vals, update=False)
        cost_subtype_id = fs_type.id if fs_type else False

        # --------------------------------------------------------------------------------------------------------------
        contract_type = apg_dict.get("TipoContratto")
        contract_types = [item[0] for item in LIST_TYPE_CONTRACT]
        if contract_type not in contract_types:
            raise Exception(f"Contract type not found: {contract_type}")

        # --------------------------------------------------------------------------------------------------------------
        contract_name = apg_dict.get('Contratto')  # c'è sempre
        contract = self.sudo().env['fleet.vehicle.log.contract'].search([('name', '=', contract_name)], limit=1)
        start_date = self.get_date_obj(apg_dict, 'dal')
        expiration_date = self.get_date_obj(apg_dict, 'al')  # Sempre a 0 -> todo valutare di creare un placeholder
        if contract:
            command_log_contracts = [Command.link(contract.id)]
        else:
            command_log_contracts = [Command.create({
                'name': contract_name,
                'cost_subtype_id': cost_subtype_id,
                'start_date': start_date,
                'expiration_date': expiration_date,
                'type': contract_type,
            })]

        # --------------------------------------------------------------------------------------------------------------
        brand_name = apg_dict.get('Marca').capitalize()  # C'è sempre
        brand_vals = {'name': brand_name}
        brand = self.sudo().search_create_update('fleet.vehicle.model.brand', 'name', brand_vals, update=False)
        brand_id = brand.id if brand else False

        # --------------------------------------------------------------------------------------------------------------
        default_fuel_type = apg_dict.get("Alimentazione")
        displacement = float(apg_dict.get("Cilindrata") or "0")
        power = int(float(apg_dict.get("KW") or "0"))
        massa = float(apg_dict.get("Massa") or "0")
        model_name = apg_dict.get('Modello').capitalize()  # C'è sempre
        model_vals = {
            'name': model_name,
            'default_fuel_type': default_fuel_type,
            'displacement': displacement,
            'brand_id': brand_id,
            'power': power,
            'massa': massa,
        }
        model = self.sudo().search_create_update('fleet.vehicle.model', 'name', model_vals, update=False)
        model_id = model.id if model else False

        # --------------------------------------------------------------------------------------------------------------
        license_plate = apg_dict.get("Targa")
        vin_sn = apg_dict.get("telaio")
        acquisition_date = self.get_date_obj(apg_dict, 'Immatricolazione')

        # --------------------------------------------------------------------------------------------------------------
        driver_code = apg_dict.get('PersonaCod')
        driver = None
        if driver_code:
            driver_code = int(driver_code)
            # driver_code_fill = str(driver_code).replace('.0', '').zfill(10)
            driver = self.sudo().env['res.partner'].search([('hosted_id', '=', driver_code)], limit=1)
            if not driver:
                raise Exception(f"Driver not found: {driver_code}")

        # --------------------------------------------------------------------------------------------------------------
        struttura_code = apg_dict.get('StrutturaCod')
        struttura = None
        if struttura_code:
            struttura_code = str(struttura_code).replace('.0', '')
            struttura = self.sudo().env['onlus.struttura'].search([('structure_code', '=', struttura_code)])
            if not struttura:
                raise Exception(f"Struttura not found: {struttura_code}")

        # --------------------------------------------------------------------------------------------------------------
        proprietario_code = apg_dict.get("ProprietarioCod")
        proprietario = None
        if proprietario_code:
            proprietario = self.sudo().env['res.company'].search([('code', '=', proprietario_code)])

        # --------------------------------------------------------------------------------------------------------------
        # "ProprietarioCod" può contenere il "CodiceAzienda" delle company interne oppure  la descrizione della company
        # proprietaria. Se Non sono riuscito a valorizzare il field "proprietario" allora valorizzo "proprietario_desc"
        proprietario_desc = None
        if not proprietario:
            proprietario_desc = apg_dict.get("ProprietarioCod")

        # --------------------------------------------------------------------------------------------------------------
        # Campi custom temporanei
        evidenza = apg_dict.get("Evidenza")
        ZonaPr = apg_dict.get("ZonaPr")
        ZonaSt = apg_dict.get("ZonaSt")
        tipo = apg_dict.get("tipo")

        # --------------------------------------------------------------------------------------------------------------
        state_registered = self.env['fleet.vehicle.state'].search([('name', '=', 'Registrato')])

        # --------------------------------------------------------------------------------------------------------------
        vehicle_vals = {
            'model_id': model_id,
            'company_id': company.id,
            'license_plate': license_plate,
            'vin_sn': vin_sn,
            'acquisition_date': acquisition_date,
            'driver_id': driver.id if driver else False,
            'struttura_id': struttura.id if struttura else False,
            'log_contracts': command_log_contracts,
            'first_contract_date': start_date,
            'fuel_type': default_fuel_type,
            'displacement': displacement,
            'power': power,
            'massa': massa,
            'state_id': state_registered.id if state_registered else None,
            # -----
            'evidenza': evidenza,
            'ZonaPr': ZonaPr,
            'ZonaSt': ZonaSt,
            'tipo': tipo,
            'proprietario_id': proprietario.id if proprietario else False,
            'proprietario_desc': proprietario_desc,
            # -----
            'apg_id': unique_code,
            'data_hash': data_hash
        }

        return vehicle_vals
# TODO forse questo metodo va spostato nel modulo huroos_apg23_analitica
    def manage_after_creation(self, send_data_type, apg_dict):
        """Imposto nuovo piano analitico sugli automezzi se la company dell'automezzo è diversa
         dalla company del piano analitico corrente."""
        analytic_account = self.analytic_account_id
        if self.company_id != analytic_account.company_id:
            AUTOMEZZI_PIANO_ANALITICO = self.env['account.analytic.plan'].search([('name', '=', 'AUTOMEZZI')])

            if not AUTOMEZZI_PIANO_ANALITICO:
                raise Exception("Piano analitico AUTOMEZZI not found")

            new_analytic_account = self.env['account.analytic.account'].create({
                'name': self.license_plate,
                'company_id': self.company_id.id,
                'plan_id': AUTOMEZZI_PIANO_ANALITICO.id
            })
            self.analytic_account_id = new_analytic_account
        else:
            analytic_account.write({
                'name': self.license_plate
            })
       
            

