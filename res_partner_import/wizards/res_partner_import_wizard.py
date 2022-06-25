# -*- coding: utf-8 -*-

import xlrd
import csv
import base64

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ResPartnerImportWizard(models.TransientModel):
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

    def _read_xlsx_file(self, file, cell_data, required_columns, file_name, partner_check):
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
                                # check the partner exist otherwise skip line
                                if cell_data[rec] == 'entity_id' and not self.env['res.partner'].search([('entity_id', '=', sheet.cell(row, rec).value)]) and partner_check:
                                    skipped_line_no.append({
                                        'line': counter,
                                        'entity_file': file_name,
                                        'reason': 'Partner not found for the entity id - %s' % str(sheet.cell(row, rec).value)
                                    })
                            # check the cell is required otherwise skip line
                            elif cell_data[rec] in required_columns:
                                skipped_line_no.append({
                                    'line': counter,
                                    'entity_file': file_name,
                                    'reason': '%s column not found' % cell_data[rec]
                                })
                        vals.append(data)
                    except Exception as e:
                        # skip line if an error occurred
                        skipped_line_no.append({
                            'line': counter,
                            'entity_file': file_name,
                            'reason': 'Value is not valid - %s' % str(e)
                        })
                counter += 1

        except Exception:
            raise UserError(_("Invalid xlsx file. Please check the file that you are trying to import!"))

        return vals, skipped_line_no

    def _read_csv_file(self, file, cell_data, required_columns, file_name, partner_check):
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
                                # check the partner exist otherwise skip line
                                if cell_data[rec] == 'entity_id' and not self.env['res.partner'].search([('entity_id', '=', row[rec])]) and partner_check:
                                    skipped_line_no.append({
                                        'line': counter,
                                        'entity_file': file_name,
                                        'reason': 'Partner not found for the entity id - %s' % str(row[rec])
                                    })
                            # check the cell is required otherwise skip line
                            elif cell_data[rec] in required_columns:
                                skipped_line_no.append({
                                    'line': counter,
                                    'entity_file': file_name,
                                    'reason': '%s column not found' % cell_data[rec]
                                })
                        vals.append(data)
                    except Exception as e:
                        # skip line if an error occurred
                        skipped_line_no.append({
                            'line': counter,
                            'entity_file': file_name,
                            'reason': 'Value is not valid - %s' % str(e)
                        })
                counter += 1
                i += 1
        except Exception:
            raise UserError(_("Invalid csv file. Please check the file that you are trying to import!"))

        return vals, skipped_line_no

    def _process_entity_data(self, data):
        """
        Create or update partner for dbo entity data
        """
        for rec in [x for x in data if ('name' in x and 'entity_id' in x)]:
            # check already assigned partner
            partner_id = self.env['res.partner'].search([('entity_id', '=', int(rec['entity_id']))], limit=1)
            # update partner if exist
            if partner_id:
                partner_id.update(rec)
            else:  # create partner if not exist
                partner_id.create(rec)

    def _process_entity_address_data(self, data):
        """
        Create or update partner for dbo entity address data
        """
        for rec in [x for x in data if ('entity_address_id' in x and 'entity_id' in x and 'address_type' in x)]:
            res_partner_obj = self.env['res.partner']
            # check already assigned partner_id
            partner_id = res_partner_obj.search([('entity_id', '=', int(rec['entity_id']))], limit=1)
            if bool(partner_id):
                # update address_type
                address_type = 'postal' if (rec['address_type'] == 'Postal Address') else 'physical'
                # check address partner already exist
                entity_address_id = res_partner_obj.search([('entity_id', '=', int(rec['entity_address_id'])), ('type', '=', 'other')])
                vals = {'entity_id': int(rec['entity_address_id']), 'type': 'other', 'entity_address_type': address_type, 'street': rec['address_1']}
                # update address partner if exist
                if entity_address_id:
                    entity_address_id.update(vals)
                else:  # create address partner if not exist
                    partner_id.update({'child_ids': [(0, 0, vals)]})

    def _process_entity_contact_data(self, data):
        """
        Create or update partner for dbo entity contact data
        """
        for rec in [x for x in data if ('entity_address_id' in x and 'entity_id' in x)]:
            res_partner_obj = self.env['res.partner']
            # check already assigned partner
            partner_id = res_partner_obj.search([('entity_id', '=', int(rec['entity_id']))], limit=1)
            if bool(partner_id):
                # check entity contact
                entity_contact_id = res_partner_obj.search([('entity_id', '=', int(rec['entity_address_id'])), ('type', '=', 'contact')])
                # prepare title
                title = False
                if 'title' in rec:
                    title = self.env['res.partner.title'].search([('name', '=', rec['title'])], limit=1)
                    if not title:
                        title = self.env['res.partner.title'].create({'name': rec['title']})
                # prepare values for update or create record
                vals = {
                    'type': 'contact',
                    'entity_id': rec['entity_address_id'],
                    'name': ' '.join([rec.get('initials', ''), rec.get('first_name', ''), rec.get('surname', '')]),
                    'title': title.id,
                    'phone': rec.get('phone', False),
                    'home_phone': rec.get('home_phone', False),
                    'mobile': rec.get('mobile', False),
                    'email': rec.get('email', False),
                    'outlook_id': rec.get('outlook_id', False),
                    'function': rec.get('job_title', False)
                }
                # update entity contact if contact exist
                if entity_contact_id:
                    entity_contact_id.update(vals)
                else:  # create entity contact if not exist
                    partner_id.update({'child_ids': [(0, 0, vals)]})

    def action_import(self):
        """
        Import read data to the database
        """
        def _get_data(file_name, file, cell_data, req_cols, partner_check=True):
            """
            Get data for given file
            """
            try:
                file_extension = file_name.split('.')[-1]
                if file_extension == 'xlsx':
                    return self._read_xlsx_file(file, cell_data, req_cols, file_name, partner_check)
                elif file_extension == 'csv':
                    return self._read_csv_file(file, cell_data, req_cols, file_name, partner_check)
                else:
                    raise UserError(_('Selected file type is invalid. Only xlsx or csv files can be imported!'))
            except Exception as error:
                raise ValidationError(_("Following error occurred when importing file:\n\n%s" % error))

        all_invalid_lines = []
        # Read, extract and process dbo entity data
        if self.dbo_entity_file:
            dbo_entity_cell_data = {
                0: 'entity_id',
                12: 'name',
                16: 'email',
                17: 'vat',
                22: 'website'
            }
            required_columns = ['entity_id', 'name']
            dbo_entity_data, invalid_lines = _get_data(self.dbo_entity_file_name, self.dbo_entity_file, dbo_entity_cell_data, required_columns, partner_check=False)
            self._process_entity_data(dbo_entity_data)
            all_invalid_lines += invalid_lines

        # Read, extract and process dbo entity address data
        if self.dbo_entity_address_file:
            dbo_entity_address_cell_data = {
                0: 'entity_address_id',
                1: 'entity_id',
                2: 'address_type',
                3: 'address_1'
            }
            required_columns = ['entity_address_id', 'entity_id', 'address_type']
            dbo_entity_address_data, invalid_lines = _get_data(self.dbo_entity_address_file_name, self.dbo_entity_address_file, dbo_entity_address_cell_data, required_columns)
            self._process_entity_address_data(dbo_entity_address_data)
            all_invalid_lines += invalid_lines

        # Read, extract and process dbo entity contact data
        if self.dbo_entity_contact_file:
            dbo_entity_contact_cell_data = {
                0: 'entity_address_id',
                1: 'entity_id',
                17: 'first_name',
                18: 'surname',
                19: 'title',
                20: 'initials',
                21: 'phone',
                24: 'home_phone',
                25: 'mobile',
                27: 'email',
                64: 'outlook_id',
                74: 'job_title'
            }
            required_columns = ['entity_address_id', 'entity_id']
            dbo_entity_contact_data, invalid_lines = _get_data(self.dbo_entity_contact_file_name, self.dbo_entity_contact_file, dbo_entity_contact_cell_data, required_columns)
            self._process_entity_contact_data(dbo_entity_contact_data)
            all_invalid_lines += invalid_lines

        # Prepare invalid lines
        invalid_lines = [(0, 0, x) for x in all_invalid_lines]

        # return status popup
        return {
            'name': 'Import Status',
            'view_mode': 'form',
            'res_model': 'invalid.lines.wizard',
            'domain': [],
            'context': {
                'default_line_ids': invalid_lines,
                'default_successful': True if not bool(invalid_lines) else False
            },
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
