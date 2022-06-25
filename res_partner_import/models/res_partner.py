# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    entity_id = fields.Integer(string='Entity ID', readonly=1)
    entity_address_type = fields.Selection([
        ('postal', 'Postal Address'),
        ('physical', 'Physical Address'),
    ], string='Entity Address Type', readonly=1)
    home_phone = fields.Char(string='Home Phone')
    outlook_id = fields.Integer(string='Outlook ID')
    