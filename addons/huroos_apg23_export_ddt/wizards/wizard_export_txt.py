# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
from ftplib import all_errors


class WizardExportTxt(models.TransientModel):
    _name = 'wizard.export.txt'
    _inherit = ["ftp.transfer.mixin"]

    ddt_id = fields.Many2one("huroos.delivery.note")
    file_io = fields.Binary(string="File")
    file_data = fields.Binary(string="File")
    file_name = fields.Char(string="Nome File")

    def _send_file_ftp(self):
        try:
            records = self.ddt_id._get_records()
            file_io, file_data, file_name = self.ddt_id._create_file(records)
            self.export_csv_to_ftp(file_io, file_name)
        except all_errors as e:
            raise UserError(
                f"FTP error: {str(e)}"
            )
        return True

    def _save_file(self):
        ddt_txt = self.env['huroos.delivery.note.txt'].create({
            'file_data': self.file_data,
            'file_name': self.file_name,
        })
        self.ddt_id.txt_id = ddt_txt

    def send_file_ftp(self):
        if self.env.company.so_ftp_operating_mode == 'production':
            ok = self._send_file_ftp()
            if ok:
                self._save_file()