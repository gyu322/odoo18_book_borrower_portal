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
    'author': 'Pang',
    'depends': [
        'library_management_1',  # Primary dependency - contains base models
        'portal',               # Portal functionality
        'mail',                 # Email notifications and chatter
    ],
    'data': [
        # Security
        'security/ir.model.access.csv',
        'security/security.xml',

        # Data - Extension-related files
        'data/ir_sequence_data.xml',
        'data/mail_templates.xml',
        'data/extension_config_data.xml',

        # Views - Extension-related views
        'views/portal_template.xml',
        'views/extension_request_views.xml',
        'views/library_member_views.xml',
        
        # Wizard views
        'wizard/extension_request_reject_wizard_views.xml',

        # Reports
        'reports/borrowing_report.xml',
        'reports/extension_request_report.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            # 'book_borrower_portal/static/src/js/extension_request_form.js',  # TEMPORARILY DISABLED
            # 'book_borrower_portal/static/src/js/borrowed_books_filter.js',  # TEMPORARILY DISABLED
            'book_borrower_portal/static/src/css/portal_styles.css',
        ]
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
