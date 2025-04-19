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


    financial_id = fields.Many2one(
        'purchase.order',
        string="Financial File / PO",
        help="Refers to the Purchase Order associated with this inventory receipt."
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
    
    ####### Added this fields to allw this module work
    
    user_owned_cash_advance_ids = fields.Many2many(
        'memo.model', 
        'user_owned_cash_warehouse_advance_rel',
        'user_owned_cash_warehouse_advance_id',
        'memo_id', string="User owned cash helpdesk advances", store=False)
    
    approver_ids = fields.Many2many(
        'hr.employee',
        'memo_model_warehouse_employee_rel',
        'memo_id',
        'hr_employee_id',
        string='Approvers',
    )

    invoice_ids = fields.Many2many(
        'account.move',
        'memo_invoice_warehouse_rel',
        'memo_id',
        'invoice_id',
        string='Invoices',
        store=True,
        domain="[('type', 'in', ['in_invoice', 'in_receipt']), ('state', '!=', 'cancel')]",
    )

    partner_ids = fields.Many2many(
        'res.partner',
        'memo_res_warehouse_partner_rel',
        'memo_id',
        'partner_id',
        string='Recipients',
    )

    attachment_ids = fields.Many2many(
        'ir.attachment',
        'memo_ir_attachment_warehouse_rel',
        'memo_id',
        'attachment_id',
        string='Attachments',
        store=True,
        domain="[('res_model', '=', 'memo.model')]",
    )

    memo_sub_stage_ids = fields.Many2many(
        'memo.sub.stage',
        'memo_sub_stage_warehouse_rel',
        'memo_id',
        'sub_stage_id',
        string='Sub‑Stages',
        store=True,
    )


    def action_pre_allocate(self):
        # Method to transition to 'allocated' status, potentially triggering other logic
        for record in self:
            # Add any pre-allocation logic here (e.g., check availability)
            # record.pre_allocation = True # Uncomment if using the boolean field
            record.inventory_status = 'allocated'
        return True # Standard return for button actions

    # Inherit and extend the confirm action if needed
    def action_confirm(self):
        # Call the original confirm method if it exists and does something important
        res = super(WarehouseInventory, self).action_confirm() if hasattr(super(), 'action_confirm') else True
        for record in self:
            # Set status to 'arrived' if confirming from 'draft'
            if record.inventory_status == 'draft':
                record.inventory_status = 'arrived'
                # Set arrival date only if not already set
                if not record.actual_date_of_arrival:
                    record.actual_date_of_arrival = fields.Date.today()
        return res

    # Onchange to populate supplier PO from financial_id (Purchase Order)
    @api.onchange('financial_id')
    def _onchange_financial_id(self):
        if self.financial_id:
            # Assuming the PO name is the number you want. Adjust if needed.
            self.supplier_po_number = self.financial_id.name or ''
            # You could also fetch the supplier from the PO
            if not self.receiving_supplier_id and self.financial_id.partner_id:
                 self.receiving_supplier_id = self.financial_id.partner_id
        # else: # Optional: Clear the field if financial_id is removed
        #     self.supplier_po_number = ''
        