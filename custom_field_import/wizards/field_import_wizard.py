# -*- coding: utf-8 -*-

import xlrd
import csv
import base64

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class FieldImportWizard(models.Model):
    _name = 'field.import.wizard'
    _description = 'Field Import Wizard'

    file = fields.Binary('File To Import', required=False)
    file_name = fields.Char("File Name")

    def _read_xlsx_file(self, file, cell_data, file_name, required_columns):
        """
        Read .xlsx type files
        """
        vals = []
        counter = 1
        skipped_line_no = []
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
                            # check the cell is required otherwise skip line
                            elif cell_data[rec] in required_columns:
                                skipped_line_no.append({
                                    'line': counter,
                                    'file': file_name,
                                    'reason': '%s column not found' % cell_data[rec]
                                })
                        vals.append(data)
                    except Exception as e:
                        # skip line if an error occurred
                        skipped_line_no.append({
                            'line': counter,
                            'file': file_name,
                            'reason': 'Value is not valid - %s' % str(e)
                        })
                counter += 1

        except Exception:
            raise UserError(_("Invalid xlsx file. Please check the file that you are trying to import!"))

        return vals, skipped_line_no

    def _read_csv_file(self, file, cell_data, file_name, required_columns):
        """
        Read .csv type files
        """
        vals = []
        counter = 1
        skipped_line_no = []
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
                            # check the cell is required otherwise skip line
                            elif cell_data[rec] in required_columns:
                                skipped_line_no.append({
                                    'line': counter,
                                    'file': file_name,
                                    'reason': '%s column not found' % cell_data[rec]
                                })
                        vals.append(data)
                    except Exception as e:
                        # skip line if an error occurred
                        skipped_line_no.append({
                            'line': counter,
                            'file': file_name,
                            'reason': 'Value is not valid - %s' % str(e)
                        })
                counter += 1
                i += 1
        except Exception:
            raise UserError(_("Invalid csv file. Please check the file that you are trying to import!"))

        return vals, skipped_line_no

    def _process_data(self, data):
        """
        Processing imported data
        """
        pass

    def action_import(self):
        """
        Import read data to the database
        """
        def _get_data(file, cell_data, file_name, required_columns):
            """
            Get data for the given file
            """
            try:
                file_extension = file_name.split('.')[-1]
                if file_extension == 'xlsx':
                    return self._read_xlsx_file(file, cell_data, file_name, required_columns)
                elif file_extension == 'csv':
                    return self._read_csv_file(file, cell_data, file_name, required_columns)
                else:
                    raise UserError(_('Selected file type is invalid. Only xlsx or csv files can be imported!'))
            except Exception as error:
                raise ValidationError(_("Following error occurred when importing file:\n\n%s" % error))

        invalid_lines = []
        if self.file:
            # Read, extract and process field data
            cell_data = {
                0: 'name',
                1: 'field_description',
                2: 'field_type',
                3: 'tab_list',
                4: 'sh_position_field',
                5: 'sh_position',
                6: 'field_help',
                7: 'required',
                8: 'copied',
            }
            required_columns = ['name', 'field_description', 'field_type', 'tab_list', 'sh_position_field', 'sh_position']
            data, invalid_lines = _get_data(self.file, cell_data, self.file_name, required_columns)
        else:
            raise UserError(_('Please add a file to import!'))

        # Prepare invalid lines
        invalid_lines = [(0, 0, x) for x in invalid_lines]

        # return status popup
        return {
            'name': 'Import Status',
            'view_mode': 'form',
            'res_model': 'invalid.import.lines.wizard',
            'domain': [],
            'context': {
                'default_line_ids': invalid_lines,
                'default_successful': True if not bool(invalid_lines) else False
            },
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    # Download template files
    def download_templates(self):
        """
        Download the sample templates
        """
        file_name = 'Field Import Sample.csv' if 'csv' in self._context else 'Field Import Sample.xlsx'
        return {
            'type': 'ir.actions.act_url',
            'name': 'Sample Import Template',
            'url': '/custom_field_import/static/src/samples/' + file_name + '?download=true',
        }
