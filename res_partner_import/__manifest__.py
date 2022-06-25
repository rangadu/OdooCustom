# -*- coding: utf-8 -*-

{
    "name": "Contacts Import",
    "author": "Ranga Dharmapriya",
    "email": "rangadharmapriya@gmail.com",
    "support": "",
    "category": "Contacts",
    "summary": "Import contacts with Excel/ CSV file",
    "description": """
Import contacts with Excel/ CSV file
""",
    "version": "15.0.1.0.0",
    "depends": [
        "base",
        "contacts",
    ],
    "data": [
        'security/ir.model.access.csv',
        'views/res_partner_views.xml',
        'wizards/res_partner_import_wizard_views.xml',
        'wizards/invalid_lines_wizard_views.xml',
    ],
    "application": False,
    "auto_install": False,
    "installable": True,
    "license": 'LGPL-3'
}
