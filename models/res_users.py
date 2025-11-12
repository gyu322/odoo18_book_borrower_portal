from odoo import models, fields, api


class ResUsers(models.Model):
    _inherit = 'res.users'
    
    library_member_id = fields.Many2one(
        'library.member',
        string='Library Member',
        help='Linked library member record'
    )
    
    def _get_library_member(self):
        """Get library member for current user"""
        self.ensure_one()
        if self.library_member_id:
            return self.library_member_id
        
        # Try to find by email
        member = self.env['library.member'].search([
            ('email', '=', self.email),
            ('is_portal_user', '=', True)
        ], limit=1)
        
        if member:
            member.user_id = self.id
            self.library_member_id = member.id
            return member
        
        return self.env['library.member']
    
    @api.model
    def _update_last_login(self):
        """Update last portal login for library members"""
        result = super()._update_last_login()
        
        # Update last portal login for library members
        if self.has_group('base.group_portal') and self.library_member_id:
            self.library_member_id.sudo().write({
                'last_portal_login': fields.Datetime.now()
            })
        
        return result