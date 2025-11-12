from odoo.addons.portal.controllers.portal import CustomerPortal, pager
from odoo.http import request
from odoo import http, fields, _
from odoo.tools import groupby as groupbyelem
from operator import itemgetter
from odoo.exceptions import AccessError, UserError
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)


class BookBorrowerPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        """Add library-specific counters to portal home - SIMPLIFIED"""
        rtn = super(BookBorrowerPortal, self)._prepare_home_portal_values(counters)
        rtn['library_member_counts'] = request.env['library.member'].search_count([])
        # Get current user's library member (basic info only)
        # member = request.env.user._get_library_member()
        # if member:
        #     # Only include fields that don't depend on disabled models
        #     rtn.update({
        #         'member': member,
        #         # Disabled fields that depend on BorrowingRecord model:
        #         # 'current_borrowed': member.current_borrowed,
        #         # 'pending_extension_requests': member.pending_extension_requests,
        #         # 'overdue_books_count': member.overdue_books_count,
        #         # 'total_fines': member.total_fines,
        #     })

        return rtn

    def _get_member_or_redirect(self):
        """Get current user's library member or redirect to access denied"""
        member = request.env.user._get_library_member()
        if not member:
            return request.render('book_borrower_portal.no_member_access')
        return member

    # Route: Create Member for Current User (Simplified)
    @http.route(['/my/create-member'], type='http', methods=['GET'], auth='user', website=True)
    def create_member_for_user(self, **kwargs):
        """Create a library member record for the current user automatically"""
        user = request.env.user
        
        try:
            # Check if member already exists
            existing_member = request.env['library.member'].search([
                ('user_id', '=', user.id)
            ], limit=1)
            
            if existing_member:
                # Redirect to profile if member exists
                return request.redirect('/my/profile')
            
            # Create member record automatically
            member = request.env['library.member'].sudo().create({
                'name': user.name,
                'email': user.email,
                'phone': '',  # Empty phone initially
                'user_id': user.id,
                'is_portal_user': True,
                'member_status': 'active',
                'join_date': fields.Date.today(),
            })
            
            # Redirect to profile to edit details
            return request.redirect('/my/profile?registration=success')
            
        except Exception as e:
            # Show error in no access template with additional info
            values = {
                'error_message': f"Failed to create member account: {str(e)}",
            }
            return request.render('book_borrower_portal.no_member_access', values)

    # Route 1: Member Profile
    @http.route(['/my/profile'], type='http', methods=['GET', 'POST'], auth='user', website=True)
    def member_profile(self, **kwargs):
        """Member profile management"""
        member = self._get_member_or_redirect()
        if not isinstance(member, request.env['library.member'].__class__):
            return member  # Return the error page
        
        values = {
            'member': member,
            'page_name': 'member_profile',
        }
        
        # Check if this is after successful registration
        if kwargs.get('registration') == 'success':
            values['success_msg'] = "Welcome! Your member account has been created successfully. You can now edit your profile details below."
        
        if request.httprequest.method == 'POST':
            errors = []
            
            # Validate form data
            name = kwargs.get('name', '').strip()
            email = kwargs.get('email', '').strip()
            phone = kwargs.get('phone', '').strip()
            
            if not name:
                errors.append("Name is required.")
            if not email:
                errors.append("Email is required.")
            
            if not errors:
                try:
                    member.write({
                        'name': name,
                        'email': email,
                        'phone': phone,
                    })
                    # Also update user email if different
                    if member.user_id and member.user_id.email != email:
                        member.user_id.write({'email': email, 'login': email})
                    
                    values['success_msg'] = "Profile updated successfully!"
                except Exception as e:
                    errors.append(str(e))
            
            if errors:
                values['errors'] = errors
        
        return request.render("book_borrower_portal.member_profile_view", values)

    # Route 2: Public Member List
    @http.route(['/my/members', '/my/members/page/<int:page>'], type='http', auth='user', website=True)
    def member_list(self, page=1, search='', **kwargs):
        """Display all library members"""
        
        # Search domain
        domain = []
        if search:
            domain = ['|', ('name', 'ilike', search), ('email', 'ilike', search)]
        
        # Get members
        Member = request.env['library.member']
        total_members = Member.search_count(domain)
        
        # Pagination
        page_detail = pager(
            url='/my/members',
            total=total_members,
            page=page,
            step=20,
            url_args={'search': search}
        )
        
        # Fetch member records
        members = Member.search(
            domain,
            limit=20,
            offset=page_detail['offset'],
            order='name asc'
        )
        
        values = {
            'members': members,
            'page_name': 'member_list',
            'pager': page_detail,
            'search': search,
            'total_members': total_members,
        }
        
        return request.render("book_borrower_portal.member_list_view", values)

    # Route 3: Borrowed Books List - TEMPORARILY DISABLED
    @http.route(['/my/borrowed-books', '/my/borrowed-books/page/<int:page>'],
                 type='http', auth='user', website=True)
    def borrowed_books_list(self, page=1, sortby='sequence', filterby='all', search='', **kwargs):
        """Display all borrowed books"""
        member = self._get_member_or_redirect()
        if not isinstance(member, request.env['library.member'].__class__):
            return member
        
        # Sorting options using correct field names
        sort_options = {
            'sequence': {'label': 'Record Number', 'order': 'sequence desc'},
            'borrow_date': {'label': 'Borrow Date', 'order': 'borrow_date desc'},
            'expected_return_date': {'label': 'Due Date', 'order': 'expected_return_date asc'},
            'book_title': {'label': 'Book Title', 'order': 'book_title asc'}
        }
        
        # Filter options using correct field names
        filter_options = {
            'all': {'label': 'All', 'domain': [('member_id', '=', member.id)]},
            'borrowed': {'label': 'Currently Borrowed', 'domain': [('member_id', '=', member.id), ('status', '=', 'borrowed')]},
            'overdue': {'label': 'Overdue', 'domain': [('member_id', '=', member.id), ('status', '=', 'overdue')]},
            'returned': {'label': 'Returned', 'domain': [('member_id', '=', member.id), ('status', '=', 'returned')]}
        }
        
        # Build search domain
        domain = filter_options[filterby]['domain']
        if search:
            domain += [('book_title', 'ilike', search)]
        
        # Get borrowing records
        BorrowingRecord = request.env['library.borrowing.record']
        total_records = BorrowingRecord.search_count(domain)
        
        # Pagination
        page_detail = pager(
            url='/my/borrowed-books',
            total=total_records,
            page=page,
            step=20,
            url_args={'sortby': sortby, 'filterby': filterby, 'search': search}
        )
        
        # Fetch records
        borrowing_records = BorrowingRecord.search(
            domain,
            limit=20,
            offset=page_detail['offset'],
            order=sort_options[sortby]['order']
        )
        
        values = {
            'borrowing_records': borrowing_records,
            'member': member,
            'page_name': 'borrowed_books',
            'pager': page_detail,
            'sortby': sortby,
            'filterby': filterby,
            'search': search,
            'sort_options': sort_options,
            'filter_options': filter_options,
        }
        
        return request.render("book_borrower_portal.borrowed_books_list_view", values)

    # Route 3: Book Borrow Details
    @http.route(['/my/borrowed-books/<int:borrowing_id>'], type='http', auth='user', website=True)
    def borrowing_detail(self, borrowing_id, **kwargs):
        """Detailed view of single borrowing record"""
        member = self._get_member_or_redirect()
        if not isinstance(member, request.env['library.member'].__class__):
            return member
        
        # Get borrowing record and check access
        borrowing_record = request.env['library.borrowing.record'].browse(borrowing_id)
        if not borrowing_record.exists() or borrowing_record.member_id != member:
            return request.not_found()
        
        # Navigation between records
        all_records = request.env['library.borrowing.record'].search([
            ('member_id', '=', member.id)
        ], order='sequence desc')
        
        record_ids = all_records.ids
        current_index = record_ids.index(borrowing_record.id)
        
        prev_record = next_record = False
        if current_index > 0:
            prev_record = all_records.browse(record_ids[current_index - 1])
        if current_index < len(record_ids) - 1:
            next_record = all_records.browse(record_ids[current_index + 1])
        
        # Check for pending extension requests
        pending_extension_request = request.env['library.extension.request'].search([
            ('borrowing_record_id', '=', borrowing_record.id),
            ('status', '=', 'pending')
        ], limit=1)
        
        # Check if extension can be requested
        can_request_extension = (
            borrowing_record.status == 'borrowed' and
            borrowing_record.expected_return_date >= fields.Date.today() and
            not pending_extension_request
        )
        
        values = {
            'borrowing_record': borrowing_record,
            'member': member,
            'page_name': 'borrowing_detail',
            'prev_record': prev_record,
            'next_record': next_record,
            'pending_extension_request': pending_extension_request,
            'can_request_extension': can_request_extension,
        }
        
        return request.render("book_borrower_portal.borrowing_detail_view", values)

    # Route 4: Request Extension
    @http.route(['/my/borrowed-books/<int:borrowing_id>/request-extension'], 
                type='http', methods=['GET', 'POST'], auth='user', website=True)
    def request_extension(self, borrowing_id, **kwargs):
        """Submit extension request"""
        member = self._get_member_or_redirect()
        if not isinstance(member, request.env['library.member'].__class__):
            return member
        
        # Get borrowing record and check access
        borrowing_record = request.env['library.borrowing.record'].browse(borrowing_id)
        if not borrowing_record.exists() or borrowing_record.member_id != member:
            return request.not_found()
        
        # Check if extension can be requested
        can_request = (
            borrowing_record.status == 'borrowed' and
            borrowing_record.expected_return_date >= fields.Date.today()
        )
        
        # Check for existing pending requests
        existing_pending_request = request.env['library.extension.request'].search([
            ('borrowing_record_id', '=', borrowing_record.id),
            ('status', '=', 'pending')
        ], limit=1)
        
        if not can_request or existing_pending_request:
            reason = None
            if not can_request and borrowing_record.status != 'borrowed':
                reason = "This book is not currently borrowed."
            elif not can_request and borrowing_record.expected_return_date < fields.Date.today():
                reason = "This book is overdue. Extensions cannot be requested for overdue books."
            elif existing_pending_request:
                reason = f"There is already a pending extension request ({existing_pending_request.name}) for this borrowing record. Please wait for it to be processed."
            
            return request.render("book_borrower_portal.extension_not_allowed", {
                'borrowing_record': borrowing_record,
                'member': member,
                'reason': reason,
                'existing_request': existing_pending_request
            })
        
        # Default extension date (14 days from expected return date)
        default_extension_days = int(request.env['ir.config_parameter'].sudo().get_param(
            'book_borrower_portal.extension_days', 14))
        default_requested_date = borrowing_record.expected_return_date + timedelta(days=default_extension_days)
        
        values = {
            'borrowing_record': borrowing_record,
            'member': member,
            'page_name': 'request_extension',
            'default_requested_date': default_requested_date
        }
        
        if request.httprequest.method == 'POST':
            errors = []
            
            # Get form data
            requested_date_str = kwargs.get('requested_expiry_date')
            request_reason = kwargs.get('request_reason', '')
            
            if not requested_date_str:
                errors.append("Requested expiry date is required.")
            
            if not errors:
                try:
                    requested_date = fields.Date.from_string(requested_date_str)
                    
                    # Create extension request
                    extension_request = request.env['library.extension.request'].create({
                        'borrowing_record_id': borrowing_record.id,
                        'requested_expiry_date': requested_date,
                        'request_reason': request_reason,
                        'status': 'pending'
                    })
                    
                    # Send notification email
                    extension_request._send_request_notification()
                    
                    values['success_msg'] = "Extension request submitted successfully! You will be notified once reviewed."
                    
                except Exception as e:
                    errors.append(str(e))
            
            if errors:
                values['errors'] = errors
        
        return request.render("book_borrower_portal.extension_request_form", values)

    # Route 5: Extension Requests History
    @http.route(['/my/extension-requests', '/my/extension-requests/page/<int:page>'], 
                type='http', auth='user', website=True)
    def extension_requests_list(self, page=1, sortby='request_date', filterby='all', **kwargs):
        """View all extension requests"""
        member = self._get_member_or_redirect()
        if not isinstance(member, request.env['library.member'].__class__):
            return member
        
        # Sorting options
        sort_options = {
            'request_date': {'label': 'Request Date', 'order': 'request_date desc'},
            'status': {'label': 'Status', 'order': 'status, request_date desc'},
            'book_title': {'label': 'Book Title', 'order': 'book_id, request_date desc'}
        }
        
        # Filter options
        filter_options = {
            'all': {'label': 'All', 'domain': [('member_id', '=', member.id)]},
            'pending': {'label': 'Pending', 'domain': [('member_id', '=', member.id), ('status', '=', 'pending')]},
            'approved': {'label': 'Approved', 'domain': [('member_id', '=', member.id), ('status', '=', 'approved')]},
            'rejected': {'label': 'Rejected', 'domain': [('member_id', '=', member.id), ('status', '=', 'rejected')]}
        }
        
        # Build domain
        domain = filter_options[filterby]['domain']
        
        # Get extension requests
        ExtensionRequest = request.env['library.extension.request']
        total_requests = ExtensionRequest.search_count(domain)
        
        # Pagination
        page_detail = pager(
            url='/my/extension-requests',
            total=total_requests,
            page=page,
            step=20,
            url_args={'sortby': sortby, 'filterby': filterby}
        )
        
        # Fetch requests
        extension_requests = ExtensionRequest.search(
            domain,
            limit=20,
            offset=page_detail['offset'],
            order=sort_options[sortby]['order']
        )
        
        values = {
            'extension_requests': extension_requests,
            'member': member,
            'page_name': 'extension_requests',
            'pager': page_detail,
            'sortby': sortby,
            'filterby': filterby,
            'sort_options': sort_options,
            'filter_options': filter_options,
        }
        
        return request.render("book_borrower_portal.extension_requests_list_view", values)

    # Route 6: Extension Request Details
    @http.route(['/my/extension-requests/<int:request_id>'], type='http', auth='user', website=True)
    def extension_request_detail(self, request_id, **kwargs):
        """Detailed view of extension request"""
        member = self._get_member_or_redirect()
        if not isinstance(member, request.env['library.member'].__class__):
            return member
        
        # Get extension request and check access
        extension_request = request.env['library.extension.request'].browse(request_id)
        if not extension_request.exists() or extension_request.member_id != member:
            return request.not_found()
        
        values = {
            'extension_request': extension_request,
            'member': member,
            'page_name': 'extension_request_detail',
        }
        
        return request.render("book_borrower_portal.extension_request_detail_view", values)

    # Route 7: Download Borrowing Report
    @http.route(['/my/borrowed-books/print/<int:borrowing_id>'], 
                type='http', auth='user', website=True)
    def borrowing_report_pdf(self, borrowing_id, **kwargs):
        """Generate PDF report for borrowing record"""
        member = self._get_member_or_redirect()
        if not isinstance(member, request.env['library.member'].__class__):
            return member
        
        # Get borrowing record and check access
        borrowing_record = request.env['library.borrowing.record'].browse(borrowing_id)
        if not borrowing_record.exists() or borrowing_record.member_id != member:
            return request.not_found()
        
        # Generate and return PDF report
        try:
            # Try to find the report action
            report_action = request.env['ir.actions.report'].search([
                ('report_name', '=', 'book_borrower_portal.borrowing_record_report_template')
            ], limit=1)
            
            if not report_action:
                # Create a simple report action on the fly if not found
                report_action = request.env['ir.actions.report'].sudo().create({
                    'name': 'Borrowing Record Report',
                    'model': 'library.borrowing.record',
                    'report_type': 'qweb-pdf',
                    'report_name': 'book_borrower_portal.borrowing_record_report_template',
                })
            
            pdf_content, content_type = report_action._render_qweb_pdf(borrowing_record.ids)
            
            # Set up the response
            pdfhttpheaders = [
                ('Content-Type', 'application/pdf'),
                ('Content-Length', len(pdf_content)),
                ('Content-Disposition', f'attachment; filename="Borrowing_Record_{borrowing_record.sequence}.pdf"')
            ]
            
            return request.make_response(pdf_content, headers=pdfhttpheaders)
            
        except Exception as e:
            _logger.error(f"Error generating borrowing record PDF: {str(e)}")
            # Fallback: render HTML version if PDF fails
            try:
                values = {
                    'docs': [borrowing_record],
                    'doc_ids': [borrowing_record.id],
                    'doc_model': 'library.borrowing.record',
                    'datetime': __import__('datetime'),
                }
                html_content = request.env['ir.qweb']._render('book_borrower_portal.borrowing_record_report_template', values)
                
                return request.make_response(html_content, headers=[
                    ('Content-Type', 'text/html'),
                    ('Content-Disposition', f'inline; filename="Borrowing_Record_{borrowing_record.sequence}.html"')
                ])
            except Exception as html_error:
                _logger.error(f"Error generating HTML fallback: {str(html_error)}")
                # Final fallback: simple text response
                error_msg = f"Error generating report: {str(e)}\nHTML fallback error: {str(html_error)}"
                return request.make_response(error_msg, headers=[('Content-Type', 'text/plain')])

    # Route 8: Download Extension Request Report
    @http.route(['/my/extension-requests/print/<int:request_id>'], 
                type='http', auth='user', website=True)
    def extension_request_report_pdf(self, request_id, **kwargs):
        """Generate PDF report for extension request"""
        member = self._get_member_or_redirect()
        if not isinstance(member, request.env['library.member'].__class__):
            return member
        
        # Get extension request and check access
        extension_request = request.env['library.extension.request'].browse(request_id)
        if not extension_request.exists() or extension_request.member_id != member:
            return request.not_found()
        
        # Generate and return PDF report
        try:
            # Try to find the report action
            report_action = request.env['ir.actions.report'].search([
                ('report_name', '=', 'book_borrower_portal.extension_request_report_template')
            ], limit=1)
            
            if not report_action:
                # Create a simple report action on the fly if not found
                report_action = request.env['ir.actions.report'].sudo().create({
                    'name': 'Extension Request Report',
                    'model': 'library.extension.request',
                    'report_type': 'qweb-pdf',
                    'report_name': 'book_borrower_portal.extension_request_report_template',
                })
            
            pdf_content, content_type = report_action._render_qweb_pdf([extension_request.id])
            
            # Set up the response
            pdfhttpheaders = [
                ('Content-Type', 'application/pdf'),
                ('Content-Length', len(pdf_content)),
                ('Content-Disposition', f'attachment; filename="Extension_Request_{extension_request.name}.pdf"')
            ]
            
            return request.make_response(pdf_content, headers=pdfhttpheaders)
            
        except Exception as e:
            _logger.error(f"Error generating extension request PDF: {str(e)}")
            # Fallback: render HTML version if PDF fails
            try:
                values = {
                    'docs': [extension_request],
                    'doc_ids': [extension_request.id],
                    'doc_model': 'library.extension.request',
                    'datetime': __import__('datetime'),
                }
                html_content = request.env['ir.qweb']._render('book_borrower_portal.extension_request_report_template', values)
                
                return request.make_response(html_content, headers=[
                    ('Content-Type', 'text/html'),
                    ('Content-Disposition', f'inline; filename="Extension_Request_{extension_request.name}.html"')
                ])
            except Exception as html_error:
                _logger.error(f"Error generating HTML fallback: {str(html_error)}")
                # Final fallback: simple text response
                error_msg = f"Error generating report: {str(e)}\nHTML fallback error: {str(html_error)}"
                return request.make_response(error_msg, headers=[('Content-Type', 'text/plain')])
