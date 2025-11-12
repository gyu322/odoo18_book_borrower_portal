# Book Borrower Portal - Project Planning Document (Updated)

## 📋 Executive Summary

A comprehensive Odoo 18.0 portal extension that provides book borrowing management functionality through a user-friendly web interface. This module **extends the existing `library_management_1` system** to enable borrowers to manage their profiles, view borrowed books, request borrow extensions, and track extension request history through a dedicated portal interface.

**Key Decision: This portal extends and leverages the existing `library_management_1` models rather than creating new ones, ensuring seamless integration with the current library management system.**

**Project Type:** Odoo Portal Module Development  
**Odoo Version:** 18.0  
**Development Timeline:** 4-6 weeks (estimated)  
**Complexity Level:** Medium  
**Dependencies:** `library_management_1` (Required)

---

## 🎯 Project Objectives

1. Enable library members to manage their personal information through a self-service portal
2. Provide real-time visibility of borrowed books and their status using existing borrowing records
3. Streamline the book borrow extension request process with librarian approval workflow
4. Maintain comprehensive history and audit trail of all extension requests
5. Integrate seamlessly with existing `library_management_1` system without disruption
6. Leverage existing business logic for borrowing, fines, and member management

---

## 📐 Requirements Analysis

### 1. Profile Management
**Description:** Library members should be able to view and edit their personal information

**Features Required:**
- View current profile information from `library.member` model
- Edit personal details (name, email, phone)
- View membership status and borrowing statistics
- Display borrowing history and current borrowed books
- View fine information and overdue books

**Technical Considerations:**
- Extend `library.member` model with portal access
- Form validation (client-side and server-side)
- CSRF protection
- Data sanitization
- Permission checks (users can only edit their own profile)

### 2. Borrowed Books Overview
**Description:** Display a comprehensive list of books borrowed by the member using `library.borrowing.record`

**Data Fields from Existing Model:**
- Book title (`book_title` - related field)
- Book cover image (`book_id.image`)
- Member name (`member_name` - related field)
- Borrow date (`borrow_date`)
- Expected return date (`expected_return_date`)
- Actual return date (`actual_return_date`)
- Current status (`status`: borrowed/returned/overdue)
- Fine amount (`fine_amount`)
- Days overdue (`days_overdue`)
- Borrowing record sequence (`sequence`)
- Librarian who processed (`librarian_id`)

**Features:**
- Sortable columns (by date, title, status)
- Filter by status (Active, Returned, Overdue)
- Search functionality
- Pagination (10-20 records per page)
- Color-coded status indicators
- Overdue warnings
- Days remaining/overdue counter

### 3. Borrow Extension Request
**Description:** Members can request an extension of the borrowing period

**Key Requirements:**
- Subject to librarian approval
- Only available for "borrowed" status books
- Business rules to implement:
  - No extension for overdue books
  - Maximum number of extensions per book (e.g., 2)
  - Minimum days before expiry to request (e.g., 3 days)
  - Extension duration (configurable, default 14 days)

**Data to Record (New Extension Model):**
- Request ID (sequence)
- Book reference (`borrowing_record_id` linking to `library.borrowing.record`)
- Member reference (related from borrowing record)
- Original expiry date (`expected_return_date` from borrowing record)
- Requested extension date
- Request submission date
- Request reason (optional text field)
- Librarian who approved/rejected
- Approval/Rejection date
- Reason for decision
- New expiry date (if approved)

**Workflow:**
```
Member submits request → Pending approval → 
Librarian reviews → Approved/Rejected → 
Member notified → History updated → 
Borrowing record updated (if approved)
```

### 4. Extension History and Status Tracking
**Description:** Members should be able to view the history and status of all their extension requests

**Display Requirements:**
- List all extension requests (past and present)
- Show current status (Pending, Approved, Rejected)
- Display updated expiry dates for approved requests
- Show approval/rejection details
- Timeline view of all activities

**Status Types:**
- **Pending:** Awaiting librarian review (yellow badge)
- **Approved:** Extension granted (green badge)
- **Rejected:** Extension denied (red badge)

**Information to Display:**
- Request date
- Book title (from related borrowing record)
- Original expiry date
- Requested new date
- Status badge
- Librarian name (if processed)
- Decision date
- Reason for rejection (if applicable)
- Comments/notes

---

## 🏗️ Technical Architecture

