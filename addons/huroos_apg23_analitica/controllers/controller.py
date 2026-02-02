# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import http
from odoo.http import request,content_disposition
import base64
import os, os.path
import csv
from os import listdir
import sys


class Download_xls(http.Controller):

    @http.route('/web/binary/download_report', type='http', auth="public")
    def download_report(self, model, id, **kw):
        if model == 'scheda.tetto':
            record = request.env[model].browse(int(id))
            filename,xlsx_data = record.generate_xls_report()
            return request.make_response(xlsx_data,headers=[('Content-Type', 'application/vnd.ms-excel'), ('Content-Disposition', content_disposition(filename))],)
