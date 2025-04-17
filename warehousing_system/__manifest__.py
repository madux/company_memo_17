# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': "Warehous Module",
    'version': '1.0',
    'category': '',
    'sequence': 3,
    'summary': 'Used to manage warehouse',
    'depends': ['base', 'stock', 'mail', 'product'],
    'author': '',
    'data': [ 
        # 'security/ir.model.access.csv',
        'views/inventory_views.xml'
    ],
    
    'installable': True,
    'auto_install': True,
    'license': 'LGPL-3',
}
