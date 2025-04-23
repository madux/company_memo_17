from odoo import api, fields, models
from dateutil.relativedelta import relativedelta

class WarehouseDashboard(models.TransientModel):
    _name = 'warehouse.dashboard'
    _description = 'Warehouse Inventory Dashboard'

    client_id  = fields.Many2one('res.partner', string='Client', domain=[('customer_rank','>',0)])
    file_type  = fields.Selection([
        ('warehouse','Warehouse'),
        ('inventory','Inventory'),
        ('shipment','Shipment')
    ], string='File Type')
    project_no = fields.Char(string='Project No.')
    month      = fields.Selection([
        ('jan','Jan'),('feb','Feb'),('mar','Mar'),
        ('apr','Apr'),('may','May'),('jun','Jun'),
        ('jul','Jul'),('aug','Aug'),('sep','Sep'),
        ('oct','Oct'),('nov','Nov'),('dec','Dec')
    ], string='Month')
    year       = fields.Selection(lambda self: [(str(y), str(y)) for y in range(2020,2030)],
                                 string='Year')

    def action_create_tiles(self):
        """ Build one transient tile per KPI and open their kanban. """
        # clear any old tiles
        self.env['warehouse.dashboard.tile'].search([]).unlink()

        # build the domain filters
        domain = []
        if self.client_id:
            domain.append(('customer_id','=',self.client_id.id))
        if self.project_no:
            domain.append(('intended_vessel','ilike', self.project_no))
        # ... include month/year like before ...

        # helper to count pickings
        Picking = self.env['stock.picking']
        today    = fields.Date.context_today(self)
        tomorrow = today + relativedelta(days=1)
        counts = {
            'waiting_for_info':  Picking.search_count(domain + [('inventory_status','=','draft')]),
            'expected_tomorrow': Picking.search_count(domain + [('expected_arrival_date','=',tomorrow)]),
            'expected_today':    Picking.search_count(domain + [('expected_arrival_date','=',today)]),
            'items_to_put':      Picking.search_count(domain + [
                                     ('inventory_status','=','arrived'),
                                     ('state','not in',['done','cancel'])
                                 ]),
            'without_storage':   Picking.search_count(domain + [
                                     ('inventory_status','=','arrived'),
                                     ('location_dest_id','=',False)
                                 ]),
            'labels_to_print':   Picking.search_count(domain + [
                                     ('inventory_status','=','arrived'),
                                     ('state','!=','done'),
                                     # ('labels_printed','=',False)
                                 ]),
            'items_90days':      Picking.search_count(domain + [
                                     ('inventory_status','=','allocated'),
                                     ('actual_date_of_arrival','<', today - relativedelta(days=90))
                                 ]),
            'open_osd':          Picking.search_count(domain + [
                                     ('inventory_status','=','allocated'),
                                     # ('is_osd','=',True)
                                 ]),
            'displaced_items':   Picking.search_count(domain + [
                                     ('inventory_status','=','allocated'),
                                     # ('is_displaced','=',True)
                                 ]),
        }

        # human titles & icons
        titles = {
            'waiting_for_info':  'Inventory Items Waiting for Info',
            'expected_tomorrow': 'Inventory Items Expected Tomorrow',
            'expected_today':    'Inventory Items Expected Today',
            'items_to_put':      'Items to be Put in Stock',
            'without_storage':   'Inventory Items without Storage',
            'labels_to_print':   'Labels to be Printed',
            'items_90days':      'Items > 90 days in Stock',
            'open_osd':          'Open OS&D Inventory',
            'displaced_items':   'Displaced Inventory Items',
        }
        icons = {
            'waiting_for_info':  'fa-info-circle',
            'expected_tomorrow': 'fa-hourglass-half',
            'expected_today':    'fa-clock-o',
            'items_to_put':      'fa-shopping-cart',
            'without_storage':   'fa-ban',
            'labels_to_print':   'fa-print',
            'items_90days':      'fa-calendar',
            'open_osd':          'fa-lock',
            'displaced_items':   'fa-truck',
        }

        Tile = self.env['warehouse.dashboard.tile']
        for key, cnt in counts.items():
            Tile.create({
                'key'       : key,
                'title'     : titles[key],
                'icon'      : icons[key],
                'count'     : cnt,
                'dashboard_id': self.id,
            })

        # open the kanban on tiles
        return {
            'type'      : 'ir.actions.act_window',
            'name'      : 'Warehouse Dashboard',
            'res_model' : 'warehouse.dashboard.tile',
            'view_mode' : 'kanban',
            'target'    : 'current',
            'context'   : {'search_default_dashboard': self.id},
        }


class WarehouseDashboardTile(models.TransientModel):
    _name = 'warehouse.dashboard.tile'
    _description = 'Single KPI Tile for Warehouse Dashboard'
    _rec_name = 'title'
    _order = 'key'

    dashboard_id = fields.Many2one('warehouse.dashboard', string='Dashboard')
    key          = fields.Char(required=True)
    title        = fields.Char(required=True)
    icon         = fields.Char(required=True)
    count        = fields.Integer()