### Module Structure
```
book_borrower_portal/
├── __init__.py                          # Module initialization
├── __manifest__.py                      # Module configuration
├── models/
│   ├── __init__.py
│   ├── library_borrowing_record.py      # Extend library.borrowing.record
│   ├── library_extension_request.py     # New extension request model
│   ├── library_member.py                # Extend library.member
│   └── res_users.py                     # Link users to library members
├── controllers/
│   ├── __init__.py
│   └── portal.py                        # Main portal controller
├── views/
│   ├── portal_templates.xml             # All portal templates
│   └── extension_request_views.xml      # Backend views for librarian
├── reports/
│   ├── borrowing_report.xml             # Borrowing history report
│   └── extension_request_report.xml     # Extension request report
├── security/
│   ├── ir.model.access.csv              # Access rights
│   └── security.xml                     # Record rules
├── data/
│   ├── mail_templates.xml               # Email notifications
│   └── extension_config_data.xml        # Configuration data
├── static/
│   └── src/
│       ├── js/
│       │   ├── extension_request_form.js  # Extension form validation
│       │   └── borrow_list_filter.js      # List filtering logic
│       ├── css/
│       │   └── portal_styles.css          # Custom styling
│       └── img/
│           └── default_book_cover.png     # Fallback image
└── README.md                             # Module documentation
```

---

## 💾 Database Models Design

### Model 1: library.borrowing.record (Extension)

**Base Model:** Existing `library.borrowing.record` from `library_management_1`  
**Action:** Extend with portal functionality

```python
class BorrowingRecord(models.Model):
    _inherit = 'library.borrowing.record'
    _inherit = ['library.borrowing.record', 'mail.thread', 'mail.activity.mixin', 'portal.mixin']
    
    # Existing fields from library_management_1:
    # - sequence (Char) - Record Number 
    # - member_id (Many2one: library.member) - Link to member
    # - member_name (Char, related) - Member name
    # - book_id (Many2one: library.book) - Link to book
    # - book_title (Char, related) - Book title
    # - librarian_id (Many2one: library.librarian) - Processed by librarian
    # - borrow_date (Date) - When borrowed
    # - expected_return_date (Date) - Original due date
    # - actual_return_date (Date) - When returned (nullable)
    # - status (Selection: borrowed/returned/overdue) - Current status
    # - days_overdue (Integer) - Days overdue
    # - fine_amount (Float) - Calculated fine (RM)
    # - fine_per_day (Float) - Fine per day (RM 5.0)
    # - notes (Text) - Additional notes
    
    # NEW fields for portal extension functionality:
    current_expiry_date = fields.Date(
        string='Current Expiry Date', 
        help='Current due date (updated by extensions)',
        default=lambda self: self.expected_return_date
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
    
    @api.depends('status', 'current_expiry_date', 'extension_count')
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
```

### Model 2: library.extension.request (New Model)

```python
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
        related='borrowing_record_id.current_expiry_date',
        string='Current Expiry Date',
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
            vals['name'] = self.env['ir.sequence'].next_by_code('library.extension.request') or 'New'
        return super().create(vals)
    
    def action_approve(self):
        """Approve extension request"""
        self.ensure_one()
        if self.status != 'pending':
            raise UserError('Only pending requests can be approved.')
        
        # Update the borrowing record
        self.borrowing_record_id.write({
            'current_expiry_date': self.requested_expiry_date,
            'extension_count': self.borrowing_record_id.extension_count + 1
        })
        
        # Update extension request
        self.write({
            'status': 'approved',
            'reviewed_by': self.env.context.get('default_librarian_id'),
            'review_date': fields.Datetime.now(),
            'new_expiry_date': self.requested_expiry_date
        })
        
        # Send notification email
        self._send_approval_notification()
    
    def action_reject(self, reason=None):
        """Reject extension request"""
        self.ensure_one()
        if self.status != 'pending':
            raise UserError('Only pending requests can be rejected.')
        
        self.write({
            'status': 'rejected',
            'reviewed_by': self.env.context.get('default_librarian_id'),
            'review_date': fields.Datetime.now(),
            'rejection_reason': reason or 'No reason provided'
        })
        
        # Send notification email
        self._send_rejection_notification()
```

### Model 3: library.member (Extension)

**Base Model:** Existing `library.member` from `library_management_1`  
**Action:** Extend with portal functionality

