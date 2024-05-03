from odoo import models, fields, api, _
from odoo.exceptions import ValidationError 

MEMOTYPES = [
        'Payment',
        'loan',
        'Internal',
        'employee_update',
        'material_request',
        'procurement_request',
        'vehicle_request',
        'leave_request',
        'server_access',
        'cash_advance',
        'soe',
        'recruitment_request',
        ] 
DEFAULT_STAGES = [
    'Draft', 'Awaiting approval', 'Done'
]

class MemoSubStageLine(models.Model):
    _name = "memo.sub.stage"

    name = fields.Char("Name", required=True)
    memo_id = fields.Many2one(
        "memo.model", 
        string="Memo Ref"
        )
    sub_stage_id = fields.Many2one(
        "memo.stage", 
        string="Stage id"
        )
    sub_stage_done = fields.Boolean("Is Done", default=False)
    invoice_ids = fields.Many2many(
        'account.move', 
        'memo_sub_invoice_rel',
        'memo_sub_invoice_id',
        'invoice_sub_memo_id',
        string='Invoice', 
        store=True,
        domain="[('move_type', 'in', ['in_invoice', 'in_receipt']), ('state', '!=', 'cancel')]"
        )
    
    attachment_ids = fields.Many2many(
        'ir.attachment', 
        'memo_sub_stage_ir_attachment_rel',
        'memo_sub_ir_attachment_id',
        'ir_sub_attachment_memo_id',
        string='Attachment', 
        store=True,
        domain="[('res_model', '=', '0')]"
        )

    def confirm_sub_stage_done(self):
        self.responsible_approver_right()
        if self.sub_stage_id.required_document_line:
            self.validate_compulsory_document()
        if self.sub_stage_id.required_invoice_line:
            self.validate_invoice_line()
        self.sub_stage_done = True

    def responsible_approver_right(self):
        user =  self.env.user
        if not user.id in [r.user_id.id for r in self.sub_stage_id.approver_ids] or user.id in [r.user_id.id for r in self.sub_stage_id.memo_config_id.approver_ids]:
            raise ValidationError("You are not allowed to validate this task / process")

    def validate_compulsory_document(self):
        """Check if compulsory documents have uploaded"""  
        attachments = self.mapped('attachment_ids').filtered(
                    lambda iv: not iv.datas
                )
        if attachments:
            for count, doc in enumerate(attachments, 1):
                matching_attachment = self.sub_stage_id.mapped('required_document_line').filtered(
                    lambda dc: dc.name == doc.name
                )
                matching_stage_doc = matching_attachment and matching_attachment[0]
                if matching_stage_doc.compulsory and not doc.datas:
                    raise ValidationError(f"Attachment with name '{doc.stage_document_name}' at line {count} does not have any data attached")

    def validate_invoice_line(self):
        '''Check all invoice in draft and check if 
        the current stage that matches it is compulsory
        if compulsory, system validates it'''
        
        invoice_ids = self.mapped('invoice_ids').filtered(
                    lambda iv: iv.state in ['draft']
                )
        # if self.memo_type.memo_key == "Payment" and invoice_ids:
        if invoice_ids:
            for count, inv in enumerate(invoice_ids, 1):
                matching_stage_invoice = self.sub_stage_id.mapped('required_invoice_line').filtered(
                    lambda rinv: rinv.name == inv.stage_invoice_name
                )
                matching_stage_invoice = matching_stage_invoice and matching_stage_invoice[0]
                if matching_stage_invoice.compulsory:
                    if inv.payment_state not in ['paid', 'partial', 'in_payment']:
                        raise ValidationError(f"Invoice at line {count} must be posted and paid before proceeding")

                    invoice_line = inv.mapped('invoice_line_ids')
                    if not invoice_line:
                        raise ValidationError(f"Add at least one invoice billing line at line {count}")
                    invoice_line_without_price = inv.mapped('invoice_line_ids').filtered(
                        lambda s: s.price_unit <= 0
                        )
                    if invoice_line_without_price:
                        raise ValidationError(f"All invoice line must have a price amount greater than 0 at line {count}")
                # else:
                #     self.invoice_ids = [(3, inv.id)]


class MemoStageDocumentLine(models.Model):
    _name = "memo.stage.document.line"

    name = fields.Char("Name", required=True)
    compulsory = fields.Boolean("Compulsory", default=False)
    # memo_stage_id = fields.Many2one(
    #     "memo.stage", 
    #     string="Memo stage Ref"
    #     )
    memo_document_id = fields.Many2one(
        "memo.model", 
        string="Memo Ref"
        )
    

class MemoStageInvoiceLine(models.Model):
    _name = "memo.stage.invoice.line"

    name = fields.Char("Name", required=True)
    compulsory = fields.Boolean("Is Compulsory", default=False)
    memo_invoice_id = fields.Many2one(
        "memo.model",
        string="Memo Ref"
        )
    move_type = fields.Selection(
        [
        ("customer", "Customer Invoice"),
        ("vendor", "Vendor Bills"),
        ],
        string="Invoice type",
        required=True,
    )
    
