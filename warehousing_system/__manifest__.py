
{
    'name': "Warehousing Module",
    'version': '1.0',
    'category': '',
    'sequence': 3,
    'summary': 'Used to manage warehouse',
    'depends': ['base', 'stock', 'purchase', 'web', 'company_memo', 'mail', 'product'],
    'author': '',
    'data': [ 
        # 'security/ir.model.access.csv',
        'data/warehouse_stage_data.xml',
        'data/memo_type_warehouse.xml',
        'views/financial_file_views.xml',
        'views/stock_move_operations_views.xml',
        'views/stock_picking_views.xml',
        'views/inventory_views.xml',
        'views/warehouse_dashboard_menu.xml',
        'report/waybill_item_report.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'warehousing_system/static/src/xml/warehouse_dashboard.xml',
            'warehousing_system/static/src/js/warehouse_dashboard.js',
            'warehousing_system/static/src/css/warehouse_dashboard_style.css',
        ],
    },
    
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
