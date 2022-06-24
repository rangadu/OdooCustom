# -*- coding: utf-8 -*-

import xlrd
import csv
import base64

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ResPartnerImportWizard(models.Model):
    _name = 'res.partner.import.wizard'
    _description = 'Res Partner Import Wizard'

    # dbo entity
    dbo_entity_file = fields.Binary("DBO Entity File", required=True)
    dbo_entity_file_name = fields.Char("DBO Entity File Name")
    # dbo_entity_address
    dbo_entity_address_file = fields.Binary("DBO Entity Address File")
    dbo_entity_address_file_name = fields.Char("DBO Entity Address File Name")
    # dbo entity contact
    dbo_entity_contact_file = fields.Binary("DBO Entity Contact File")
    dbo_entity_contact_file_name = fields.Char("DBO Entity Contact File Name")

    def _read_xlsx_file(self, file, cell_data):
        """
        Read .xlsx type files
        """
        vals = []
        counter = 1
        skipped_line_no = {}
        try:
            workbook = xlrd.open_workbook(file_contents=base64.decodebytes(file))
            sheet = workbook.sheet_by_index(0)

            for row in range(sheet.nrows):
                if row > 1:  # skip header lines
                    try:
                        data = {}
                        for rec in cell_data:
                            if sheet.cell(row, rec).value != '':
                                data.update({cell_data[rec]: sheet.cell(row, rec).value})
                        vals.append(data)
                    # TODO: Add a popup to display invalid lines
                    except Exception as e:
                        skipped_line_no[str(counter)] = " - Value is not valid " + str(e)
                        counter += 1
                        continue

        except Exception:
            raise UserError(_("Invalid xlsx file. Please check the file that you are trying to import!"))
        return vals

    def _read_csv_file(self, file, cell_data):
        """
        Read .csv type files
        """
        vals = []
        counter = 1
        skipped_line_no = {}
        try:
            file = str(base64.decodebytes(file).decode('utf-8'))
            csvreader = csv.reader(file.splitlines())

            i = 0
            for row in csvreader:
                if i > 1:  # skip header lines
                    try:
                        data = {}
                        for rec in cell_data:
                            if row[rec] != '':
                                data.update({cell_data[rec]: row[rec]})
                        vals.append(data)
                    # TODO: Add a popup to display invalid lines
                    except Exception as e:
                        skipped_line_no[str(counter)] = " - Value is not valid " + str(e)
                        counter += 1
                        continue
                i += 1
        except Exception:
            raise UserError(_("Invalid csv file. Please check the file that you are trying to import!"))
        return vals

    def action_import(self):
        """
        Import read data to the database
        """
        def _get_data(file_name, file, cell_data):
            """
            Get data for given file
            """
            try:
                file_extension = file_name.split('.')[-1]
                if file_extension == 'xlsx':
                    return self._read_xlsx_file(file, cell_data)
                elif file_extension == 'csv':
                    return self._read_csv_file(file, cell_data)
                else:
                    raise UserError(_('Selected file type is invalid. Only xlsx or csv files can be imported!'))
            except Exception as error:
                raise ValidationError(_("Following error occurred when importing file:\n\n%s" % error))

        # Read and extract file data
        dbo_entity_cell_data = {0: 'entity_id', 12: 'name', 16: 'email', 17: 'vat', 22: 'website'}
        dbo_entity_data = _get_data(self.dbo_entity_file_name, self.dbo_entity_file, dbo_entity_cell_data) if self.dbo_entity_file else {}

        dbo_entity_address_cell_data = {}
        dbo_entity_address_data = _get_data(self.dbo_entity_address_file_name, self.dbo_entity_address_file, dbo_entity_address_cell_data) if self.dbo_entity_address_file else {}

        dbo_entity_contact_cell_data = {}
        dbo_entity_contact_data = _get_data(self.dbo_entity_contact_file_name, self.dbo_entity_contact_file, dbo_entity_contact_cell_data) if self.dbo_entity_contact_file else {}

        # Create or update partner for dbo entity data FIXME to all types
        for rec in [x for x in dbo_entity_data if ('name' in x and 'entity_id' in x)]:
            partner_id = self.env['res.partner'].search([('entity_id', '=', rec['entity_id'])], limit=1)
            if partner_id:
                partner_id.update(rec)
            else:
                partner_id.create(rec)
