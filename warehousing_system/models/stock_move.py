from odoo import api, fields, models
import io
import base64
import qrcode
from odoo.exceptions import ValidationError


class StockMove(models.Model):
    _inherit = 'stock.move'

    #item descrition = description_picking
    #length (in mtr) = 
    is_label_printed = fields.Boolean(String="Label Printed")
    length_mtr = fields.Integer(String="Length (mm)")
    #width (in mtr) =
    width_mtr = fields.Integer(String="Width (mm)")
    # Height (in mtr) =
    height_mtr = fields.Integer(String="Height (mm)")
    #Item value (Naira)
    item_value = fields.Float(String="Item Value (Naira)")
    #Customer Reference = restrict_partner_id
    #Amount of inner package per item = product_qty product_uom product_uom_qty quantity
    #Weight (kg) per Item
    weight_per_item = fields.Float(String="Weight per item (Kg)")
    
    #Space occupied in m2
    area_m2 = fields.Float(String="Space occupied (m2)",
                           compute="compute_stockmove_measure"
    )

    @api.depends('length_mtr', 'height_mtr', 'width_mtr')
    def compute_stockmove_measure(self):
        rec = self
        if rec.move_line_ids:#: .length_mtr or rec.move_line_ids.height_mtr or rec.move_line_ids.width_mtr:
            volume, height, width, length = 0,0,0,0 
            for ml in rec.move_line_ids:
                # if ml.length_mtr or ml.height_mtr or ml.width_mtr:
                volume += (ml.length_mtr * ml.height_mtr * ml.width_mtr)
                height += ml.height_mtr
                width += ml.width_mtr
                length += ml.length_mtr
                # rec.width_mtr += ml.width_mtr
                # rec.length_mtr += ml.length_mtr
                
            rec.volume_m3 = volume
            rec.area_m2 = height * width
            rec.height_mtr = height
            rec.width_mtr = width
            rec.length_mtr = length
        else:
            rec.volume_m3 = 0
            rec.area_m2 = 0
            rec.length_mtr = 0
            rec.height_mtr = 0
            rec.width_mtr = 0
                
    #Space Occupied in m3
    volume_m3 = fields.Float(String="Space occupied (m3)")#, compute="compute_stockmove_measure")
    area_chargeable = fields.Float(String="Chargeable Space(m2)")
    
    show_details_visible = fields.Boolean('Details Visible', default=True)
    no_of_items = fields.Float('No. of items', help="No of item in each box")
    item_picture = fields.Binary("Picture")
    qr_code = fields.Binary(string="QR Code")
    dispatch_picking_id = fields.Many2one(
        'stock.picking',
        string="Dispatch Stock Picking",
    )
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'stock_move_attachment_ids_rel',
        'attachment_id',
        'stock_id'
    )
    critical_equipment = fields.Selection([
        ('none', "None Critical"),
        ('safety', "Safety Critical"),
        ('operations', "Operations Critical"),
        ('date_sensitive', "Date Sensitive"),
        ('hazard', "Hazard Material"),
    ], string="Critical Equipment")
    
    item_classification_critical = fields.Boolean(
        string="Critical")
    item_classification_dangerous = fields.Boolean(
        string="Dangerous Goods")
    item_classification_temperature = fields.Boolean(
        string="Temperature Sensitive")
    
    remaining_qty = fields.Float(
        string="Remaining Qty", 
        store=True)
    
    # @api.depends('product_uom_qty')
    # def compute_product_uom_qty(self):
    #     for r in self:
    #         if r.product_uom_qty:
    #             r.remaining_qty = r.product_uom_qty
    #         else:
    #             r.remaining_qty = 0
    
    balance_qty = fields.Float(
        string="Balance Qty", 
        # compute="compute_balance_qty",
        )
    
    # @api.depends("remaining_qty")
    @api.onchange("product_uom_qty")
    def compute_balance_qty(self):
        for r in self:
            if r.product_uom_qty:
                balance = r.remaining_qty - r.product_uom_qty 
                r.balance_qty = balance
            else:
                r.balance_qty = 0
    
    def create_qr_code(self, code):
        qr = qrcode.QRCode()
        qr.add_data(code)
        return qr.make_image(fill_color="black", back_color="white")
    
    def generate_qr_code(self):
        img = self.create_qr_code(self.name)
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        self.write({
            'qr_code': img_str,
        })
        
    def print_way_bill_item(self):
        self.is_label_printed = True 
        self.generate_qr_code()
        return self.env.ref('warehousing_system.print_waybill_item_report').report_action(self)

    def validate_dispatch_lines(self):
        if self.move_line_ids:
            for count, ml in enumerate(self.move_line_ids, 1):
                total_stock_availability_in_location = self.env['stock.quant'].sudo()._get_available_quantity(ml.product_id, ml.location_dest_id, allow_negative=False) # or 0.0
                if ml.quantity > total_stock_availability_in_location:
                    raise ValidationError(f"At line {count}: The quantity to dispatch is lesser than the amount remaining in the inventory location. The product {(ml.product_id.name)} available quantity is {total_stock_availability_in_location}")
        else:
            raise ValidationError("""
                                  This dispatch does not have any product / items 
                                  allocation during receipts""")

    @api.constrains('move_line_ids')
    def check_stock_allocation_quantity(self):
        quantity = self.quantity
        total_move_qty = sum([r.quantity for r in self.move_line_ids])
        
        if self.product_uom_qty < total_move_qty:
            raise ValidationError(f"""Ops, you cannot proceed because the Allocated Store line total quantity ({total_move_qty}) is greater than the quantity to recieve {self.product_uom_qty}
                                """)
            
            
class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    is_label_printed = fields.Boolean(String="Label Printed")
    length_mtr = fields.Integer(String="Length (mm)")
    width_mtr = fields.Integer(String="Width (mm)")
    height_mtr = fields.Integer(String="Height (mm)")
    item_value = fields.Float(String="Item Value (Naira)")
    weight_per_item = fields.Float(String="Weight per item (Kg)")
    
    #Space occupied in m2
    area_m2 = fields.Float(String="Space occupied (m2)",
                           compute="compute_stockmove_measure"
    )

    @api.depends('length_mtr', 'height_mtr', 'width_mtr')
    def compute_stockmove_measure(self):
        for rec in self:
            if rec.length_mtr or rec.height_mtr or rec.width_mtr:
                volume = rec.length_mtr * rec.height_mtr * rec.width_mtr
                rec.volume_m3 = volume
                rec.area_m2 = rec.height_mtr * rec.width_mtr
            else:
                rec.volume_m3 = 0
                rec.area_m2 = 0
                
    #Space Occupied in m3
    volume_m3 = fields.Float(String="Space occupied (m3)", compute="compute_stockmove_measure")
    area_chargeable = fields.Float(String="Chargeable Space(m2)")