```python
class LibraryMember(models.Model):
    _inherit = 'library.member'
    
    # Existing fields from library_management_1:
    # - sequence (Char) - Member Number
    # - name (Char) - Name
    # - email (Char) - Email
    # - phone (Char) - Phone Number
    # - join_date (Date) - Join Date
    # - max_borrow_limit (Integer) - Maximum Borrow Limit
    # - current_borrowed (Integer, computed) - Currently Borrowed
    # - member_status (Selection: active/inactive/pending) - Member Status
    # - borrowing_ids (One2many) - Borrowing Records
    # - total_books_borrowed (Integer, computed) - Total Books Borrowed
    # - total_fines (Float, computed) - Total Fines
    # - overdue_books_count (Integer, computed) - Overdue Books
    # - returned_books_count (Integer, computed) - Returned Books
    
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
    
    @api.depends('borrowing_ids.extension_request_ids')
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
        
        # Create portal user
        user_vals = {
            'name': self.name,
            'login': self.email,
            'email': self.email,
            'groups_id': [(6, 0, [self.env.ref('base.group_portal').id])],
            'partner_id': self._create_or_update_partner().id
        }
        user = self.env['res.users'].create(user_vals)
        
        self.write({
            'user_id': user.id,
            'is_portal_user': True
        })
        
        return user
```

### Model 4: res.users (Extension)

```python
class ResUsers(models.Model):
    _inherit = 'res.users'
    
    library_member_id = fields.Many2one(
        'library.member',
        string='Library Member',
        help='Linked library member record'
    )
    
    def _get_library_member(self):
        """Get library member for current user"""
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
```

---

## 🛣️ Portal Routes Planning

### Route 1: Portal Home Integration
**URL:** `/my`  
**Purpose:** Add borrower portal entries to main portal dashboard  
**Method:** Inherit `portal.portal_my_home`

**Counters to Display:**
- Total active borrows (`current_borrowed` from `library.member`)
- Pending extension requests
- Overdue books count (`overdue_books_count` from `library.member`)
- Total fines (`total_fines` from `library.member`)

### Route 2: Member Profile
**URL:** `/my/profile`  
**Method:** GET, POST  
**Authentication:** User (portal/internal)  
**Purpose:** View and edit member profile using `library.member` model

**Template:** `member_profile_view`

### Route 3: Borrowed Books List
**URL:** `/my/borrowed-books` or `/my/borrowed-books/page/<int:page>`  
**Method:** GET  
**Authentication:** User  
**Purpose:** Display all borrowed books using `library.borrowing.record`

**Query Parameters:**
- `page` - Pagination
- `sortby` - sequence/borrow_date/expected_return_date/book_title
- `filterby` - all/borrowed/returned/overdue
- `search` - Search term

**Template:** `borrowed_books_list_view`

### Route 4: Book Borrow Details
**URL:** `/my/borrowed-books/<int:borrowing_id>`  
**Method:** GET  
**Authentication:** User  
**Purpose:** Detailed view of single `library.borrowing.record`

**Features:**
- Full book details from `book_id`
- Borrowing timeline
- Extension request history
- Download borrowing receipt (PDF)
- Request extension button (if `can_request_extension` is True)

**Template:** `borrowing_detail_view`

### Route 5: Request Extension
**URL:** `/my/borrowed-books/<int:borrowing_id>/request-extension`  
**Method:** GET, POST  
**Authentication:** User  
**Purpose:** Submit extension request for `library.borrowing.record`

**Validations:**
- Book status must be "borrowed"
- Not already overdue
- Not exceeded maximum extensions
- Within allowed timeframe
- No pending extension requests

**Template:** `extension_request_form_view`

### Route 6: Extension Requests History
**URL:** `/my/extension-requests` or `/my/extension-requests/page/<int:page>`  
**Method:** GET  
**Authentication:** User  
**Purpose:** View all `library.extension.request` records

**Query Parameters:**
- `page` - Pagination
- `sortby` - request_date/status/book_title
- `filterby` - all/pending/approved/rejected

**Template:** `extension_requests_list_view`

### Route 7: Extension Request Details
**URL:** `/my/extension-requests/<int:request_id>`  
**Method:** GET  
**Authentication:** User  
**Purpose:** Detailed view of single `library.extension.request`

**Template:** `extension_request_detail_view`

### Route 8: Download Borrowing Report
**URL:** `/my/borrowed-books/print/<int:borrowing_id>`  
**Method:** GET  
**Authentication:** User  
**Purpose:** Generate and download PDF report of `library.borrowing.record`

