from odoo import http
from odoo.http import request, Response
import json

class PublicWarehouseDashboardController(http.Controller):
    @http.route(
        '/warehouse/public/dashboard',
        type='http',
        auth='public',
        website=True,
    )
    def render_public_dashboard(self, **kw):
        """Renders the public warehouse dashboard template"""
        return request.render('warehousing_system.public_warehouse_dashboard_template', {})
    
    @http.route(
        '/warehouse/public/dashboard/data',
        type='json',
        auth='public',
        csrf=False,
        methods=['POST', 'GET'],
    )
    def dashboard_data(self, client=None, month='All', year='All', **kw):
        """
        JSON endpoint returning warehouse dashboard summary counts.
        Delegates filtering & counting to model method.
        """
        filters = {
            'client': client or '',
            'month': month or 'All',
            'year': year or 'All',
        }
        data = request.env['stock.picking'].sudo().get_customer_warehouse_dashboard_data(filters)
        return data
    
    @http.route(
        '/warehouse/public/dashboard/action',
        type='json',
        auth='public',
        csrf=False,
        methods=['POST', 'GET'],
    )
    def dashboard_action(self, cardSelected=None, title=None, client=None, month='All', year='All', **kw):
        """
        JSON endpoint returning detailed records for a clicked dashboard card.
        Delegates domain logic to model method.
        """
        action_data = {
            'cardSelected': cardSelected or '',
            'title': title or '',
            'filterData': {
                'client': client or '',
                'month': month or 'All',
                'year': year or 'All',
            }
        }
        records = request.env['stock.picking'].sudo().get_customer_dashboard_detail(action_data)
        return records
    
    @http.route(
        '/warehouse/public/dashboard/list',
        type='http',
        methods=['POST', 'GET'],
        auth='public',
        website=True,
    )
    def customer_inventory_list(self, cardSelected=None, title=None, client=None, month='All', year='All', **kw):
        """
        Renders a list view of the records behind the clicked card.
        """
        # build filter/action payload
        action_data = {
            'cardSelected': cardSelected or '',
            'title': title or '',
            'filterData': {
                'client': client or '',
                'month': month or 'All',
                'year': year or 'All',
            }
        }
        records = request.env['stock.picking'].sudo().get_customer_dashboard_detail(action_data)
        return request.render(
            'warehousing_system.public_warehouse_detail_template',
            {
                'records': records,
                'title': title,
                'filters': action_data['filterData']
            }
        )
