from odoo import models, fields, api
from odoo.exceptions import UserError


class LibraryMember(models.Model):
    _inherit = 'library.member'
    
    # NEW fields for portal functionality:
    user_id = fields.Many2one(
        'res.users',
        string='Portal User',
        help='Linked portal user account',
        ondelete='restrict'
    )
    is_portal_user = fields.Boolean(
        string='Portal Access',
        default=False,
        help='Whether this member has portal access'
    )
    portal_access_token = fields.Char(
        string='Portal Access Token',
        copy=False,
        groups='base.group_user'
    )
    last_portal_login = fields.Datetime(
        string='Last Portal Login',
        readonly=True
    )
    
    # Extension request statistics
    total_extension_requests = fields.Integer(
        string='Total Extension Requests',
        compute='_compute_extension_statistics'
    )
    pending_extension_requests = fields.Integer(
        string='Pending Extension Requests',
        compute='_compute_extension_statistics'
    )
    approved_extension_requests = fields.Integer(
        string='Approved Extension Requests',
        compute='_compute_extension_statistics'
    )
    
    def _compute_extension_statistics(self):
        """Compute extension request statistics"""
        for member in self:
            extension_requests = self.env['library.extension.request'].search([
                ('member_id', '=', member.id)
            ])
            member.total_extension_requests = len(extension_requests)
            member.pending_extension_requests = len(extension_requests.filtered(lambda r: r.status == 'pending'))
            member.approved_extension_requests = len(extension_requests.filtered(lambda r: r.status == 'approved'))
    
    def create_portal_user(self):
        """Create portal user for this member"""
        if self.user_id:
            raise UserError('Portal user already exists for this member.')
        
        if not self.email:
            raise UserError('Email is required to create portal user.')
        
        # Check if user with this email already exists
        existing_user = self.env['res.users'].search([('login', '=', self.email)], limit=1)
        if existing_user:
            raise UserError(f'A user with email {self.email} already exists.')
        
        # Create partner first
        partner_vals = {
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'is_company': False,
            'customer_rank': 1,
        }
        partner = self.env['res.partner'].create(partner_vals)
        
        # Create portal user
        user_vals = {
            'name': self.name,
            'login': self.email,
            'email': self.email,
            'groups_id': [(6, 0, [self.env.ref('base.group_portal').id])],
            'partner_id': partner.id,
            'library_member_id': self.id,
        }
        user = self.env['res.users'].create(user_vals)
        
        self.write({
            'user_id': user.id,
            'is_portal_user': True
        })
        
        return user
    
    def action_create_portal_user(self):
        """Action to create portal user"""
        try:
            user = self.create_portal_user()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Portal User Created',
                    'message': f'Portal user created successfully for {self.name}. Login: {user.login}',
                    'type': 'success',
                }
            }
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error',
                    'message': str(e),
                    'type': 'danger',
                }
            }
    
    def action_reset_portal_password(self):
        """Action to reset portal user password"""
        if not self.user_id:
            raise UserError('No portal user exists for this member.')
        
        # Reset password - will send email to user
        self.user_id.action_reset_password()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Password Reset',
                'message': f'Password reset email sent to {self.email}',
                'type': 'success',
            }
        }