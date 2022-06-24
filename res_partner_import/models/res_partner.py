# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    entity_id = fields.Integer(string='Entity ID', readonly=1)
    