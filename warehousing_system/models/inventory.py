from odoo import api, fields, models
from datetime import timedelta

class StockMove(models.Model):
    _inherit = 'stock.move'

    is_hazard_material = fields.Boolean(string="Hazard Material?")
    intended_vessel = fields.Char(string="Intended Vessel")
    custom_uom = fields.Selection([
        ('4x2_pallet', "4x2 Pallet"),
        ('4x4_pallet', "4x4 Pallet"),
        ('air_conditioner', "Air Conditioner"),
        ('angle_bar', "Angle Bar"),
        ('bag', "Bag"),
        ('container', "Container"),
        ('cable', "Cable"),
        ('bolt', "Bolt"),
        ('boxes', "Boxes"),
    ], string="Custom Unit of Measure")
    
    
    class PickingItem(models.Model):
        _name = 'stock.picking.item'
        _description = "One line of items on our Inventory Creation Form"

        picking_id = fields.Many2one('stock.picking', ondelete='cascade')
        product_id = fields.Many2one('product.product', required=True)
        description = fields.Char(String='Description')
        qty = fields.Integer(String='Quantity',default=0)
        customer_reference = fields.Char(String="Customer Reference")


class WarehouseInventory(models.Model):
    _inherit = 'stock.picking'


    financial_id = fields.Many2one(
        'memo.model',
        string="Financial File / PO",
        help="Refers to the Purchase Order associated with this inventory receipt.",
        domain=[('memo_type.memo_key','=', 'warehouse')]
    )
    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string="Warehouse",
        help="Select the warehouse where the goods arrived or are expected."
    )
    inventory_status = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('arrived', "Arrived at Warehouse"),
        ('allocated', "Allocated"),
        ('waiting', 'Waiting'),
        ('done', 'Processed / Shipped'),
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
    expected_arrival_date = fields.Date(
        string="Expected Arrival Date",
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
        string="End Customer / Requestor",
        domain=[('customer_rank', '>', 0)],
        help="The ultimate customer or internal department requesting the items."
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

    
    item_line_ids = fields.One2many(
        'stock.picking.item', 'picking_id',
        string="Item Details (per item)",
        readonly=False, copy=False,
    )

    @api.onchange('financial_id')
    def _onchange_financial_id_for_items(self):
        for pick in self:
            pick.item_line_ids = [(5,0,0)]
            if pick.financial_id:
                lines = []
                for wb in pick.financial_id.waybill_ids:
                    lines.append((0,0,{
                        'product_id': wb.product_id.id,
                        'description':  wb.waybill_desc or '',
                        'qty': wb.quantity or 0
                    }))
                pick.item_line_ids = lines
    
    inbound_picking_id = fields.Many2one(
        'stock.picking',
        string="Related Inbound Shipment",
        domain=[('picking_type_id.code', '=', 'incoming')],
        help="Select the receipt operation that brought these goods into stock."
    )
    
    ####### Added this fields to allw this module work
    
    # user_owned_cash_advance_ids = fields.Many2many(
    #     'memo.model', 
    #     'user_owned_cash_warehouse_advance_rel',
    #     'user_owned_cash_warehouse_advance_id',
    #     'memo_id', string="User owned cash helpdesk advances", store=False)
    
    # approver_ids = fields.Many2many(
    #     'hr.employee',
    #     'memo_model_warehouse_employee_rel',
    #     'memo_id',
    #     'hr_employee_id',
    #     string='Approvers',
    # )

    # invoice_ids = fields.Many2many(
    #     'account.move',
    #     'memo_invoice_warehouse_rel',
    #     'memo_id',
    #     'invoice_id',
    #     string='Invoices',
    #     store=True,
    #     domain="[('type', 'in', ['in_invoice', 'in_receipt']), ('state', '!=', 'cancel')]",
    # )

    # partner_ids = fields.Many2many(
    #     'res.partner',
    #     'memo_res_warehouse_partner_rel',
    #     'memo_id',
    #     'partner_id',
    #     string='Recipients',
    # )

    # attachment_ids = fields.Many2many(
    #     'ir.attachment',
    #     'memo_ir_attachment_warehouse_rel',
    #     'memo_id',
    #     'attachment_id',
    #     string='Attachments',
    #     store=True,
    #     domain="[('res_model', '=', 'memo.model')]",
    # )

    # memo_sub_stage_ids = fields.Many2many(
    #     'memo.sub.stage',
    #     'memo_sub_stage_warehouse_rel',
    #     'memo_id',
    #     'sub_stage_id',
    #     string='Sub‑Stages',
    #     store=True,
    # )


    def action_pre_allocate(self):
        for record in self:
            #logic here
            record.inventory_status = 'allocated'
        return True


    # Onchange to populate supplier PO from financial_id (Purchase Order)
    @api.onchange('financial_id')
    def _onchange_financial_id(self):
        if self.financial_id:
            self.supplier_po_number = self.financial_id.name or ''
            if not self.receiving_supplier_id and self.financial_id.partner_id:
                 self.receiving_supplier_id = self.financial_id.partner_id
                 
    
    @api.model
    def get_warehouse_dashboard_data(self, filters=None):
        """
        Return a dict of counts for each dashboard tile, applying optional filters.

        filters: {
            client:    str or None,
            fileType:  str or None,    # unused currently
            projectNo: str or None,
            month:     'Jan'..'Dec' or None,
            year:      'YYYY' or None,
        }
        """
        # 1) Normalize filters
        filters = filters or {}
        client     = filters.get('client')
        projectNo  = filters.get('projectNo')
        month      = filters.get('month')
        year       = filters.get('year')

        # 2) Build the reusable base domain from client & projectNo
        base = []
        if client and client != 'All':
            base.append(('customer_id.name', '=', client))
        if projectNo and projectNo != 'All':
            base.append(('intended_vessel', '=', projectNo))

        # 3) Handle month/year date window
        if month and month != 'All':
            month_map = {
                'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4,
                'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8,
                'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
            }
            m = month_map.get(month)
            if m:
                y = int(year) if year and year != 'All' else fields.Date.today().year
                start = fields.Date.to_string(fields.Date.from_string(f'{y}-01-01') + timedelta(days=(m-1)*30))
                # approximate month length – you could refine with relativedelta
                end_day = (fields.Date.from_string(f'{y}-{m:02d}-01') + timedelta(days=31)).strftime('%Y-%m-%d')
                base += [
                    ('expected_arrival_date', '>=', f'{y}-{m:02d}-01'),
                    ('expected_arrival_date', '<',  end_day),
                ]

        # 4) Prepare date tokens
        today         = fields.Date.context_today(self)
        tomorrow      = today + timedelta(days=1)
        ninety_days_ago = today - timedelta(days=90)

        # 5) Define the KPI‐specific domain fragments
        kpi_domains = {
            'waitingForInfo':          [('inventory_status', '=', 'draft')],
            'expectedTomorrow':        [('expected_arrival_date', '=', tomorrow)],
            'expectedToday':           [('expected_arrival_date', '=', today)],
            'toBePutInStock':          [('inventory_status', '=', 'arrived')],
            'withoutAllocatedStorage': [
                ('warehouse_id', '=', False),
                ('inventory_status', 'not in', ['draft','cancelled']),
            ],
            'labelsToBePrinted':       [
                ('inventory_status', 'in', ['arrived','allocated']),
            ],
            'longerThan90Days':        [
                ('actual_date_of_arrival', '<', ninety_days_ago),
                ('inventory_status', 'not in', ['done','cancel']),
            ],
            'openOSDInventory':        [
                # customize your OS&D logic here
                ('inventory_status', '=', 'waiting'),
            ],
            'displachedItems':         [
                # customize your displaced-item logic here
                ('inventory_status', '=', 'allocated'),
                ('warehouse_id', '!=', False),
            ],
        }

        # 6) Run search_count for each KPI
        result = {}
        StockPicking = self.env['stock.picking']
        for key, domain_part in kpi_domains.items():
            result[key] = StockPicking.search_count(base + domain_part)

        return result
        