from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class LibraryExtensionRequest(models.Model):
    _name = 'library.extension.request'
    _description = 'Book Borrow Extension Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'request_date desc'
    
    # Reference fields
    name = fields.Char(string='Request Reference', readonly=True, copy=False, default='New')
    borrowing_record_id = fields.Many2one(
        'library.borrowing.record', 
        string='Borrowing Record', 
        required=True, 
        ondelete='cascade'
    )
    member_id = fields.Many2one(
        related='borrowing_record_id.member_id',
        string='Member',
        store=True,
        readonly=True
    )
    book_id = fields.Many2one(
        related='borrowing_record_id.book_id',
        string='Book',
        store=True,
        readonly=True
    )
    
    # Request details
    request_date = fields.Datetime(
        string='Request Date',
        default=fields.Datetime.now,
        required=True,
        readonly=True
    )
    original_expiry_date = fields.Date(
        string='Current Expiry Date',
        help='Current expiry date of the borrowing record at time of request',
        readonly=True
    )
    requested_expiry_date = fields.Date(
        string='Requested New Expiry Date',
        required=True
    )
    request_reason = fields.Text(
        string='Reason for Extension',
        help='Optional reason for requesting extension'
    )
    
    # Status and approval
    status = fields.Selection([
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string='Status', default='pending', required=True, tracking=True)
    
    # Review details
    reviewed_by = fields.Many2one(
        'library.librarian',
        string='Reviewed By',
        readonly=True
    )
    review_date = fields.Datetime(
        string='Review Date',
        readonly=True
    )
    rejection_reason = fields.Text(
        string='Rejection Reason',
        help='Reason for rejecting the extension request'
    )
    new_expiry_date = fields.Date(
        string='Approved New Expiry Date',
        readonly=True,
        help='New expiry date if approved'
    )
    
    # Computed fields
    extension_days = fields.Integer(
        string='Extension Days',
        compute='_compute_extension_days',
        help='Number of days extension requested'
    )
    
    def _get_or_create_reviewer_librarian(self):
        """Get or create a librarian record for the current user"""
        reviewer_id = self.env.context.get('default_librarian_id')
        if reviewer_id:
            return reviewer_id
            
        # Try to find existing librarian record with matching email
        librarian = None
        if self.env.user.email:
            librarian = self.env['library.librarian'].search([('email', '=', self.env.user.email)], limit=1)
        
        if librarian:
            return librarian.id
            
        # Create new librarian record if user has permission
        if self.env.user.has_group('base.group_system') or self.env.user.has_group('base.group_user'):
            # Generate unique employee ID
            existing_count = self.env['library.librarian'].search_count([])
            employee_id = f"LIB{str(existing_count + 1).zfill(3)}"
            
            # Ensure employee ID is unique
            while self.env['library.librarian'].search([('employee_id', '=', employee_id)]):
                existing_count += 1
                employee_id = f"LIB{str(existing_count + 1).zfill(3)}"
            
            librarian = self.env['library.librarian'].create({
                'name': self.env.user.name or 'System User',
                'employee_id': employee_id,
                'email': self.env.user.email or '',
                'phone': getattr(self.env.user, 'phone', '') or '',
                'department': 'administration',
                'position': 'head_librarian' if self.env.user.has_group('base.group_system') else 'librarian',
            })
            return librarian.id
            
        return None
    
    @api.depends('original_expiry_date', 'requested_expiry_date')
    def _compute_extension_days(self):
        """Calculate number of extension days"""
        for record in self:
            if record.original_expiry_date and record.requested_expiry_date:
                delta = record.requested_expiry_date - record.original_expiry_date
                record.extension_days = delta.days
            else:
                record.extension_days = 0
    
    @api.model
    def create(self, vals):
        """Generate sequence number for extension request"""
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].sudo().next_by_code('library.extension.request') or 'New'
        
        # Set original expiry date from borrowing record
        if vals.get('borrowing_record_id') and not vals.get('original_expiry_date'):
            borrowing_record = self.env['library.borrowing.record'].browse(vals['borrowing_record_id'])
            # Use expected_return_date since current_expiry_date may not be available yet
            vals['original_expiry_date'] = borrowing_record.expected_return_date
        
        return super().create(vals)
    
    @api.constrains('requested_expiry_date', 'original_expiry_date')
    def _check_extension_date(self):
        """Validate extension date"""
        for record in self:
            if record.requested_expiry_date and record.original_expiry_date:
                if record.requested_expiry_date <= record.original_expiry_date:
                    raise ValidationError('Requested expiry date must be after current expiry date.')
                
                # Check maximum extension days
                max_extension_days = int(self.env['ir.config_parameter'].sudo().get_param(
                    'book_borrower_portal.max_extension_days', 14))
                if record.extension_days > max_extension_days:
                    raise ValidationError(f'Extension cannot exceed {max_extension_days} days.')
    
    @api.constrains('borrowing_record_id', 'status')
    def _check_pending_requests(self):
        """Prevent multiple pending requests for same borrowing record"""
        for record in self:
            if record.status == 'pending':
                # Check if there's already a pending request for this borrowing record
                existing_pending = self.search([
                    ('borrowing_record_id', '=', record.borrowing_record_id.id),
                    ('status', '=', 'pending'),
                    ('id', '!=', record.id)
                ])
                if existing_pending:
                    raise ValidationError(
                        f'There is already a pending extension request for this borrowing record. '
                        f'Please wait for the current request ({existing_pending[0].name}) to be processed before submitting a new one.'
                    )
    
    def action_approve(self):
        """Approve extension request"""
        self.ensure_one()
        if self.status != 'pending':
            raise UserError('Only pending requests can be approved.')
        
        # Update the borrowing record expected return date
        self.borrowing_record_id.write({
            'expected_return_date': self.requested_expiry_date
        })
        
        # Get or create reviewer librarian record
        reviewer_id = self._get_or_create_reviewer_librarian()
        
        # Update extension request
        self.write({
            'status': 'approved',
            'reviewed_by': reviewer_id,
            'review_date': fields.Datetime.now(),
            'new_expiry_date': self.requested_expiry_date
        })
        
        # Send notification email
        self._send_approval_notification()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Extension Approved',
                'message': f'Extension request {self.name} has been approved.',
                'type': 'success',
            }
        }
    
    def action_reject(self):
        """Reject extension request"""
        self.ensure_one()
        if self.status != 'pending':
            raise UserError('Only pending requests can be rejected.')
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Reject Extension Request',
            'res_model': 'library.extension.request.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_request_id': self.id}
        }
    
    def _send_request_notification(self):
        """Send email notification when extension request is submitted"""
        template = self.env.ref('book_borrower_portal.extension_request_submitted_email', raise_if_not_found=False)
        if template:
            template.sudo().send_mail(self.id, force_send=True)
    
    def _send_approval_notification(self):
        """Send email notification when extension request is approved"""
        template = self.env.ref('book_borrower_portal.extension_request_approved_email', raise_if_not_found=False)
        if template:
            template.sudo().send_mail(self.id, force_send=True)
    
    def _send_rejection_notification(self):
        """Send email notification when extension request is rejected"""
        template = self.env.ref('book_borrower_portal.extension_request_rejected_email', raise_if_not_found=False)
        if template:
            template.sudo().send_mail(self.id, force_send=True)
    
    def name_get(self):
        """Custom name display"""
        result = []
        for record in self:
            name = f"{record.name} - {record.book_id.title}"
            result.append((record.id, name))
        return result