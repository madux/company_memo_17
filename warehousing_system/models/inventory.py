from odoo import api, fields, models
from datetime import date, timedelta
import logging
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class WarehouseInventory(models.Model):
    _inherit = 'stock.picking'
    _order = "id desc"
    
    
    @api.onchange('warehouse_id')
    def onchange_warehouse(self):
        picking_code = self.env.context.get('default_picking_type_code') or self.picking_type_code
        if self.warehouse_id:
            warehouse_picking_types = self.env['stock.picking.type'].search([
                ('warehouse_id', '=', self.warehouse_id.id),
                ('code', '=', picking_code),
                ])
            self.update({
                'dummy_picking_type_ids': [(6, 0, warehouse_picking_types.ids)]
                })
        else:
            self.update({
                'dummy_picking_type_ids': False
                })
                
    dummy_picking_type_ids = fields.Many2many(
        'stock.picking.type',
        string="Dummy Stock Picking type",
    )
     
    financial_id = fields.Many2one(
        'memo.model',
        string="Financial File",
        copy=True,
        help="Refers to the Purchase Order associated with this inventory receipt.",
        domain=[('memo_type.memo_key','in', ['transport', 'warehouse'])]
    )
    related_inbound_shipment = fields.Many2one(
        'stock.picking',
        string="Related Inbound Shipment",
    )
    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string="Warehouse",
        copy=True,
        help="Select the warehouse where the goods arrived or are expected."
    )
    inventory_status = fields.Selection(selection=[
        ('draft', "Draft"),
        ('arrived', "Allocated"),
        ('allocated', "Put Away"),
        ('done', 'Stored'),
        ('awaiting_dispatch', 'Awaiting Dispatch'),
        ('dispatch', 'Dispatched'),
        ('cancelled', 'Cancelled')
    ], string="Inventory Status",copy=True, default='draft', index=True, tracking=True)
    actual_date_of_arrival = fields.Date(
        string="Actual Arrival Date",
        tracking=True,
        copy=False,
    )
    days_in_warehouse = fields.Integer(
        copy=False,
        string="Days in Storage (days)",
        compute="compute_days_in_storage"
    )

    @api.depends('actual_date_of_arrival')
    def compute_days_in_storage(self):
        for rec in self:
            if rec.actual_date_of_arrival:
                today = fields.Date.today()
                date_of_arrival = rec.actual_date_of_arrival
                diff = today - date_of_arrival
                rec.days_in_warehouse= diff.days
            else:
                rec.days_in_warehouse= 0

    receiving_supplier_id = fields.Many2one(
        'res.partner',
        string="Delivering Supplier/Vendor",
        # domain=[('supplier_rank', '>', 0)],
        help="The supplier who delivered the goods."
    )
    supplier_po_number = fields.Char(
        string="PO No.",
        copy=True,
        help="PO number from the supplier's system, if different from Odoo's PO."
    )
    dispatch_company = fields.Char(
        string="Dispatch company",
        copy=True,
    )
    transport_details = fields.Char(
        string="Transport Detail",
    )
    receiving_waybill_number = fields.Char(
        string="Waybill No. (RL/AWB)",
        copy=True,
        help="Receiving Log / Air Waybill number associated with the delivery."
    )
    bl_awb_number = fields.Char(string="BL/AWB No.", copy=True)
    expected_arrival_date = fields.Date(
        string="Expected Arrival Date",
        tracking=True
    )
    expected_dispatch_arrival_date = fields.Date(
        string="Expected Dispatch Arrival Date",
        tracking=True
    )
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
    customer_address = fields.Text(
        string="Customer Address",
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
        string="Total items", 
        help="Total items for each line",
        compute="compute_total_items"
    )
    
    # TRANSPORT
    truck_company_name = fields.Many2one('res.partner', string='Truck company Name')
    truck_reg = fields.Char(string='Truck registration No.')
    truck_type = fields.Char(string='Truck Type')
    truck_driver = fields.Many2one('res.partner', string='Driver details')
    truck_driver_phone = fields.Char(string='Driver Phone')
     
    waybill_from = fields.Char(string='Pickup Location?')
    waybill_to = fields.Char(string='Drop Off Location')
    waybill_date = fields.Datetime(string='Date of Transportation')
    waybill_expected_arrival_date = fields.Datetime(string='Expected Arrival')
    waybill_note = fields.Char(string='Waybill Note')
    

    # dispatch_move_ids_packages = fields.One2many(
    #     'stock.move',
    #     'dispatch_picking_id',
    #     string="Dispatch Moves"
    # )
    dispatch_picking_ids_packages = fields.Many2many(
        'stock.picking',
        'stock_picking_dispatch_rel',
        'stock_picking_id',
        'stock_dispatch_picking_id',
        string="Dispatch Picking"
    )
    dispatch_dest_location_id = fields.Many2one(
        'stock.location', 
        string="Dispatch location"
    )
    
    def confirm_dispatch(self):
        '''Checks if item exist in inventory and
        set status to dispatched
        '''
        # tt = self.env['stock.quant'].sudo()._get_available_quantity(self.env['product.product'].browse([10]), self.env['stock.location'].browse([18]), allow_negative=False) # or 0.0
        # raise ValidationError(f"{tt},{self.env['product.product'].browse([10])}, {self.env['stock.location'].browse([18])} ")
        for pck in self.dispatch_picking_ids_packages:
            for count, pml in enumerate(pck.move_ids_without_package, 1):
                tt_availability = self.env['stock.quant'].sudo()._get_available_quantity(pml.product_id, pml.location_id, allow_negative=False) # or 0.0
                if pml.quantity > tt_availability:
                    raise ValidationError(f"""
                                          At line {count}: The quantity to dispatch is lesser than the amount \n remaining in the inventory location {(pml.location_id.name)}. The product {(pml.product_id.name)} available quantity is {tt_availability}"""
                                          )
                # else:
                #     raise ValidationError("This dispatch does not have any product / items allocation during receipts")
                
            # pck.button_validate()
            if pck.state not in ['done']:
                raise ValidationError("please validate the dispatch operation before confirming")
        self.inventory_status = 'dispatch'
        
    is_dispatch = fields.Boolean()
    
    # def action_validate_owner_stock(self, picking):
    #     '''check the lines to ensure owner still have products in stock'''
    #     for rec in picking.move_ids_without_package:
    #         if rec.product_id.id:
    #             owner_stock_quants = self.env['stock.quant'].sudo().search([
    #             ('owner_id', '=', self.customer_id.id),
    #             ('product_id', '=', self.product_id.id),
    #             '|',('warehouse_id', '=', self.warehouse_id.id),
    #             ('location_id', '=', self.location_id.id)
    #             ])
    #             total_quantity = sum([qt.quantity for qt in owner_stock_quants])
    #             if total_quantity < 1:
    #                 items_to_remove
            
    def action_dispatch_moves(self):
        '''set is dispatch to true and enable dispatch functionality'''
        self.action_validate_owner_stock(self.customer_id)
        if self.move_ids_without_package:
            if not self.dispatch_picking_ids_packages:
                picking_id = self.copy()
                warehouse_picking_types = self.env['stock.picking.type'].search([
                    ('warehouse_id', '=', self.warehouse_id.id),
                    ('code', '=', 'outgoing'),
                    ], limit=1)
                picking_id.update({
                    "name": f"DISP/{picking_id.name}",
                    'location_id': self.location_dest_id.id,
                    'location_dest_id': self.dispatch_dest_location_id.id,
                    'related_inbound_shipment': self.id,
                    'inbound_picking_id': self.id,
                    'is_dispatch': True,
                    'picking_type_code': 'outgoing',
                    'picking_type_id': warehouse_picking_types and warehouse_picking_types.id,
                    'inventory_status': 'awaiting_dispatch',
                })
                 
                self.dispatch_picking_ids_packages = [(6, 0, [picking_id.id])]
                
                # '''check the lines to ensure owner still have products in stock'''
                for pi in self.dispatch_picking_ids_packages:
                    for ml in pi.move_ids_without_package:
                        if ml.product_id.id:
                            owner_stock_quants = self.env['stock.quant'].sudo().search([
                            ('owner_id', '=', self.customer_id.id),
                            ('product_id', '=', ml.product_id.id),
                            '|',('warehouse_id', '=', self.warehouse_id.id),
                            ('location_id', '=', self.location_id.id)
                            ])
                            total_quantity = sum([qt.quantity for qt in owner_stock_quants])
                            if total_quantity < 1:
                                pi.move_ids_without_package = [(3, ml.id)]
            else:
                picking_id = self.dispatch_picking_ids_packages[0]
            picking_id.action_confirm()
            self.inventory_status = "awaiting_dispatch"
            return self.button_view_picking(picking_id.id)
        else:
            raise ValidationError("No stock move lines to Dispatch!!!")
    
    def print_way_bill(self):
        return self.env.ref('warehousing_system.print_dispatch_waybill_report').report_action(self)
    
    def button_view_picking(self, pickingId):
        view_id = self.env.ref('warehousing_system.view_warehouse_inventory_form').id
        ret = {
            'name': "Dispatching",
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'stock.picking',
            'res_id': pickingId,
            'type': 'ir.actions.act_window',
            'domain': [],
            'target': 'current'
            }
        return ret     
                
    @api.depends('move_ids_without_package.no_of_items')
    def compute_total_items(self):
        for rec in self:
            if rec.move_ids_without_package:
                sum_items = sum([re.no_of_items for re in rec.mapped('move_ids_without_package')])
                rec.amount = sum_items if sum_items > 1 else len( rec.move_ids_without_package.ids)
            else:
                rec.amount = 0 
    
    @api.onchange('customer_id')
    def _onchange_customer_id(self):
        if self.customer_id:
            self.owner_id = self.customer_id.id
            if self.picking_type_code == "outgoing":
                quant = self.env['stock.quant'].sudo()
                move = self.env['stock.move'].sudo()
                '''Get the owner stocks greater than 0 in given warehouse'''
                owner_stock_quants = quant.search([
                    ('owner_id', '=', self.customer_id.id),
                    # ('quantity', '>', 0),
                    '|',('warehouse_id', '=', self.warehouse_id.id),
                    ('location_id', '=', self.location_id.id)
                    ])
                list_items = {}
                # raise ValidationError(f"{owner_stock_quants}, {self.customer_id.id} {self.location_id.id}")
                for sq in owner_stock_quants:
                    '''Build stock moves dynamically'''
                    # product_items = {'id': False, 'name': "", 'qty': 0}
                    productId = sq.product_id.id
                    if str(productId) in list_items:
                        list_items[str(productId)]['qty'] += sq.available_quantity
                    else:
                        list_items[str(productId)] = {
                            'id': productId, 
                            'qty': sq.available_quantity, 
                            'name': sq.product_id.name
                            }
                for k, v in list_items.items():   
                    sq_vals = {
                        "name": f"{v.get('name')}-{v.get('id')}",
                        "product_id": v.get('id'),
                        "product_uom_qty": v.get('qty'),
                        "remaining_qty": v.get('qty'),
                        "product_uom": self.env['product.product'].sudo().browse([v.get('id')]).uom_id.id,
                        "picking_id": self.id,
                        "state": "draft",
                        "location_id": self.location_id.id,
                        "location_dest_id": self.location_dest_id.id,
                    }
                    self.move_ids_without_package = [(0, 0, sq_vals)]
        
    @api.onchange('financial_id')
    def _onchange_financial_id_for_items(self):
        for pick in self:
            if pick.financial_id:
                # self.supplier_po_number = self.financial_id.name or ''
                self.origin = self.financial_id.code
                self.partner_id = self.financial_id.client_id.id
                self.customer_id = self.financial_id.client_id.id
                self.owner_id = self.financial_id.client_id.id
                if not self.receiving_supplier_id and self.financial_id.client_id:
                    self.receiving_supplier_id = self.financial_id.client_id
                pick.move_ids_without_package = [(5, 0, 0)]
                src_loc = pick.location_id.id \
                        or pick.picking_type_id.default_location_src_id.id
                dst_loc = pick.location_dest_id.id \
                        or pick.picking_type_id.default_location_dest_id.id
                new_moves = []
                if pick.financial_id.waybill_ids:
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
        view_id = self.env.ref('company_memo.tree_memo_model_view2').id
        ret = {
            'name': "Financial File",
            'view_mode': 'tree',
            'view_id': view_id,
            'view_type': 'tree',
            'res_model': 'memo.model',
            # 'res_id': self.financial_id.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain' :[('id', 'in', [self.financial_id.id])]
            }
        return ret
    
    def action_confirm(self):
        res = super(WarehouseInventory, self).action_confirm()
        self.inventory_status = 'allocated' if not self.dispatch_dest_location_id else 'awaiting_dispatch'
        return res
    
    def button_validate(self):
        'validate transport details'
        if self.is_dispatch:
            if not self.truck_company_name or not self.truck_reg or not self.truck_type \
                or not self.truck_driver or not self.waybill_from or not self.waybill_to or not self.waybill_date:
                raise ValidationError('Please ensure all transportation details are filled')
        for rec in self.move_ids_without_package:
            if rec.product_uom_qty <= 0:
                raise ValidationError(f'{rec.product_id.name} move lines quantity contains negative stock. It must be above 0')
            rec.update({
                'quantity': rec.product_uom_qty,
                # 'product_qty': rec.product_uom_qty,
            })
        
        res = super(WarehouseInventory, self).button_validate()
        self.inventory_status = 'done' if not self.dispatch_dest_location_id and self.inventory_status not in 'awaiting_dispatch' else 'dispatch'
        return res
    
    def action_cancel(self):
        res = super(WarehouseInventory, self).action_cancel()
        self.inventory_status = 'cancelled'
        return res
    
    
    def get_base_domain(self, filters):
        base_domain = []
         
        if filters.get('client') and filters['client'].strip():
            base_domain.append(('customer_id.name', 'ilike', filters['client'].strip()))
            _logger.info(f'Customer: {base_domain}')
            
        if filters.get('vehicle') and filters['vehicle'].strip():
            base_domain.append(('truck_company_name.name', 'ilike', filters['vehicle'].strip()))
            _logger.info(f'Vehicle: {base_domain}')
        
        # if filters.get('fileType'):
        #     # base_domain.append(('inventory_status', '=', filters['fileType']))
        #     _logger.info('Not implemented...continuing with warehouse')
        
        # if filters.get('projectNo') and filters['projectNo'].strip():
        #     base_domain.append(('origin', 'ilike', filters['projectNo'].strip()))
        
        # if (filters.get('month') and filters['month'] != 'All') or (filters.get('year') and filters['year'] != 'All'):
        #     month_mapping = {
        #         'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
        #         'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
        #     }
            
        #     year = fields.Date.today().year
        #     if filters.get('year') and filters['year'] != 'All':
        #         try:
        #             year = int(filters['year'])
        #         except (ValueError, TypeError):
        #             pass
            
        #     if filters.get('month') and filters['month'] != 'All' and filters['month'] in month_mapping:
        #         month_num = month_mapping[filters['month']]
        #         start_date = fields.Date.to_string(date(year, month_num, 1))
                
        #         if month_num == 12:
        #             end_date = fields.Date.to_string(date(year + 1, 1, 1))
        #         else:
        #             end_date = fields.Date.to_string(date(year, month_num + 1, 1))
                    
        #         base_domain.append(('create_date', '>=', start_date))
        #         base_domain.append(('create_date', '<', end_date))
        #     elif filters.get('year') and filters['year'] != 'All':
        #         start_date = fields.Date.to_string(date(year, 1, 1))
        #         end_date = fields.Date.to_string(date(year + 1, 1, 1))
        #         base_domain.append(('create_date', '>=', start_date))
        #         base_domain.append(('create_date', '<', end_date))
            
        return base_domain
    
    def waiting_for_info_domain(self):
        return [('inventory_status', '=', 'draft'), ('financial_id', '!=', False)]
    
    def expected_date_domain(self, days):
        the_date = fields.Date.today(self) + timedelta(days=days)
        return [('scheduled_date', '=', the_date), 
                ('financial_id', '!=', False), 
                ('inventory_status', 'not in', ['done', 'cancelled']),]
    
    def to_be_put_in_stock_domain(self):
        return [('inventory_status', '=', 'arrived'),('financial_id', '!=', False)]
    
    
    def without_allocated_storage_domain(self):
        return [
            ('warehouse_id', '=', False),
            ('financial_id', '!=', False),
            ('inventory_status', 'in', ['draft', 'cancelled']),
            ('move_ids_without_package.is_label_printed', '=', False)
        ]
    
    def labels_to_be_printed_domain(self):
        return [
            ('inventory_status', 'not in', ['draft', 'cancelled']),
            ('financial_id', '!=', False),
            ('move_ids_without_package', '!=', False),
            ('move_ids_without_package.is_label_printed', '=', False)
        ]
        
    def open_osd_inventory_domain(self):
        return [
            ('inventory_status', '=', 'arrived'),
            ('financial_id', '!=', False),
        ]
        
    def displaced_items_domain(self):
        return [
            ('warehouse_id', '!=', False),
            ('inventory_status', '=', 'allocated'),
            ('financial_id', '!=', False)
        ]
        
    def dispatched_items_domain(self):
        return [
            ('inventory_status', '=', 'done'),
            ('financial_id', '!=', False)
        ]
        
    def critical_stock_items_domain(self):
        return [
            ('critical_equipment', '!=', 'none'),
            ('financial_id', '!=', False)
        ]
        
    def temperature_sensitive_domain(self):
        return [
            ('critical_equipment', '!=', 'none'),
            ('financial_id', '!=', False)
        ]
        
    def dangerous_goods_domain(self):
        return [
            ('critical_equipment', '=', 'hazard'),
            ('financial_id', '!=', False)
        ]
    
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
            
        base_domain = self.get_base_domain(filters) or []
        _logger.info(f'Base: Domain: {base_domain}')
        
        waiting_for_info = self.search_count(base_domain + self.waiting_for_info_domain())
        expected_tomorrow = self.search_count(base_domain + self.expected_date_domain(1))
        expected_today = self.search_count(base_domain + self.expected_date_domain(0))
        to_be_put_in_stock = self.search_count(base_domain + self.to_be_put_in_stock_domain())
        without_allocated_storage = self.search_count(base_domain + self.without_allocated_storage_domain())
        
        # labels_to_be_printed_ids = self.search(base_domain + self.labels_to_be_printed_domain())
        # not_printed_labels = []
        # pickings_not_printed = []
        # for lb in labels_to_be_printed_ids:
        #     moves = lb.mapped('move_ids_without_package').filtered(lambda prn: not prn.is_label_printed)
        #     not_printed_labels += moves.ids
        #     pickings_not_printed += [m.picking_id.id for m in moves] # 54
            
        # _logger.info(f"INVENTORY ITEMS ==> {not_printed_labels}")
        
        not_printed_labels = self.search(base_domain + self.labels_to_be_printed_domain())
        labels_to_be_printed = len(not_printed_labels)
        
        longer_than_90_days = self.search_count(base_domain + self.expected_date_domain(90))
        
        open_osd_inventory = self.search_count(base_domain + self.open_osd_inventory_domain())
        
        displaced_items = self.search_count(base_domain + self.displaced_items_domain())
        
        dispatched_items = self.search_count(base_domain + self.dispatched_items_domain())
        
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

        action_ref = 'warehousing_system.action_warehouse_inventory_receipts'
        action = self.env["ir.actions.actions"]._for_xml_id(action_ref)
        
        _logger.info("get_action python method..........")

        if action_data.get('title'):
            action['display_name'] = action_data['title']
            _logger.info("Title added")
            
        domain_map = {
            'waitingForInfo':        self.waiting_for_info_domain,
            'expectedTomorrow':      lambda: self.expected_date_domain(1),
            'expectedToday':         lambda: self.expected_date_domain(0),
            'toBePutInStock':        self.to_be_put_in_stock_domain,
            'withoutAllocatedStorage': self.without_allocated_storage_domain,
            'labelsToBePrinted':     self.labels_to_be_printed_domain,
            'longerThan90Days':      lambda: self.expected_date_domain(90),
            'openOSDInventory':      self.open_osd_inventory_domain,
            'displacedItems':        self.displaced_items_domain,
            'dispatchedItems':       self.dispatched_items_domain,
        }
        card = action_data.get('cardSelected')
        if card in domain_map:
            action['domain'] = domain_map[card]()
            
        if action_data.get('filterData'):
            base_domain = self.get_base_domain(action_data['filterData']) or []
            if base_domain:
                action['domain'] += base_domain
                
        _logger.info(f'Whole Domain = {action['domain']}')

        return {'action': action}
    
    
    
    # Public mehods
    @api.model
    def get_customer_warehouse_dashboard_data(self, filters=None):
        """
        Public version of get_warehouse_dashboard_data with additional security measures
        
        This method exposes only the necessary data for public dashboard viewing,
        ensuring sensitive information is not leaked.
        
        Args:
            filters: A dictionary with filter values
                - client: Text to search in customer_id.name
                - month: Month for create_date
                - year: Year for create_date
        """
        if not filters:
            filters = {}
            
        base_domain = self.get_base_domain(filters) or []
        _logger.info(f'Base: Domain: {base_domain}')
        
        waiting_for_info = self.search_count(base_domain + self.waiting_for_info_domain())
        expected_tomorrow = self.search_count(base_domain + self.expected_date_domain(1))
        expected_today = self.search_count(base_domain + self.expected_date_domain(0))
        to_be_put_in_stock = self.search_count(base_domain + self.to_be_put_in_stock_domain())
        without_allocated_storage = self.search_count(base_domain + self.without_allocated_storage_domain())
        
        # labels_to_be_printed_ids = self.search(base_domain + self.labels_to_be_printed_domain())
        # not_printed_labels = []
        # pickings_not_printed = []
        # for lb in labels_to_be_printed_ids:
        #     moves = lb.mapped('move_ids_without_package').filtered(lambda prn: not prn.is_label_printed)
        #     not_printed_labels += moves.ids
        #     pickings_not_printed += [m.picking_id.id for m in moves] # 54
            
        # _logger.info(f"INVENTORY ITEMS ==> {not_printed_labels}")
        
        not_printed_labels = self.search(base_domain + self.labels_to_be_printed_domain())
        labels_to_be_printed = len(not_printed_labels)
        
        longer_than_90_days = self.search_count(base_domain + self.expected_date_domain(90))
        
        open_osd_inventory = self.search_count(base_domain + self.open_osd_inventory_domain())
        
        displaced_items = self.search_count(base_domain + self.displaced_items_domain())
        
        dispatched_items = self.search_count(base_domain + self.dispatched_items_domain())
        
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
    def get_customer_dashboard_detail(self, action_data=None):
        """
        Public version of get_action that returns data instead of an action
        
        Since public users don't have access to Odoo actions, this method
        returns the filtered data directly.
        
        Args:
            action_data: A dictionary with filtering information
                - cardSelected: Which dashboard card was clicked
                - filterData: Additional filters to apply
        """
        action_data = action_data or {}

        action_ref = 'warehousing_system.action_warehouse_inventory_receipts'
        action = self.env["ir.actions.actions"]._for_xml_id(action_ref)
        
        _logger.info("get_action python method..........")

        if action_data.get('title'):
            action['display_name'] = action_data['title']
            _logger.info("Title added")
            
        domain_map = {
            'waitingForInfo':        self.waiting_for_info_domain,
            'expectedTomorrow':      lambda: self.expected_date_domain(1),
            'expectedToday':         lambda: self.expected_date_domain(0),
            'toBePutInStock':        self.to_be_put_in_stock_domain,
            'withoutAllocatedStorage': self.without_allocated_storage_domain,
            'labelsToBePrinted':     self.labels_to_be_printed_domain,
            'longerThan90Days':      lambda: self.expected_date_domain(90),
            'openOSDInventory':      self.open_osd_inventory_domain,
            'displacedItems':        self.displaced_items_domain,
            'dispatchedItems':       self.dispatched_items_domain,
        }
        card = action_data.get('cardSelected')
        if card in domain_map:
            action['domain'] = domain_map[card]()
            
        if action_data.get('filterData'):
            base_domain = self.get_base_domain(action_data['filterData']) or []
            if base_domain:
                action['domain'] += base_domain
                
        _logger.info(f'Whole Domain = {action['domain']}')

        return {'action': action}
    
    
    
    # Public mehods
    @api.model
    def get_customer_warehouse_dashboard_data(self, filters=None):
        """
        Public version of get_warehouse_dashboard_data with additional security measures
        
        This method exposes only the necessary data for public dashboard viewing,
        ensuring sensitive information is not leaked.
        
        Args:
            filters: A dictionary with filter values
                - client: Text to search in customer_id.name
                - month: Month for create_date
                - year: Year for create_date
        """
        if not filters:
            filters = {}
        
        base_domain = self.get_base_domain(filters) or []
        waiting_for_info = self.search_count(base_domain + self.waiting_for_info_domain())
        expected_tomorrow = self.search_count(base_domain + self.expected_date_domain(1))
        expected_today = self.search_count(base_domain + self.expected_date_domain(0))
        to_be_put_in_stock = self.search_count(base_domain + self.to_be_put_in_stock_domain())
        without_allocated_storage = self.search_count(base_domain + self.without_allocated_storage_domain())
        
        not_printed_labels = self.search(base_domain + self.labels_to_be_printed_domain())
        labels_to_be_printed = len(not_printed_labels)
        
        longer_than_90_days = self.search_count(base_domain + self.expected_date_domain(90))
        open_osd_inventory = self.search_count(base_domain + self.open_osd_inventory_domain())
        displaced_items = self.search_count(base_domain + self.displaced_items_domain())
        dispatched_items = self.search_count(base_domain + self.dispatched_items_domain())
        
        critical_stock_items = self.search_count(base_domain + self.critical_stock_items_domain())
        temperature_sensitive = self.search_count(base_domain + self.temperature_sensitive_domain())
        dangerous_goods = self.search_count(base_domain + self.dangerous_goods_domain())
        
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
            'dispatchedItems': dispatched_items,
            'criticalStockItems': critical_stock_items,
            'temperatureSensitive': temperature_sensitive,
            'dangerousGoods': dangerous_goods
        }
        
        _logger.info(f"Public dashboard data: {result}")
        
        return result
    
    @api.model
    def get_customer_dashboard_detail(self, action_data=None):
        """
        Public version of get_action that returns data instead of an action
        
        Since public users don't have access to Odoo actions, this method
        returns the filtered data directly.
        
        Args:
            action_data: A dictionary with filtering information
                - cardSelected: Which dashboard card was clicked
                - filterData: Additional filters to apply
        """
        action_data = action_data or {}
        
        domain_map = {
            'waitingForInfo':        self.waiting_for_info_domain,
            'expectedTomorrow':      lambda: self.expected_date_domain(1),
            'expectedToday':         lambda: self.expected_date_domain(0),
            'toBePutInStock':        self.to_be_put_in_stock_domain,
            'withoutAllocatedStorage': self.without_allocated_storage_domain,
            'labelsToBePrinted':     self.labels_to_be_printed_domain,
            'longerThan90Days':      lambda: self.expected_date_domain(90),
            'openOSDInventory':      self.open_osd_inventory_domain,
            'displacedItems':        self.displaced_items_domain,
            'dispatchedItems':       self.dispatched_items_domain,
            'criticalStockItems':    self.critical_stock_items_domain,
            'temperatureSensitive':  self.temperature_sensitive_domain,
            'dangerousGoods':        self.dangerous_goods_domain,
        }
        
        domain = []
        card = action_data.get('cardSelected')
        if card in domain_map:
            domain = domain_map[card]()
            
        if action_data.get('filterData'):
            base_domain = self.get_base_domain(action_data['filterData']) or []
            if base_domain:
                domain += base_domain
                
        
        records = self.search(domain)
    
        result = []
        for record in records:
            result.append({
                'id': record.id,
                'name': record.name,
                'vehicle': record.truck_company_name.name if record.customer_id else '',
                'status': record.inventory_status,
                'scheduled_date': record.scheduled_date.strftime('%Y-%m-%d') if record.scheduled_date else '',
            })
        
        return result