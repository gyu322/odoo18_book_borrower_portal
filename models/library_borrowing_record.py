from odoo import models, fields, api
from datetime import timedelta
import uuid


class BorrowingRecord(models.Model):
    _inherit = ['library.borrowing.record', 'mail.thread', 'mail.activity.mixin', 'portal.mixin']
    
    # NEW fields for portal extension functionality:
    current_expiry_date = fields.Date(
        string='Current Expiry Date', 
        help='Current due date (updated by extensions)',
        compute='_compute_current_expiry_date',
        store=True
    )
    extension_count = fields.Integer(
        string='Extensions Granted', 
        default=0,
        help='Number of extensions granted for this borrowing'
    )
    can_request_extension = fields.Boolean(
        string='Can Request Extension',
        compute='_compute_can_request_extension',
        help='Whether member can request extension for this borrow'
    )
    extension_request_ids = fields.One2many(
        'library.extension.request', 
        'borrowing_record_id',
        string='Extension Requests'
    )
    
    # Portal access fields
    access_token = fields.Char('Access Token', copy=False, groups='base.group_user')
    access_url = fields.Char('Portal Access URL', compute='_compute_access_url')
    
    @api.depends('expected_return_date', 'extension_count', 'extension_request_ids.status', 'extension_request_ids.new_expiry_date')
    def _compute_current_expiry_date(self):
        """Compute current expiry date based on approved extensions"""
        for record in self:
            # Default to expected return date
            record.current_expiry_date = record.expected_return_date
            
            if record.extension_count > 0 and record.extension_request_ids:
                # Get the latest approved extension
                approved_extensions = record.extension_request_ids.filtered(
                    lambda r: r.status == 'approved'
                ).sorted('review_date', reverse=True)
                if approved_extensions and approved_extensions[0].new_expiry_date:
                    record.current_expiry_date = approved_extensions[0].new_expiry_date
    
    @api.depends('status', 'current_expiry_date', 'extension_count', 'extension_request_ids')
    def _compute_can_request_extension(self):
        """Check if extension can be requested"""
        for record in self:
            # Get configuration parameters
            max_extensions = int(self.env['ir.config_parameter'].sudo().get_param(
                'book_borrower_portal.max_extensions', 2))
            min_days_before_expiry = int(self.env['ir.config_parameter'].sudo().get_param(
                'book_borrower_portal.min_days_before_expiry', 3))
            
            # Check all conditions
            can_request = (
                record.status == 'borrowed' and  # Must be currently borrowed
                record.current_expiry_date >= fields.Date.today() and  # Not overdue
                record.extension_count < max_extensions and  # Haven't exceeded max extensions
                (record.current_expiry_date - fields.Date.today()).days <= min_days_before_expiry and  # Within request window
                not record.extension_request_ids.filtered(lambda r: r.status == 'pending')  # No pending requests
            )
            record.can_request_extension = can_request
    
    def _compute_access_url(self):
        """Compute portal access URL"""
        for record in self:
            record.access_url = f'/my/borrowed-books/{record.id}'
    
    def _portal_ensure_token(self):
        """Ensure access token exists for portal access"""
        if not self.access_token:
            self.access_token = str(uuid.uuid4())
        return self.access_token
    
    def get_portal_url(self, suffix=None, report_type=None, download=None, query_string=None, anchor=None):
        """Get portal URL for this record"""
        self.ensure_one()
        url = self.access_url
        if query_string:
            url += '?' + query_string
        if anchor:
            url += '#' + anchor
        return url