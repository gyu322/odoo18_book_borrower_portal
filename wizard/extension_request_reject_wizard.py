from odoo import models, fields, api
from odoo.exceptions import UserError


class ExtensionRequestRejectWizard(models.TransientModel):
    _name = 'library.extension.request.reject.wizard'
    _description = 'Extension Request Rejection Wizard'
    
    request_id = fields.Many2one(
        'library.extension.request',
        string='Extension Request',
        required=True,
        readonly=True
    )
    rejection_reason = fields.Text(
        string='Rejection Reason',
        required=True,
        help='Please provide a reason for rejecting this extension request'
    )
    
    def action_reject_request(self):
        """Reject the extension request with reason"""
        self.ensure_one()
        if not self.request_id:
            raise UserError('No extension request specified.')
        
        if self.request_id.status != 'pending':
            raise UserError('Only pending requests can be rejected.')
        
        # Get or create reviewer librarian record using the extension request helper
        reviewer_id = self.request_id._get_or_create_reviewer_librarian()
        
        # Update extension request
        self.request_id.write({
            'status': 'rejected',
            'reviewed_by': reviewer_id,
            'review_date': fields.Datetime.now(),
            'rejection_reason': self.rejection_reason
        })
        
        # Send notification email
        self.request_id._send_rejection_notification()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Extension Rejected',
                'message': f'Extension request {self.request_id.name} has been rejected.',
                'type': 'success',
            }
        }