### Route 9: Download Extension Request Report
**URL:** `/my/extension-requests/print/<int:request_id>`  
**Method:** GET  
**Authentication:** User  
**Purpose:** Generate and download PDF of `library.extension.request`

---

## 🎨 Frontend Templates Planning

### Template 1: Portal Home Menu Integration
**Template ID:** `portal_my_home_borrower`  
**Inherits:** `portal.portal_my_home`

**Menu Items to Add:**
```xml
- My Borrowed Books (icon: book, counter: current_borrowed)
- Request Extension (icon: clock)
- Extension Requests (icon: list, counter: pending_extension_requests)
- My Profile (icon: user)
```

### Template 2: Breadcrumb Navigation
**Template ID:** `borrower_portal_breadcrumbs`  
**Inherits:** `portal.portal_breadcrumbs`

**Breadcrumb Paths:**
- My Account / Borrowed Books
- My Account / Borrowed Books / [Book Title]
- My Account / Extension Requests
- My Account / Extension Requests / [Request Reference]
- My Account / Profile

### Template 3: Member Profile View
**Template ID:** `member_profile_view_portal`  
**Purpose:** Display and edit member information from `library.member`

**Sections:**
1. Basic Information (name, sequence, member_status)
2. Contact Information (email, phone)
3. Membership Details (join_date, max_borrow_limit)
4. Statistics (total_books_borrowed, current_borrowed, total_fines, overdue_books_count)

**Form Fields (from `library.member`):**
- Name (required)
- Email (required, validated)
- Phone (validated)

### Template 4: Borrowed Books List View
**Template ID:** `borrowed_books_list_view_portal`  
**Purpose:** Display all borrowed books from `library.borrowing.record`

**Table Columns (using existing fields):**
- Book Cover (`book_id.image`)
- Book Title (`book_title` - clickable link)
- Author (`book_id.author`)
- Borrow Date (`borrow_date`)
- Expected Return Date (`expected_return_date` or `current_expiry_date`)
- Current Status (`status` - badge)
- Days Overdue (`days_overdue`)
- Fine Amount (`fine_amount`)
- Actions (View Details, Request Extension if `can_request_extension`)

### Template 5: Borrowing Detail View
**Template ID:** `borrowing_detail_view_portal`  
**Purpose:** Comprehensive view of single `library.borrowing.record`

**Layout Sections:**
1. **Book Information**
   - Cover image (`book_id.image`)
   - Title (`book_title`)
   - Author (`book_id.author`)
   - ISBN (`book_id.isbn`)
   - Publisher (`book_id.publisher`)

2. **Borrowing Information**
   - Record number (`sequence`)
   - Borrow date (`borrow_date`)
   - Expected return date (`expected_return_date`)
   - Current expiry date (`current_expiry_date`)
   - Status (`status`)
   - Days overdue (`days_overdue`)
   - Fine amount (`fine_amount`)
   - Extensions used (`extension_count`)
   - Processed by (`librarian_id.name`)

3. **Extension History**
   - List of all `extension_request_ids`
   - Timeline view of extension requests

4. **Actions**
   - Request Extension (if `can_request_extension`)
   - Download PDF Report

### Template 6: Extension Request Form
**Template ID:** `extension_request_form_view_portal`  
**Purpose:** Form to submit extension request for `library.borrowing.record`

**Form Fields (for `library.extension.request`):**
- Book Information (read-only from `borrowing_record_id`)
- Current Expiry Date (`original_expiry_date` - read-only)
- Requested Extension Date (`requested_expiry_date` - date picker)
- Reason for Extension (`request_reason` - textarea, optional)

**Validations:**
- Check `can_request_extension` from borrowing record
- Date validation (must be after current expiry)
- Maximum extension days check

### Template 7: Extension Requests List View
**Template ID:** `extension_requests_list_view_portal`  
**Purpose:** Display all `library.extension.request` records

**Table Columns:**
- Request Reference (`name`)
- Book Title (`book_id.title`)
- Request Date (`request_date`)
- Original Expiry (`original_expiry_date`)
- Requested Expiry (`requested_expiry_date`)
- Status (`status` - badge)
- Reviewed By (`reviewed_by.name`)
- Review Date (`review_date`)

### Template 8: Extension Request Detail View
**Template ID:** `extension_request_detail_view_portal`  
**Purpose:** Detailed view of single `library.extension.request`

