from odoo import fields, models


class Website(models.Model):
    _inherit = "website"

    show_time_slots = fields.Boolean(
        string="Fascia oraria selezionabile al checkout",
        help="Nel checkout inserisce la possibilità di inserire una fascia oraria per la consegna."
    )
    show_time_range = fields.Boolean(
        string="Dettagli fascia oraria visibili",
        help="Visualizza i dettagli della fascia oraria (es: 'Mattina (9:00-12:00)')."
    )
