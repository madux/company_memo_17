from odoo import api, fields, models

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
    
    
class WarehouseInventory(models.Model):
    _inherit = 'memo.model'
    
    warehousefig_id = fields.Many2one(
        'memo.config', 
        string="Category", 
        )
    customer_partner_id = fields.Many2one('res.partner', string='Customer ID')
    customer_state_id = fields.Many2one('res.country.state', string='State')
    
    financial_id = fields.Many2one(
        'purchase.order',
        string="Financial File",
        help="Refers to the purchase order or the office memo record containing the PO"
    )

    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string="Warehouse",
        help="Select the warehouse in which this picking/transfer will occur."
    )
    
    inventory_status = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('arrived', "Arrived at Warehouse"),
        ('allocated', "Allocated"),
        ('waiting', 'Waiting'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled')
    ], default='draft')

    actual_date_of_arrival = fields.Date(string="Actual Arrival Date")

    receiving_supplier_id = fields.Many2one('res.partner', string="Receiving Supplier")
    supplier_po_number = fields.Char(string="Supplier PO Number")
    receiving_waybill_number = fields.Char(string="Waybill Number (RL/AWB)")
    expected_arrival_date = fields.Date(string="Expected Arrival Date")

    critical_equipment = fields.Selection([
        ('none', "None Critical"),
        ('safety', "Safety Critical"),
        ('operations', "Operations Critical"),
        ('date_sensitive', "Date Sensitive"),
        ('hazard', "Hazard Material"),
    ], string="Critical Equipment")

    intended_vessel = fields.Char(string="Intended Vessel")
    customer_id = fields.Many2one('res.partner', string="Customer")

    # 7) Pre-allocation status or logic
    #    This might be a boolean or separate selection.  Alternatively, you can just
    #    have a button that triggers a method below.
    # pre_allocation = fields.Boolean(string="Pre-Allocation", default=False)

    #    Pre-allocation.
    def action_pre_allocate(self):
        for picking in self:
            picking.pre_allocation = True
            picking.inventory_status = 'allocated'
        return True

    def action_confirm(self):
        res = super(WarehouseInventory, self).action_confirm()
        for picking in self:
            if picking.inventory_status == 'draft':
                picking.inventory_status = 'arrived'
                picking.actual_date_of_arrival = fields.Date.today()
        return res
    
    @api.onchange('financial_id')
    def _onchange_financial_id(self):
        if self.financial_id:
            self.supplier_po_number = self.financial_id.name or ''
    

