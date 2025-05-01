from odoo import api, fields, models
from datetime import date, timedelta
import logging

_logger = logging.getLogger(__name__)
    
class WarehouseInventory(models.Model):
    _inherit = 'stock.picking'

    financial_id = fields.Many2one(
        'memo.model',
        string="Financial File / PO",
        help="Refers to the Purchase Order associated with this inventory receipt.",
        domain=[('memo_type.memo_key','in', ['transport', 'warehouse'])]
    )
    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string="Warehouse",
        help="Select the warehouse where the goods arrived or are expected."
    )
    inventory_status = fields.Selection(selection=[
        ('draft', "Draft"),
        ('arrived', "Arrived at Warehouse"),
        ('allocated', "Allocated"),
        ('done', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string="Inventory Status", default='draft', index=True, tracking=True)
    actual_date_of_arrival = fields.Date(
        string="Actual Arrival Date",
        tracking=True
    )
    receiving_supplier_id = fields.Many2one(
        'res.partner',
        string="Delivering Supplier/Vendor",
        domain=[('supplier_rank', '>', 0)],
        help="The supplier who delivered the goods."
    )
    supplier_po_number = fields.Char(
        string="Supplier PO Number",
        help="PO number from the supplier's system, if different from Odoo's PO."
    )
    receiving_waybill_number = fields.Char(
        string="Waybill Number (RL/AWB)",
        help="Receiving Log / Air Waybill number associated with the delivery."
    )
    bl_awb_number     = fields.Char(string="BL / AWB Number")
    
    # expected_arrival_date = fields.Selection([
    #     ('today', 'Today'),
    #     ('tomorrow', 'Tomorrow'),
    #     ('other', 'Other')
    # ], string='Expected Arrival Date (str)', compute='_compute_expected_arrival_date', store=True, default='other')
    
    critical_equipment = fields.Selection([
        ('none', "None Critical"),
        ('safety', "Safety Critical"),
        ('operations', "Operations Critical"),
        ('date_sensitive', "Date Sensitive"),
        ('hazard', "Hazard Material"),
    ], string="Criticality", help="Classification of the received items.")
    intended_vessel = fields.Char(
        string="Intended Vessel / Project",
        help="The vessel, project, or destination these goods are intended for."
    )
    customer_id = fields.Many2one(
        'res.partner',
        string="Customer",
        help="The ultimate customer."
    )
    po_line_ids = fields.One2many(
        'purchase.order.line',
        'order_id',
        string='Item Details (per item)',
        readonly=True,
        copy=False,
    )
    unit_of_measure_id = fields.Many2one(
        'uom.uom',
        string="Unit of Measure",
        help="Select the default unit of measure for this receipt."
    )
    amount = fields.Float(
        string="Amount",
        digits='Product Price',
        help="Total amount for these goods"
    )
    
    def _compute_expected_arrival_date(self):
        today = fields.Date.today()
        for rec in self:
            scheduled_date = rec.scheduled_date.date() if rec.scheduled_date else None
            if scheduled_date == today:
                rec.expected_arrival_date = 'today'
            elif scheduled_date == today + timedelta(days=1):
                rec.expected_arrival_date = 'tomorrow'
            else:
                rec.expected_arrival_date = 'other'

    
    @api.onchange('financial_id')
    def _onchange_financial_id_for_items(self):
        for pick in self:
            if pick.financial_id:
                self.supplier_po_number = self.financial_id.name or ''
                self.origin = self.financial_id.code
                if not self.receiving_supplier_id and self.financial_id.client_id:
                    self.receiving_supplier_id = self.financial_id.client_id
                pick.move_ids_without_package = [(5, 0, 0)]
                src_loc = pick.location_id.id \
                        or pick.picking_type_id.default_location_src_id.id
                dst_loc = pick.location_dest_id.id \
                        or pick.picking_type_id.default_location_dest_id.id
                new_moves = []
                for wb in pick.financial_id.waybill_ids:
                    uom = self.env['uom.uom'].search(
                        [('name', '=', wb.uom)], limit=1
                    )
                    new_moves.append((0, 0, {
                        'name': wb.product_id.display_name,
                        'product_id': wb.product_id.id,
                        'product_uom_qty': wb.quantity or 0.0,
                        'product_uom': uom.id or wb.product_id.uom_id.id or False,
                        'location_id': src_loc,
                        'location_dest_id': dst_loc,
                        'description_picking': wb.waybill_desc or '',
                    }))
                pick.move_ids_without_package = new_moves
                self.inventory_status = "arrived"
            # else:
            #     self.inventory_status = "arrived"
            #     self.state = "draft"
                
    inbound_picking_id = fields.Many2one(
        'stock.picking',
        string="Related Inbound Shipment",
        domain=[('picking_type_id.code', '=', 'incoming')],
        help="Select the receipt operation that brought these goods into stock."
    )

    def button_financial_file(self):
        view_id = self.env.ref('company_memo.memo_model_form_view_3').id
        ret = {
            'name': "Financial File",
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'memo.model',
            'res_id': self.financial_id.id,
            'type': 'ir.actions.act_window',
            'target': 'new'
            }
        return ret
    
    def action_confirm(self):
        res = super(WarehouseInventory, self).action_confirm()
        self.inventory_status = 'allocated'
        return res
    
    def button_validate(self):
        res = super(WarehouseInventory, self).button_validate()
        self.inventory_status = 'done'
        return res
    
    def action_cancel(self):
        res = super(WarehouseInventory, self).action_cancel()
        self.inventory_status = 'cancelled'
        return res
                 
    @api.model
    def get_warehouse_dashboard_data(self, filters=None):
        """
        This method fetches all the necessary data for the warehouse dashboard
        Returns a dictionary with counts for different inventory statuses
        
        Args:
            filters: A dictionary with filter values
                - client: Text to search in customer_id.name
                - fileType: Inventory status
                - projectNo: Supplier PO number
                - month: Month for create_date
                - year: Year for create_date
        """
        if not filters:
            filters = {}
            
        base_domain = []
        
        if filters.get('client') and filters['client'].strip():
            base_domain.append(('customer_id.name', 'ilike', filters['client'].strip()))
            _logger.info(f'Customer: {base_domain}')
        
        if filters.get('fileType') and filters['fileType'] != 'warehouse':
            # base_domain.append(('inventory_status', '=', filters['fileType']))
            _logger.info('Not implemented...continuing with warehouse')
        
        if filters.get('projectNo') and filters['projectNo'].strip():
            base_domain.append(('origin', 'ilike', filters['projectNo'].strip()))
        
        if (filters.get('month') and filters['month'] != 'All') or (filters.get('year') and filters['year'] != 'All'):
            month_mapping = {
                'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
            }
            
            year = fields.Date.today().year
            if filters.get('year') and filters['year'] != 'All':
                try:
                    year = int(filters['year'])
                except (ValueError, TypeError):
                    pass
            
            if filters.get('month') and filters['month'] != 'All' and filters['month'] in month_mapping:
                month_num = month_mapping[filters['month']]
                start_date = fields.Date.to_string(date(year, month_num, 1))
                
                if month_num == 12:
                    end_date = fields.Date.to_string(date(year + 1, 1, 1))
                else:
                    end_date = fields.Date.to_string(date(year, month_num + 1, 1))
                    
                base_domain.append(('create_date', '>=', start_date))
                base_domain.append(('create_date', '<', end_date))
            elif filters.get('year') and filters['year'] != 'All':
                start_date = fields.Date.to_string(date(year, 1, 1))
                end_date = fields.Date.to_string(date(year + 1, 1, 1))
                base_domain.append(('create_date', '>=', start_date))
                base_domain.append(('create_date', '<', end_date))
        
        today = fields.Date.today()
        tomorrow = today + timedelta(days=1)
        ninety_days_ago = today - timedelta(days=90)
        
        waiting_for_info = self.search_count(base_domain + [('inventory_status', '=', 'draft')])
        expected_tomorrow = self.search_count(base_domain + [('scheduled_date', '=', tomorrow)])
        expected_today = self.search_count(base_domain + [('scheduled_date', '=', today)])
        to_be_put_in_stock = self.search_count(base_domain + [('inventory_status', '=', 'arrived')])
        without_allocated_storage = self.search_count(base_domain + [
            ('warehouse_id', '=', False), 
            ('inventory_status', 'not in', ['draft', 'cancelled'])
        ])
        
        labels_to_be_printed = self.search_count(base_domain + [
            ('inventory_status', 'in', ['arrived', 'allocated']),
        ])
        
        longer_than_90_days = self.search_count(base_domain + [
            ('actual_date_of_arrival', '!=', False),
            ('actual_date_of_arrival', '<', ninety_days_ago),
            ('inventory_status', 'not in', ['done', 'cancelled'])
        ])
        
        open_osd_inventory = self.search_count(base_domain + [
            ('inventory_status', '=', 'arrived')
        ])
        
        displaced_items = self.search_count(base_domain + [
            ('warehouse_id', '!=', False),
            ('inventory_status', '=', 'allocated')
        ])
        
        dispatched_items = self.search_count(base_domain + [
            ('inventory_status', '=', 'done')
        ])
        
        result = {
            'waitingForInfo': waiting_for_info,
            'expectedTomorrow': expected_tomorrow,
            'expectedToday': expected_today,
            'toBePutInStock': to_be_put_in_stock,
            'withoutAllocatedStorage': without_allocated_storage,
            'labelsToBePrinted': labels_to_be_printed,
            'longerThan90Days': longer_than_90_days,
            'openOSDInventory': open_osd_inventory,
            'displacedItems': displaced_items,
            'dispatchedItems': dispatched_items
        }
        
        _logger.info(f"Dashboard data: {result}")
        
        return result

    @api.model
    def get_action(self, action_data=None):
        action_data = action_data or {}

        action_ref = 'warehousing_system.action_warehouse_inventory'
        action = self.env["ir.actions.actions"]._for_xml_id(action_ref)

        if action_data.get('title'):
            action['display_name'] = action_data['title']

        if 'domain' in action_data and action_data['domain'] is not None:
            action['domain'] = action_data['domain']

        ctx_flags = action_data.get('context') or {}
        if ctx_flags:
            today = fields.Date.today()
            tomorrow = today + timedelta(days=1)
            ninety_days_ago = today - timedelta(days=90)
            
            if ctx_flags.pop('expectedToday', False):
                action['domain'].append([('scheduled_date', '=', today)])
                _logger.info('Today\'s Context')
            elif ctx_flags.pop('expectedTomorrow', False):
                action['domain'].append([('scheduled_date', '=', tomorrow)])
                _logger.info('Tomorrow\'s Context')
            elif ctx_flags.pop('longerThan90Days', False):
                action['domain'].append([
                    ('actual_date_of_arrival', '!=', False),
                    ('actual_date_of_arrival', '<', ninety_days_ago),
                    ('inventory_status', 'not in', ['done', 'cancelled'])
                ])
                _logger.info('longerThan90Days\'s Context')
                
            ctx = dict(action.get('context') or {})
            ctx.update(ctx_flags)
            action['context'] = ctx

        return {'action': action}