class MemoLogisticItems(models.Model):
    _name = "logistic.items"

    memo_type_key = fields.Char('Memo type key')
    memo_id = fields.Many2one(
        "memo.model",
        string="Memo id"
        )
    product_id = fields.Many2one(
        "product.product",
        string="Item"
        )
    source_location_id = fields.Many2one(
        "stock.location",
        string="Source location"
        )
    destination_location_id = fields.Many2one(
        "stock.location",
        string="Destination location"
        )
    stock_picking_id = fields.Many2one(
        "stock.picking",
        string="Picking ref"
        )
    quantity_to_move = fields.Integer("Quantity to move", required=True)


class MemoType(models.Model):
    _name = "memo.type"
    _description = "Memo Type"

    name = fields.Char("Name", required=True)
    memo_key = fields.Char(
        "Key", 
        required=True,
        help="""e.g material_request; This is used to 
        request the static Id of the memo type for use in conditioning
        """,
        )
    active = fields.Boolean("Active", default=True)
    allow_for_publish = fields.Boolean("Allow to be published?", default=True)

class MemoStage(models.Model):
    _name = "memo.stage"
    _description = "Memo Stage"
    _order = 'sequence'

    name = fields.Char("Name", required=False)
    sequence = fields.Integer("Sequence", required=False)
    active = fields.Boolean("Active", default=True)
    is_approved_stage = fields.Boolean("Is approved stage", help="if set true, it is used to determine if this stage is the final approved stage")
    approver_id = fields.Many2one("hr.employee", string="Responsible Approver")
    approver_ids = fields.Many2many("hr.employee", string="Responsible Approvers")
    memo_config_id = fields.Many2one("memo.config", string="Parent settings", required=False)
    loaded_from_data = fields.Boolean(string="Loaded from data", default=False)
    # has_condition = fields.Selection([
    #     ("none", ""),
    #     ("yes", "Yes"),
    #     ("no", "No"),
    #     ],
    #     string="Has condition",
    #     required=False,
    #     help="If there is a condition of yer or no, system determines what stage to jump or move back to"
    # )
    memo_has_condition = fields.Boolean(string="Has condition",
                                      default=False, 
                                      help="If there is a condition of yer or no, system determines what stage to jump or move back to")
    
    yes_condition = fields.Boolean(string="Yes",
                                      default=False, 
                                      help="if condition is Yes, set the stage for yes condition")
    no_condition = fields.Boolean(string="No",
                                      default=False, 
                                      help="if condition is No, set the stage for No condition")

    @api.onchange('memo_has_condition')
    def onchange_has_condition(self):
        if self.memo_has_condition:
            self.yes_condition = True
            self.no_condition = True
        else:
            self.yes_condition = False
            self.no_condition = False

    # if system has condition,user must select stage to jump to
    yes_conditional_stage_id = fields.Many2one(
        "memo.stage", 
        string="Yes Conditional stage",
        help="Shows list of all the stages that has memo_config_id")
    
    no_conditional_stage_id = fields.Many2one(
        "memo.stage", 
        string="No Conditional stage",
        help="Shows list of all the stages that has memo_config_id")
    
    dummy_memo_config_stage_ids = fields.Many2many(
        "memo.stage", 
        "dummy_memo_stage_rel",
        "dummy_memo_stage_id",
        "memo_stage_id",
        string="dummy config stages",
        help="Shows list of all the stages that has memo_config_id",
        compute="show_all_related_memo_config_stage")
    sub_stage_ids = fields.Many2many(
        "memo.stage",
        "sub_stage_rel",
        "sub_memo_stage_id",
        "memo_stage_id",
        string="Sub stages",
        help="This are sub stages of the parent stage")
    is_sub_stage = fields.Boolean("Is sub stage", default=False)

    required_invoice_line = fields.Many2many(
        'memo.stage.invoice.line',
        'memo_stage_invoice_rel',
        'memo_stage_invoice_id',
        'memo_stage_id',
        string='Invoice line required'
        )
    required_document_line = fields.Many2many(
        'memo.stage.document.line',
        'memo_stage_document_rel',
        'memo_stage_document_id',
        'memo_stage_id',
        string='Documents required'
        )
    
    @api.depends("memo_config_id")
    def show_all_related_memo_config_stage(self):
        if self.memo_config_id:
            memo_stage_ids = self.memo_config_id.mapped('stage_ids').filtered(lambda s: not s.is_sub_stage)
            self.dummy_memo_config_stage_ids = memo_stage_ids.ids
        else:
            self.dummy_memo_config_stage_ids = False

    @api.constrains('sequence')
    def _validate_sequence(self):
        """Check to ensure that record does not have same sequence"""
        if not self.loaded_from_data:
            memo_duplicate = self.env['memo.stage'].search([
                ('memo_config_id.memo_type', '=', self.memo_config_id.memo_type.id),
                ('sequence', '=', self.sequence),
                ('memo_config_id.department_id', '=', self.memo_config_id.department_id.id)
                ])
            if memo_duplicate and len(memo_duplicate.ids) > 1:
                raise ValidationError("You have already created a stage with the same sequence")


