from odoo import models, fields

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    inventory_memo_id = fields.Many2one(
        'memo.model',
        string="Warehouse Inventory Memo",
        help="When you receive goods, link them back to the warehouse‐inventory record."
    )

    receiving_waybill_number = fields.Char(string="Waybill Number (RL/AWB)")
    # waybill_number    = fields.Char(string="Waybill Number (RL/AWB)")
    bl_awb_number     = fields.Char(string="BL / AWB Number")
    arrived_goods_img = fields.Binary(string="Image of Arrived Goods")
