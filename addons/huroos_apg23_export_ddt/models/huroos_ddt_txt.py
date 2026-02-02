from odoo import models, fields


class APGDDTHuroosDDTTxt(models.Model):
    _name = 'huroos.delivery.note.txt'

    name = fields.Char(string="Nome", related="file_name")

    file_data = fields.Binary(string="File")
    file_name = fields.Char(string="Nome File")