class MemoConfig(models.Model):
    _name = "memo.config"
    _description = "Memo setting"
    _rec_name = "memo_type"

    # memo_type = fields.Selection(
    #     [
    #     ("Payment", "Payment"),
    #     ("loan", "Loan"),
    #     ("Internal", "Internal Memo"),
    #     ("employee_update", "Employee Update Request"),
    #     ("material_request", "Material request"),
    #     ("procurement_request", "Procurement Request"),
    #     ("vehicle_request", "Vehicle request"),
    #     ("leave_request", "Leave request"),
    #     ("server_access", "Server Access Request"),
    #     ("cash_advance", "Cash Advance"),
    #     ("soe", "Statement of Expense"),
    #     ("recruitment_request", "Recruitment Request"),
    #     ], string="Memo Type",default="", required=True)
    def get_publish_memo_types(self):
        return [('allow_for_publish', '=', True)]

    memo_type = fields.Many2one(
        'memo.type',
        string='Memo type',
        required=True,
        copy=False,
        domain=lambda self: self.get_publish_memo_types()
        )
    
    approver_ids = fields.Many2many(
        'hr.employee',
        'hr_employee_memo_config_rel',
        'hr_employee_memo_id',
        'config_memo_id',
        string="Employees for Final Validation",
        required=True
        )
    
    stage_ids = fields.Many2many(
        'memo.stage',
        'memo_stage_rel',
        'memo_stage_id', 
        'memo_config_id',
        string="Stages",
        required=True,
        store=True,
        copy=False,
        domain = lambda self: self._get_related_stages()
        )

    department_id = fields.Many2one(
        'hr.department',
        string='Department',
        required=True,
        copy=False
        )
    active = fields.Boolean(string="Active", default=True)
    allowed_for_company_ids = fields.Many2many(
        'res.partner', 
        'res_partner_memo_config_rel',
        'partner_id',
        'memo_setting_id',
        string="Allowed companies",
        help="""
        If companies are selected, this will allow 
        employees with external user option to select 
        the list from the portal
        """
        )

    @api.constrains('memo_type')
    def _check_duplicate_memo_type(self):
        memo = self.env['memo.config'].sudo()
        for rec in self:
            duplicate = memo.search([('memo_type', '=', rec.memo_type.id),('department_id', '=', rec.department_id.id)], limit=2)
            if len([r for r in duplicate]) > 1:
                raise ValidationError("A memo type has already been configured for this record, kindly locate it and select the approvers")

    def _get_related_stages(self):
        if self.id:
            stage_ids = self.env['memo.stage'].search([('memo_config_id', '=', self.id)]) 
            return [('id', 'in', stage_ids.ids)]

    def auto_configuration(self):
        # TODO: To be used to dynamically generate configurations 
        # for all departments using default stages such as 
        # Draft, Awaiting approval, Done
        # This will be used if no manual stages and configuration is done
        """Loop all departments, 
            Loop via memo type that does not have memo type and the department generated,
            if not found, 
            create or generate a memo.config --> Create the memo stages as above and then
            the Awaiting approval stage should be assigned with the department parent id
              memo that does not departments that does not have memo types configured"""
        approval_stage = DEFAULT_STAGES[1]
        department_ids = self.env['hr.department'].search([])
        MEMOTYPES = self.env['memo.type'].search([])
        if department_ids:
            for department in department_ids:
                for memotype in MEMOTYPES:
                    existing_memo_config = self.env['memo.config'].search([
                        ('memo_type.memo_key','=', memotype), 
                        ('department_id', '=',department.id)
                        ], limit=1
                        )
                    if not existing_memo_config:
                        memo_type_id = self.env['memo.type'].search([
                            ('memo_key','=', memotype.memo_key)]
                            , limit=1)
                        if not memo_type_id:
                            raise ValidationError(f'Memo type with key {memotype} does not exist. Contact admin to configure')
                        memo_config_vals = {
                            'active': True,
                            'memo_type': memo_type_id.id,
                            'department_id': department.id,
                        }
                        memo_config = self.env['memo.config'].create(memo_config_vals)
                        stages = []
                        for count, st in enumerate(DEFAULT_STAGES):
                            stage_id = self.env['memo.stage'].create(
                                {'name': st,
                                 'approver_ids': [(4, department.manager_id.id)] if st == approval_stage else False,
                                 'memo_config_id': memo_config.id,
                                 'is_approved_stage': True if st == approval_stage else False,
                                 'active': True,
                                 'sequence': count
                                 }
                            )
                            stages.append(stage_id.id)
                        memo_config.stage_ids = [(6, 0, stages)]

    def custom_duplicate(self):
        return {
            'name': 'Duplicate Memo Config',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'memo.config.duplication.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_employees_follow_up_ids': self.approver_ids.ids,
                'default_allowed_companies_ids': self.allowed_for_company_ids.ids,
            },
        }


class MemoCategory(models.Model):
    _name = "memo.category"
    _description = "Memo document Category"

    name = fields.Char('Name')
