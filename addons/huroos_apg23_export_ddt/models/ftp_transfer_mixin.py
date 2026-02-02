# -*- coding: utf-8 -*-

from odoo import api, models, fields

from ftplib import FTP
import logging

logger = logging.getLogger(__name__)


class FtpTransferMixin(models.AbstractModel):
    _name = "ftp.transfer.mixin"

    def export_csv_to_ftp(self, file, filename):
        """funzione che esporta il file ftp generato nell'ftp di apg"""
        param = self.env.company.get_jde_csv_export_ftp_param()

        host_parts = param['hostname'].split(':')
        hostname = host_parts[0]
        port = int(host_parts[1]) if len(host_parts) > 1 else 21

        ftp = FTP()
        ftp.connect(hostname, port)

        ftp.login(param['username'], param['password'])
        logger.info("Connected to FTP server %s:%s", hostname, port)
        ftp.cwd(param['path'])
        logger.info("Changed to directory %s", param['path'])
        ftp.storbinary('STOR %s' % filename.replace('/', '_'), file)
        logger.info("File %s transfer success", filename)
        ftp.quit()