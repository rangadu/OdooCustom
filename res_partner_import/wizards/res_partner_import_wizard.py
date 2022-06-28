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
            vals = {
                'entity_id': rec['entity_id'],
                'dealer_id': rec.get('dealer_id', False),
                'company': rec.get('company', False),
                'entity_type_id': rec.get('entity_type_id', False),
                'entity_category_id': rec.get('entity_category_id', False),
                'entity_creator_id': rec.get('entity_creator_id', False),
                'entity_updater_id': rec.get('entity_updater_id', False),
                'abc_cat_id': rec.get('abc_cat_id', False),
                'bus_cat_id': rec.get('bus_cat_id', False),
                'notes': rec.get('notes', False),
                'date_added': rec.get('date_added', False),
                'date_modified': rec.get('date_modified', False),
                'name': rec['name'],
                'switchboard': rec.get('switchboard', False),
                'fax': rec.get('fax', False),
                'url': rec.get('url', False),
                'email': rec.get('email', False),
                'vat': rec.get('vat', False),
                'vat_except_num': rec.get('vat_except_num', False),
                'accept_back_orders': rec.get('accept_back_orders', False),
                'menthod_of_contact': rec.get('menthod_of_contact', False),
                'catdesc': rec.get('catdesc', False),
                'website': rec.get('website', False),
                'comptel': rec.get('comptel', False),
                'next_call_date': rec.get('next_call_date', False),
                'account_type_id': rec.get('account_type_id', False),
                'date_updated': rec.get('date_updated', False),
                'temp_id': rec.get('temp_id', False),
                'compregnum': rec.get('compregnum', False),
                'account_num': rec.get('account_num', False),
                'modified_by': rec.get('modified_by', False),
                'account_supplier_id': rec.get('account_supplier_id', False),
                'account_customer_id': rec.get('account_customer_id', False),
                'is_birthday_supplier': rec.get('is_birthday_supplier', False),
                'is_birthday_courier': rec.get('is_birthday_courier', False),
                'is_anniversary_courier': rec.get('is_anniversary_courier', False),
                'is_anniversary_supplier': rec.get('is_anniversary_supplier', False),
                'is_account_supplier': rec.get('is_account_supplier', False),
                'is_supplier': rec.get('is_supplier', False),
                'invoice_to': rec.get('invoice_to', False),
                'currency': rec.get('currency', False),
                'credit_limit': rec.get('credit_limit', False),
                'payment_terms': rec.get('payment_terms', False),
                'sdl_no': rec.get('sdl_no', False),
                'sic_code': rec.get('sic_code', False),
                'ofo_no': rec.get('ofo_no', False),
                'markup': rec.get('markup', False),
                'client_rating': rec.get('client_rating', False),
                'manual_rating': rec.get('manual_rating', False),
                'sales_cons_id': rec.get('sales_cons_id', False),
                'alternate_company_id': rec.get('comments', False),
                'comments': rec.get('comments', False),
                'card_type_id': rec.get('card_type_id', False),
                'credit_card_name': rec.get('credit_card_name', False),
                'credit_card_number': rec.get('credit_card_number', False),
                'exp_month': rec.get('exp_month', False),
                'exp_year': rec.get('exp_year', False),
                'bank_recon_notes': rec.get('bank_recon_notes', False),
                'acc_stat_id': rec.get('acc_stat_id', False),
                'avg_payment_time': rec.get('avg_payment_time', False),
                'vendor_number': rec.get('vendor_number', False),
                'source_id': rec.get('source_id', False),
                'pricelistID': rec.get('pricelistID', False),
                'bank_branch_name': rec.get('bank_branch_name', False),
                'bank_branch_code': rec.get('bank_branch_code', False),
                'debit_order': rec.get('debit_order', False),
                'ref_no': rec.get('ref_no', False),
                'tax_type_id': rec.get('tax_type_id', False),
                'industry_id': rec.get('industry_id', False),
                'entity_subtype_id': rec.get('entity_subtype_id', False),
                'temp_id_varchar': rec.get('temp_id_varchar', False),
                'is_vat_exempt': rec.get('is_vat_exempt', False),
                'in_active': rec.get('in_active', False),
                'cnt_order_number': rec.get('cnt_order_number', False),
                'cnt_id_number': rec.get('cnt_id_number', False),
                'cnt_damage_waiver': rec.get('cnt_damage_waiver', False),
                'cnt_sites': rec.get('cnt_sites', False),
            }
            # update partner if exist
            if partner_id:
                partner_id.update(vals)
            else:  # create partner if not exist
                partner_id.create(vals)

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
                # prepare country
                country_id = False
                if 'country' in rec:
                    country_id = self.env['res.country'].search([('name', '=', rec['country'])], limit=1).id
                # prepare state
                state_id = False
                if 'state' in rec:
                    state_id = self.env['res.country.state'].search([('name', '=', rec['state'])], limit=1).id

                # prepare values
                vals = {
                    'entity_id': int(rec['entity_address_id']),
                    'type': 'other',
                    'entity_address_type': address_type,
                    'street': rec['address_1'],
                    'address_2': rec.get('address_2', False),
                    'address_3': rec.get('address_3', False),
                    'city': rec.get('city', False),
                    'region': rec.get('region', False),
                    'code': rec.get('code', False),
                    'country_id': country_id,
                    'state_id': state_id,
                    'temp_id': rec.get('temp_id', False),
                    'is_default': True if rec.get('is_default', False) == 1 else False,
                    'address_4': rec.get('address_4', False),
                }
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
                # prepare country
                country_id = False
                if 'country' in rec:
                    country_id = self.env['res.country'].search([('name', '=', rec['country'])], limit=1).id
                # prepare state
                state_id = False
                if 'state' in rec:
                    state_id = self.env['res.country.state'].search([('name', '=', rec['state'])], limit=1).id
                # prepare values for update or create record
                vals = {
                    'type': 'contact',
                    'entity_id': rec['entity_address_id'],
                    'name': ' '.join([rec.get('initials', ''), rec.get('first_name', ''), rec.get('surname', '')]),
                    'title': title.id if title else False,
                    'entity_type_id': rec.get('entity_type_id', False),
                    'entity_category_id': rec.get('entity_category_id', False),
                    'alternate_contact_id': rec.get('alternate_contact_id', False),
                    'entity_contact_updater_id': rec.get('entity_contact_updater_id', False),
                    'entity_contact_creator_id': rec.get('entity_contact_creator_id', False),
                    'physical_addr_id': rec.get('physical_addr_id', False),
                    'postal_addr_id': rec.get('postal_addr_id', False),
                    'cont_type_id': rec.get('cont_type_id', False),
                    'position_id': rec.get('position_id', False),
                    'sales_cons_id': rec.get('sales_cons_id', False),
                    'bus_cat_id': rec.get('buscatid', False),
                    'abc_cat_id': rec.get('abc_catid', False),
                    'is_default': rec.get('is_default', False),
                    'company': rec.get('company', False),
                    'phone': rec.get('phone', False),
                    'phone2': rec.get('phone2', False),
                    'phone3': rec.get('phone3', False),
                    'home_phone': rec.get('home_phone', False),
                    'mobile': rec.get('mobile', False),
                    'fax': rec.get('fax', False),
                    'email': rec.get('email', False),
                    'ext': rec.get('ext', False),
                    'department': rec.get('department', False),
                    'spouse': rec.get('spouse', False),
                    'asst_title': rec.get('asst_title', False),
                    'asst_name': rec.get('asst_name', False),
                    'asst_phone': rec.get('asst_phone', False),
                    'asst_ext': rec.get('asst_ext', False),
                    'hobbies': rec.get('hobbies', False),
                    'notes': rec.get('notes', False),
                    'street': rec.get('address1', False),
                    'address_2': rec.get('address2', False),
                    'address_3': rec.get('address3', False),
                    'city': rec.get('city', False),
                    'state_id': state_id,
                    'code': rec.get('code', False),
                    'region': rec.get('region', False),
                    'country_id': country_id,
                    'poaddress1': rec.get('poaddress1', False),
                    'poaddress2': rec.get('poaddress2', False),
                    'poaddress3': rec.get('poaddress3', False),
                    'pocity': rec.get('pocity', False),
                    'postate': rec.get('postate', False),
                    'pocode': rec.get('pocode', False),
                    'poregion': rec.get('poregion', False),
                    'pocountry': rec.get('pocountry', False),
                    'birth_date': rec.get('birth_date', False),
                    'path': rec.get('path', False),
                    'province': rec.get('province', False),
                    'is_supplier': rec.get('is_supplier', False),
                    'send_email': rec.get('send_email', False),
                    'send_sms': rec.get('send_sms', False),
                    'date_updated': rec.get('date_updated', False),
                    'account_num': rec.get('account_num', False),
                    'entity_htype': rec.get('entity_htype', False),
                    'date_added': rec.get('date_added', False),
                    'date_modified': rec.get('date_modified', False),
                    'outlook_id': rec.get('outlook_id', False),
                    'owning_user_id': rec.get('owning_user_id', False),
                    'temp_id': rec.get('temp_id', False),
                    'position': rec.get('position', False),
                    'asstemail': rec.get('asstemail', False),
                    'sendpost': rec.get('sendpost', False),
                    'dissacosiate': rec.get('dissacosiate', False),
                    'modified_by': rec.get('modifiedby', False),
                    'birthday_supplier_id': rec.get('birthday_supplier_id', False),
                    'birthday_courier_id': rec.get('birthday_courier_id', False),
                    'function': rec.get('job_title', False),
                    'anniversary_supplier_id': rec.get('anniversary_supplier_id', False),
                    'anniversary_courier_id': rec.get('anniversary_courier_id', False),
                    'anniversary_date': rec.get('anniversary_date', False),
                    'account_type_id': rec.get('account_type_id', False),
                    'account_ref': rec.get('account_ref', False),
                    'id_number': rec.get('id_number', False),
                    'bank_name': rec.get('bank_name', False),
                    'account_no': rec.get('account_no', False),
                    'account_name': rec.get('account_name', False),
                    'bank_account_name': rec.get('bank_account_name', False),
                    'branch_code': rec.get('branch_code', False),
                    'acc_type_id': rec.get('acc_type_id', False),
                    'emailref': rec.get('emailref', False),
                    'credit_card_name': rec.get('credit_card_name', False),
                    'credit_card_number': rec.get('credit_card_number', False),
                    'expiry_date': rec.get('expiry_date', False),
                    'card_type_id': rec.get('card_type_id', False),
                    'is_credit_card': rec.get('is_credit_card', False),
                    'in_use': rec.get('in_use', False),
                    'exp_month': rec.get('exp_month', False),
                    'exp_year': rec.get('exp_year', False),
                    'agent_ref': rec.get('agent_ref', False),
                    'agent_id': rec.get('agnet_id', False),
                    'press': rec.get('press', False),
                    'proj_cust': rec.get('proj_cust', False),
                    'completed': rec.get('completed', False),
                    'department_id': rec.get('department_id', False),
                    'industry_id': rec.get('industry_id', False),
                    'entity_subtype_id': rec.get('entity_sub_type_id', False),
                    'use_comp_addr': rec.get('use_comp_addr', False),
                    'additional1': rec.get('additional1', False),
                    'additional2': rec.get('additional2', False),
                    'additional3': rec.get('additional3', False),
                    'additional4': rec.get('additional4', False),
                    'additional_id5': rec.get('additional_id5', False),
                    'additional_id6': rec.get('additional_id6', False),
                    'additional_id7': rec.get('additional_id7', False),
                    'additional_id8': rec.get('additional_id8', False),
                    'in_active': rec.get('in_active', False),
                    'screenshot_path': rec.get('screenshot_path', False),
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
                1: 'dealer_id',
                2: 'company',
                3: 'entity_type_id',
                4: 'entity_category_id',
                5: 'entity_creator_id',
                6: 'entity_updater_id',
                7: 'abc_cat_id',
                8: 'bus_cat_id',
                9: 'notes',
                10: 'date_added',
                11: 'date_modified',
                12: 'name',
                13: 'switchboard',
                14: 'fax',
                15: 'url',
                16: 'email',
                17: 'vat',
                18: 'vat_except_num',
                19: 'accept_back_orders',
                20: 'menthod_of_contact',
                21: 'catdesc',
                22: 'website',
                23: 'comptel',
                24: 'next_call_date',
                25: 'account_type_id',
                26: 'date_updated',
                27: 'temp_id',
                28: 'compregnum',
                29: 'account_num',
                30: 'modified_by',
                31: 'account_supplier_id',
                32: 'account_customer_id',
                33: 'is_birthday_supplier',
                34: 'is_birthday_courier',
                35: 'is_anniversary_courier',
                36: 'is_anniversary_supplier',
                37: 'is_account_supplier',
                38: 'is_supplier',
                39: 'invoice_to',
                40: 'currency',
                41: 'credit_limit',
                42: 'payment_terms',
                43: 'sdl_no',
                44: 'sic_code',
                45: 'ofo_no',
                46: 'markup',
                47: 'client_rating',
                48: 'manual_rating',
                49: 'sales_cons_id',
                50: 'alternate_company_id',
                51: 'comments',
                52: 'card_type_id',
                53: 'credit_card_name',
                54: 'credit_card_number',
                55: 'exp_month',
                56: 'exp_year',
                57: 'bank_recon_notes',
                58: 'acc_stat_id',
                59: 'avg_payment_time',
                60: 'vendor_number',
                61: 'source_id',
                62: 'pricelistID',
                63: 'bank_branch_name',
                64: 'bank_branch_code',
                65: 'debit_order',
                66: 'ref_no',
                67: 'tax_type_id',
                68: 'industry_id',
                69: 'entity_subtype_id',
                70: 'temp_id_varchar',
                71: 'is_vat_exempt',
                72: 'in_active',
                73: 'cnt_order_number',
                74: 'cnt_id_number',
                75: 'cnt_damage_waiver',
                76: 'cnt_sites'
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
                3: 'address_1',
                4: 'address_2',
                5: 'address_3',
                6: 'city',
                7: 'region',
                8: 'code',
                9: 'country',
                10: 'state',
                11: 'temp_id',
                12: 'is_default',
                13: 'address_4',
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
                2: 'entity_type_id',
                3: 'entity_category_id',
                4: 'alternate_contact_id',
                5: 'entity_contact_updater_id',
                6: 'entity_contact_creator_id',
                7: 'physical_addr_id',
                8: 'postal_addr_id',
                9: 'cont_type_id',
                10: 'position_id',
                11: 'interest_id',
                12: 'sales_cons_id',
                13: 'buscatid',
                14: 'abc_catid',
                15: 'is_default',
                16: 'company',
                17: 'first_name',
                18: 'surname',
                19: 'title',
                20: 'initials',
                21: 'phone',
                22: 'phone2',
                23: 'phone3',
                24: 'home_phone',
                25: 'mobile',
                26: 'fax',
                27: 'email',
                28: 'ext',
                29: 'department',
                30: 'spouse',
                31: 'asst_title',
                32: 'asst_name',
                33: 'asst_phone',
                34: 'asst_ext',
                35: 'hobbies',
                36: 'notes',
                37: 'address1',
                38: 'address2',
                39: 'address3',
                40: 'city',
                41: 'state',
                42: 'code',
                43: 'region',
                44: 'country',
                45: 'poaddress1',
                46: 'poaddress2',
                47: 'poaddress3',
                48: 'pocity',
                49: 'postate',
                50: 'pocode',
                51: 'poregion',
                52: 'pocountry',
                53: 'birth_date',
                54: 'path',
                55: 'province',
                56: 'is_supplier',
                57: 'send_email',
                58: 'send_sms',
                59: 'date_updated',
                60: 'account_num',
                61: 'entity_htype',
                62: 'date_added',
                63: 'date_modified',
                64: 'outlook_id',
                65: 'owning_user_id',
                66: 'temp_id',
                67: 'position',
                68: 'asstemail',
                69: 'sendpost',
                70: 'dissacosiate',
                71: 'modifiedby',
                72: 'birthday_supplier_id',
                73: 'birthday_courier_id',
                74: 'job_title',
                75: 'anniversary_supplier_id',
                76: 'anniversary_courier_id',
                77: 'anniversary_date',
                78: 'account_type_id',
                79: 'account_ref',
                80: 'id_number',
                81: 'bank_name',
                82: 'account_no',
                83: 'account_name',
                84: 'bank_account_name',
                85: 'branch_code',
                86: 'acc_type_id',
                87: 'emailref',
                88: 'credit_card_name',
                89: 'credit_card_number',
                90: 'expiry_date',
                91: 'card_type_id',
                92: 'is_credit_card',
                93: 'in_use',
                94: 'exp_month',
                95: 'exp_year',
                96: 'agent_ref',
                97: 'agnet_id',
                98: 'press',
                99: 'proj_cust',
                100: 'completed',
                101: 'department_id',
                102: 'industry_id',
                103: 'entity_sub_type_id',
                104: 'use_comp_addr',
                105: 'additional1',
                106: 'additional2',
                107: 'additional3',
                108: 'additional4',
                109: 'additional_id5',
                110: 'additional_id6',
                111: 'additional_id7',
                112: 'additional_id8',
                113: 'in_active',
                114: 'screenshot_path'
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
