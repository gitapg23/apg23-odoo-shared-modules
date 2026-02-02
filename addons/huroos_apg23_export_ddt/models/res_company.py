# Copyright 2023-TODAY Rapsodoo Italia S.r.L. (www.rapsodoo.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import models, fields


class ResCompany(models.Model):
    _inherit = "res.company"

    so_ftp_host_export = fields.Char(
        string="FTP Host Export",
    )

    so_ftp_user_export = fields.Char(
        string="FTP User Export",
    )

    so_ftp_password_export = fields.Char(
        string="FTP Password Export",
    )

    so_ftp_path_export = fields.Char(
        string="Path Export",
    )

    so_ftp_operating_mode = fields.Selection(
        [('production', 'Production'), ('testing', 'Testing')], required=True, default="production", string="Operating Mode"
    )

    def get_jde_csv_export_ftp_param(self):
        return {
            'hostname': self.so_ftp_host_export,
            'username': self.so_ftp_user_export,
            'password': self.so_ftp_password_export,
            'path': self.so_ftp_path_export,
        }
