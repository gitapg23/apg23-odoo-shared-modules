# Copyright 2023-TODAY Rapsodoo Italia S.r.L. (www.rapsodoo.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    so_ftp_host_export = fields.Char(
        related="company_id.so_ftp_host_export",
        readonly=False,
    )

    so_ftp_user_export = fields.Char(
        related="company_id.so_ftp_user_export",
        readonly=False,
    )

    so_ftp_password_export = fields.Char(
        related="company_id.so_ftp_password_export",
        readonly=False,
    )

    so_ftp_path_export = fields.Char(
        related="company_id.so_ftp_path_export",
        readonly=False,
    )

    so_ftp_operating_mode = fields.Selection(
        related="company_id.so_ftp_operating_mode",
        readonly=False,
    )
