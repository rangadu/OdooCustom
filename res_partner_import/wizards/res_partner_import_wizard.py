# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ResPartnerImportWizard(models.Model):
    _name = 'res.partner.import.wizard'
    _description = 'Res Partner Import Wizard'

    file = fields.Binary("File", required=True)
    file_name = fields.Char("File Name")

    def action_import(self):
        """
        Read and import selected file
        """
        print('here')
