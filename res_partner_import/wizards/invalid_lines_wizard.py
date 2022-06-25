# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class InvalidLinesWizard(models.TransientModel):
    _name = 'invalid.lines.wizard'
    _description = 'Invalid Lines Wizard'

    successful = fields.Boolean('Successful')
    line_ids = fields.One2many('invalid.lines', 'wizard_id', string='Invalid Lines')


class InvalidLines(models.TransientModel):
    _name = 'invalid.lines'
    _description = 'Invalid Lines'

    entity_file = fields.Char('File Name')
    line = fields.Char('Line')
    reason = fields.Text('Reason')
    wizard_id = fields.Many2one('invalid.lines.wizard', string='Wizard')
