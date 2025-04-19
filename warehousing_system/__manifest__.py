# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': "Warehousing Module",
    'version': '1.0',
    'category': '',
    'sequence': 3,
    'summary': 'Used to manage warehouse',
    'depends': ['base', 'stock', 'purchase', 'company_memo', 'mail', 'product'],
    'author': '',
    'data': [ 
        # 'security/ir.model.access.csv',
         'data/warehouse_stage_data.xml',
        'data/memo_type_warehouse.xml',
        'views/inventory_views.xml',
    ],
    
    'installable': True,
    'auto_install': True,
    'license': 'LGPL-3',
}
