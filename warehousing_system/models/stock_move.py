from odoo import api, fields, models
import io
import base64
import qrcode

class StockMove(models.Model):
    _inherit = 'stock.move'

    #item descrition = description_picking
    #length (in mtr) = 
    is_label_printed = fields.Boolean(String="Label Printed")
    length_mtr = fields.Integer(String="Length (mtr)")
    #width (in mtr) =
    width_mtr = fields.Integer(String="Width (mtr)")
    # Height (in mtr) =
    height_mtr = fields.Integer(String="Height (mtr)")
    #Item value (Naira)
    item_value = fields.Float(String="Item Value (Naira)")
    #Customer Reference = restrict_partner_id
    #Amount of inner package per item = product_qty product_uom product_uom_qty quantity
    #Weight (kg) per Item
    weight_per_item = fields.Float(String="Weight per item (Kg)")
    
    #Space occupied in m2
    area_m2 = fields.Float(String="Space occupied (m2)")
    #Space Occupied in m3
    volume_m3 = fields.Float(String="Space occupied (m3)")
    area_chargeable = fields.Float(String="Chargeable Space(m2)")
    
    show_details_visible = fields.Boolean('Details Visible', default=True)
    no_of_items = fields.Float('No. of items', help="No of item in each box")
    item_picture = fields.Binary("Picture")
    qr_code = fields.Binary(string="QR Code")
    
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