**Sections:**
1. **Request Information**
   - Request reference (`name`)
   - Submission date (`request_date`)
   - Status badge (`status`)
   - Extension days (`extension_days`)

2. **Book Information**
   - From related `borrowing_record_id`
   - Current borrow status

3. **Extension Details**
   - Original expiry date (`original_expiry_date`)
   - Requested new date (`requested_expiry_date`)
   - Reason provided (`request_reason`)

4. **Review Information** (if processed)
   - Reviewed by (`reviewed_by.name`)
   - Review date (`review_date`)
   - Decision (`status`)
   - New expiry date (`new_expiry_date` if approved)
   - Rejection reason (`rejection_reason` if rejected)

---

## 📦 Dependencies and Integration

### Required Odoo Modules
- `library_management_1` (Primary dependency - contains all base models)
- `portal` (Core portal functionality)
- `mail` (Chatter, messaging, notifications)
- `web` (Frontend assets)

### Model Dependencies Mapping
```python
# This portal module will use these existing models:
'library.member'           # Main borrower/member model
'library.book'             # Book information  
'library.borrowing.record' # Main borrowing transactions
'library.librarian'        # For approval workflow

# And create these new models:
'library.extension.request' # Extension request workflow
```

### Integration Points
1. **Member Management**: Leverage existing `library.member` with all its business logic
2. **Borrowing Logic**: Use existing `library.borrowing.record` with fine calculation, validations
3. **Book Management**: Access existing `library.book` data and availability
4. **Librarian Workflow**: Integrate with existing `library.librarian` for approvals

---

## ✅ Business Logic & Validations (Leveraging Existing System)

### Extension Request Validations

#### 1. Status Check (using existing field)
```python
if borrowing_record.status != 'borrowed':
    raise ValidationError("Extension can only be requested for currently borrowed books")
```

#### 2. Overdue Check (using existing logic)
```python
if borrowing_record.current_expiry_date < fields.Date.today():
    raise ValidationError("Cannot request extension for overdue books")
```

#### 3. Maximum Extensions Check (new field)
```python
MAX_EXTENSIONS = 2  # Configurable
if borrowing_record.extension_count >= MAX_EXTENSIONS:
    raise ValidationError(f"Maximum {MAX_EXTENSIONS} extensions already used")
```

#### 4. Fine Calculation (existing logic)
```python
# Leverage existing fine calculation from library.borrowing.record
# No need to rebuild - use existing fine_amount and days_overdue fields
```

#### 5. Member Limit Validation (existing logic)
```python
# Use existing validation from library.member
member.check_borrow_limit()  # Existing method
```

---

## 🔔 Notification System

### Email Templates (using existing model data)

#### 1. Extension Request Submitted
**To:** Member (`library.member.email`)  
**Subject:** Extension Request Submitted - [Book Title from `book_id.title`]

#### 2. Extension Request Approved
**To:** Member  
**Subject:** Extension Request Approved - [Book Title]  
**Updates:** `library.borrowing.record.current_expiry_date`

#### 3. Extension Request Rejected
**To:** Member  
**Subject:** Extension Request Not Approved - [Book Title]

---

## 📊 Code Examples with Correct Field Names

### Example 1: Portal Controller Method

```python
@http.route(['/my/borrowed-books'], type='http', auth='user', website=True)
def borrowed_books_list(self, page=1, sortby='sequence', filterby='all', search='', **kwargs):
    # Get current user's library member record
    member = request.env.user._get_library_member()
    if not member:
        return request.not_found()
    
    # Sorting options using correct field names
    sort_options = {
        'sequence': {'label': 'Record Number', 'order': 'sequence desc'},
        'borrow_date': {'label': 'Borrow Date', 'order': 'borrow_date desc'},
        'expected_return_date': {'label': 'Due Date', 'order': 'current_expiry_date asc'},
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
    
    # Get borrowing records using correct model name
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

@http.route(['/my/borrowed-books/<int:borrowing_id>/request-extension'], 
            type='http', methods=['GET', 'POST'], auth='user', website=True)
def request_extension(self, borrowing_id, **kwargs):
    # Get borrowing record using correct model name
    borrowing_record = request.env['library.borrowing.record'].browse(borrowing_id)
    
    # Check access (member can only access their own records)
    member = request.env.user._get_library_member()
    if not member or borrowing_record.member_id != member:
        return request.not_found()
    
    # Check if extension can be requested using computed field
    if not borrowing_record.can_request_extension:
        return request.render("book_borrower_portal.extension_not_allowed", {
            'borrowing_record': borrowing_record,
            'member': member
        })
    
    vals = {
        'borrowing_record': borrowing_record,
        'member': member,
        'page_name': 'request_extension',
        'default_requested_date': borrowing_record.current_expiry_date + timedelta(days=14)
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
                
                # Create extension request using correct model name
                extension_request = request.env['library.extension.request'].create({
                    'borrowing_record_id': borrowing_record.id,
                    'requested_expiry_date': requested_date,
                    'request_reason': request_reason,
                    'status': 'pending'
                })
                
                vals['success_msg'] = "Extension request submitted successfully!"
                
                # Send notification email
                extension_request._send_request_notification()
                
            except Exception as e:
                errors.append(str(e))
        
        if errors:
            vals['errors'] = errors
    
    return request.render("book_borrower_portal.extension_request_form", vals)
```

