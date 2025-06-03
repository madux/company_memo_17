from odoo import http
from odoo.http import request, Response
import json

class CustomerWarehouseDashboardController(http.Controller):
    
    @http.route([
        '/warehouse', 
        '/warehouse/', 
        '/warehouse/dashboard',
        '/warehouse/customer/dashboard'
    ], type='http', auth='public', website=True)
    def render_customer_dashboard(self, **kw):
        """Renders the customer warehouse dashboard template"""
        return request.render('warehousing_system.customer_warehouse_dashboard_template', {
            'current_page': 'dashboard'
        })
    
    @http.route(
        '/warehouse/customer/dashboard/data',
        type='json',
        auth='public',
        csrf=False,
        methods=['POST', 'GET'],
    )
    def dashboard_data(self, client=None, **kw):
        """
        JSON endpoint returning warehouse dashboard summary counts.
        Delegates filtering & counting to model method.
        """
        filters = {
            'client': client or '',
        }
        data = request.env['stock.picking'].sudo().get_customer_warehouse_dashboard_data(filters)
        return data
    
    @http.route(
        '/warehouse/customer/dashboard/action',
        type='json',
        auth='public',
        csrf=False,
        methods=['POST', 'GET'],
    )
    def dashboard_action(self, cardSelected=None, title=None, client=None, **kw):
        """
        JSON endpoint returning detailed records for a clicked dashboard card.
        Delegates domain logic to model method.
        """
        action_data = {
            'cardSelected': cardSelected or '',
            'title': title or '',
            'filterData': {
                'client': client or '',
            }
        }
        records = request.env['stock.picking'].sudo().get_customer_dashboard_detail(action_data)
        return records
    
    @http.route(
        '/warehouse/customer/dashboard/list',
        type='http',
        methods=['POST', 'GET'],
        auth='public',
        website=True,
    )
    def customer_inventory_list(self, cardSelected=None, title=None, vehicle=None, **kw):
        """
        Renders a list view of the records behind the clicked card.
        """
        # build filter/action payload
        action_data = {
            'cardSelected': cardSelected or '',
            'title': title or '',
            'filterData': {
                'vehicle': vehicle or '',
            }
        }
        records = request.env['stock.picking'].sudo().get_customer_dashboard_detail(action_data)
        return request.render(
            'warehousing_system.customer_warehouse_detail_template',
            {
                'records': records,
                'title': title,
                'filters': action_data['filterData'],
                'current_page': 'dashboard'
            }
        )

    @http.route(
        '/warehouse/inventory',
        type='http',
        auth='public',
        website=True,
    )
    def warehouse_inventory(self, vehicle=None, **kw):
        """
        Display all inventory items (stock.picking records)
        """
        filters = {
            'client': vehicle or '',
        }
        
        domain = request.env['stock.picking'].sudo().get_base_domain(filters) or []
        records = request.env['stock.picking'].sudo().search(domain)
        
        formatted_records = []
        for record in records:
            formatted_records.append({
                'id': record.id,
                'name': record.name,
                'client': record.customer_id.name if record.customer_id else '',
                'status': record.inventory_status,
                'scheduled_date': record.scheduled_date.strftime('%Y-%m-%d') if record.scheduled_date else '',
            })
        
        return request.render(
            'warehousing_system.customer_warehouse_detail_template',
            {
                'records': formatted_records,
                'title': 'All Inventory Items',
                'filters': filters,
                'current_page': 'inventory'
            }
        )

    @http.route(
        '/warehouse/outbound',
        type='http',
        auth='public',
        website=True,
    )
    def outbound_dispatch_orders(self, vehicle=None, **kw):
        """
        Display outbound dispatch orders using the same API as card clicks
        """
        action_data = {
            'cardSelected': 'dispatchedItems',
            'title': 'Outbound Dispatch Orders',
            'filterData': {
                'client': vehicle or '',
            }
        }
        
        records = request.env['stock.picking'].sudo().get_customer_dashboard_detail(action_data)
        
        return request.render(
            'warehousing_system.customer_warehouse_detail_template',
            {
                'records': records,
                'title': 'Outbound Dispatch Orders',
                'filters': action_data['filterData'],
                'current_page': 'outbound'
            }
        )

    @http.route(
        '/warehouse/inventory/create',
        type='http',
        auth='public',
        website=True,
    )
    def inventory_create_form(self, **kw):
        """
        Placeholder for inventory creation form
        """
        return request.render(
            'warehousing_system.customer_warehouse_detail_template',
            {
                'records': [],
                'title': 'Inventory Creation Form',
                'filters': {},
                'current_page': 'create',
                'is_form': True
            }
        )

    @http.route(
        '/warehouse/put-away',
        type='http',
        auth='public',
        website=True,
    )
    def put_away_section(self, **kw):
        """
        Placeholder for put away to section
        """
        return request.render(
            'warehousing_system.customer_warehouse_detail_template',
            {
                'records': [],
                'title': 'Put Away to Section',
                'filters': {},
                'current_page': 'put-away'
            }
        )

    @http.route(
        '/warehouse/inventory/lists',
        type='http',
        auth='public',
        website=True,
    )
    def inventory_lists(self, **kw):
        """
        Placeholder for inventory lists
        """
        return request.render(
            'warehousing_system.customer_warehouse_detail_template',
            {
                'records': [],
                'title': 'Inventory Lists',
                'filters': {},
                'current_page': 'lists'
            }
        )

    @http.route(
        '/warehouse/inbound',
        type='http',
        auth='public',
        website=True,
    )
    def inbound_shipments(self, **kw):
        """
        Placeholder for inbound shipments
        """
        return request.render(
            'warehousing_system.customer_warehouse_detail_template',
            {
                'records': [],
                'title': 'Inbound Shipments',
                'filters': {},
                'current_page': 'inbound'
            }
        )