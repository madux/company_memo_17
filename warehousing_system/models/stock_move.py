from odoo import api, fields, models

class StockMove(models.Model):
    _inherit = 'stock.move'

    #item descrition = description_picking
    #length (in mtr) = 
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
    #Chargeable Space in m2
    area_chargeable = fields.Float(String="Chargeable Space(m2)")

    
    #Preview img