### Example 2: Template with Correct Field Names

```xml
<template id="borrowed_books_list_view_portal">
    <t t-call="portal.portal_layout">
        <t t-set="title">My Borrowed Books</t>
        
        <div class="container-fluid">
            <!-- Header with member info using correct fields -->
            <div class="row mb-4">
                <div class="col-12">
                    <h2>My Borrowed Books</h2>
                    <div class="alert alert-info">
                        <strong>Member:</strong> <span t-out="member.name"/> (<span t-out="member.sequence"/>)<br/>
                        <strong>Current Borrowed:</strong> <span t-out="member.current_borrowed"/> / <span t-out="member.max_borrow_limit"/><br/>
                        <strong>Total Fines:</strong> RM <span t-out="member.total_fines"/>
                    </div>
                </div>
            </div>
            
            <!-- Search and filters -->
            <div class="row mb-3">
                <div class="col-md-8">
                    <form method="get" class="form-inline">
                        <input type="text" name="search" class="form-control mr-2" 
                               placeholder="Search by book title..." t-att-value="search"/>
                        <button type="submit" class="btn btn-primary">Search</button>
                    </form>
                </div>
                <div class="col-md-4">
                    <select name="filterby" class="form-control" onchange="this.form.submit()">
                        <t t-foreach="filter_options.items()" t-as="filter_item">
                            <option t-att-value="filter_item[0]" 
                                    t-att-selected="'selected' if filterby == filter_item[0] else None">
                                <t t-out="filter_item[1]['label']"/>
                            </option>
                        </t>
                    </select>
                </div>
            </div>
            
            <!-- Borrowing records table -->
            <table class="table table-striped">
                <thead>
                    <tr>
                        <th>Book Cover</th>
                        <th>Book Title</th>
                        <th>Author</th>
                        <th>Borrow Date</th>
                        <th>Due Date</th>
                        <th>Status</th>
                        <th>Fine (RM)</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    <t t-foreach="borrowing_records" t-as="record">
                        <tr>
                            <td>
                                <!-- Using correct field name for book image -->
                                <t t-if="record.book_id.image">
                                    <img t-attf-src="data:image/png;base64,{{record.book_id.image}}" 
                                         alt="Book Cover" class="img-thumbnail" style="width: 60px;"/>
                                </t>
                                <t t-else="">
                                    <img src="/book_borrower_portal/static/img/default_book_cover.png" 
                                         alt="No Cover" class="img-thumbnail" style="width: 60px;"/>
                                </t>
                            </td>
                            <td>
                                <!-- Using correct field name -->
                                <a t-attf-href="/my/borrowed-books/{{record.id}}">
                                    <strong t-out="record.book_title"/>
                                </a>
                            </td>
                            <td t-out="record.book_id.author"/>
                            <td t-out="record.borrow_date"/>
                            <td>
                                <!-- Using current_expiry_date for extended books -->
                                <span t-out="record.current_expiry_date"/>
                                <t t-if="record.extension_count > 0">
                                    <small class="text-info">
                                        (Extended <span t-out="record.extension_count"/> time<t t-if="record.extension_count > 1">s</t>)
                                    </small>
                                </t>
                            </td>
                            <td>
                                <!-- Status badge using correct field -->
                                <span t-attf-class="badge badge-#{{'success' if record.status == 'returned' else 'danger' if record.status == 'overdue' else 'primary'}}">
                                    <t t-out="record.status.title()"/>
                                </span>
                                <!-- Days overdue using correct field -->
                                <t t-if="record.days_overdue > 0">
                                    <br/><small class="text-danger">
                                        <span t-out="record.days_overdue"/> days overdue
                                    </small>
                                </t>
                            </td>
                            <td>
                                <!-- Fine amount using correct field -->
                                <span t-out="record.fine_amount" t-options="{'widget': 'monetary', 'display_currency': 'RM'}"/>
                            </td>
                            <td>
                                <a t-attf-href="/my/borrowed-books/{{record.id}}" class="btn btn-sm btn-outline-primary">
                                    View Details
                                </a>
                                <!-- Extension button using computed field -->
                                <t t-if="record.can_request_extension">
                                    <a t-attf-href="/my/borrowed-books/{{record.id}}/request-extension" 
                                       class="btn btn-sm btn-outline-success">
                                        Request Extension
                                    </a>
                                </t>
                            </td>
                        </tr>
                    </t>
                </tbody>
            </table>
            
            <!-- Pagination -->
            <t t-call="portal.pager"/>
        </div>
    </t>
</template>
```

### Example 3: Extension Request Model Method

```python
def _send_request_notification(self):
    """Send email notification when extension request is submitted"""
    template = self.env.ref('book_borrower_portal.extension_request_submitted_email')
    
    # Email context using correct field names
    email_values = {
        'email_to': self.member_id.email,  # Using library.member.email
        'email_from': self.env.company.email,
        'subject': f'Extension Request Submitted - {self.book_id.title}',  # Using library.book.title
    }
    
    # Template context with correct field references
    template_context = {
        'member_name': self.member_id.name,  # library.member.name
        'book_title': self.book_id.title,    # library.book.title
        'book_author': self.book_id.author,  # library.book.author
        'request_reference': self.name,      # library.extension.request.name
        'original_expiry': self.original_expiry_date,
        'requested_expiry': self.requested_expiry_date,
        'extension_days': self.extension_days,
        'borrowing_sequence': self.borrowing_record_id.sequence,  # library.borrowing.record.sequence
    }
    
    template.with_context(**template_context).send_mail(
        self.id, 
        force_send=True,
        email_values=email_values
    )
```

---

## 📋 Updated Module Manifest

```python
{
    'name': 'Book Borrower Portal',
    'version': '1.0.0',
    'category': 'Portal',
    'summary': 'Portal interface for library members to manage borrowed books and extension requests',
    'description': """
Book Borrower Portal

A comprehensive portal extension for library members that integrates with the existing 
library_management_1 system to provide:

- Member profile management
- Borrowed books overview and tracking
- Extension request submission and tracking  
- PDF reports and notifications
- Mobile-responsive interface

This module extends the existing library_management_1 models rather than creating new ones,
ensuring seamless integration with your current library management system.
    """,
    'author': 'Your Company',
    'depends': [
        'library_management_1',  # Primary dependency - contains base models
        'portal',               # Portal functionality
        'mail',                 # Email notifications and chatter
    ],
    'data': [
        # Security
        'security/ir.model.access.csv',
        'security/security.xml',
        
        # Data
        'data/ir_sequence_data.xml',
        'data/mail_templates.xml',
        'data/extension_config_data.xml',
        
        # Views
        'views/portal_templates.xml',
        'views/extension_request_views.xml',
        'views/library_member_views.xml',
        
        # Reports
        'reports/borrowing_report.xml',
        'reports/extension_request_report.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'book_borrower_portal/static/src/js/extension_request_form.js',
            'book_borrower_portal/static/src/js/borrowed_books_filter.js',
            'book_borrower_portal/static/src/css/portal_styles.css',
        ]
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
```

---

## 🎯 Development Phases (Updated)

### Phase 1: Foundation (Week 1)
- [ ] Set up module structure with correct dependencies
- [ ] Extend existing `library.borrowing.record` model with portal fields
- [ ] Create new `library.extension.request` model
- [ ] Extend `library.member` model with portal functionality
- [ ] Define access rights and security rules
- [ ] Set up basic controller structure inheriting from CustomerPortal
- [ ] Create portal home integration

**Deliverables:**
- Module skeleton with correct model extensions
- Working model extensions with proper field mappings
- Portal menu entries showing correct counters

### Phase 2: Core Features (Week 2-3)
- [ ] Implement member profile management using `library.member`
- [ ] Build borrowed books list view using `library.borrowing.record`
- [ ] Create borrowing detail view with all related information
- [ ] Implement search and filtering using existing field names
- [ ] Add pagination and sorting
- [ ] Create extension request functionality with `library.extension.request`
- [ ] Implement business logic validations leveraging existing system

**Deliverables:**
- Working profile page with existing member data
- Complete borrowed books listing with all existing fields
- Extension request form with proper validations
- Business logic integration with existing library system

### Phase 3: Advanced Features (Week 4)
- [ ] Build extension requests history view
- [ ] Implement extension request detail view
- [ ] Create PDF reports using existing model data
- [ ] Set up email notifications with correct field references
- [ ] Integrate with existing librarian approval workflow
- [ ] Test integration with existing fine calculation system

**Deliverables:**
- Complete extension workflow integrated with existing system
- Email notifications using existing model data
- PDF reports with proper field mappings
- Librarian backend views for approval

### Phase 4: Integration & Testing (Week 5)
- [ ] Test portal access with existing library members
- [ ] Verify all field mappings and relationships work correctly
- [ ] Test business logic integration (borrowing limits, fines, etc.)
- [ ] Validate that existing library management functions still work
- [ ] Cross-browser testing and responsive design validation
- [ ] Performance testing with existing data

**Deliverables:**
- Fully integrated portal working with existing library data
- Validated system that doesn't break existing functionality
- Performance-optimized interface

### Phase 5: Documentation & Deployment (Week 6)
- [ ] Write user documentation with correct field references
- [ ] Create admin guide for integration
- [ ] Document model extensions and relationships
- [ ] Prepare deployment checklist
- [ ] Create data migration scripts if needed
- [ ] Deploy to production with existing library system

**Deliverables:**
- Complete documentation with correct model references
- Deployment package ready for existing library system
- Training materials for library staff and members

---

## 📊 Success Metrics

### Integration Success Metrics
1. **Seamless Data Flow**: All existing library data accessible through portal
2. **No Disruption**: Existing library management functions continue to work
3. **Data Consistency**: Portal shows same data as backend library system
4. **Performance**: Portal doesn't slow down existing library operations

### User Adoption Metrics
1. **Member Portal Usage**: Number of library members using portal
2. **Extension Request Usage**: Reduction in manual extension requests
3. **Self-Service**: Reduction in staff time for member inquiries

---

## 🎓 Best Practices for Model Extension

### 1. Extend, Don't Replace
```python
# GOOD - Extend existing model
class BorrowingRecord(models.Model):
    _inherit = 'library.borrowing.record'
    # Add portal-specific fields

# BAD - Create duplicate model  
class BookBorrow(models.Model):
    _name = 'book.borrow'
    # Duplicate existing functionality
```

### 2. Use Related Fields
```python
# GOOD - Use related fields from existing models
member_name = fields.Char(related='borrowing_record_id.member_id.name')
book_title = fields.Char(related='borrowing_record_id.book_id.title')

# BAD - Store duplicate data
member_name = fields.Char(string='Member Name')  # Duplicates library.member.name
```

### 3. Leverage Existing Computed Fields
```python
# GOOD - Use existing computed fields
total_fines = fields.Float(related='member_id.total_fines')

# BAD - Recompute existing calculations
total_fines = fields.Float(compute='_compute_fines')  # Already computed in library.member
```

---

## 🎯 Conclusion

This updated plan leverages the robust `library_management_1` system while adding portal functionality. By extending existing models rather than creating new ones, we ensure:

- **Data Consistency**: Single source of truth for all library data
- **Business Logic Reuse**: Leverage existing validations and calculations  
- **Seamless Integration**: Portal works with existing library workflows
- **Faster Development**: Focus on portal features, not rebuilding library logic
- **Maintainability**: Changes to library system automatically reflect in portal

**Next Steps:**
1. Review and approve this integration approach
2. Set up development environment with `library_management_1` dependency
3. Begin Phase 1 implementation focusing on model extensions
4. Regular testing to ensure integration doesn't break existing functionality

---

**Document Version:** 2.0 (Updated for library_management_1 Integration)  
**Last Updated:** [Current Date]  
**Dependencies:** library_management_1 v1.0.0  
**Project:** Book Borrower Portal - Odoo 18.0 (Integrated with Existing Library System)