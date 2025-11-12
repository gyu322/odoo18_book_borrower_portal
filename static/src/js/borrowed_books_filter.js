/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { _t } from "@web/core/l10n/translation";

publicWidget.registry.BorrowedBooksFilter = publicWidget.Widget.extend({
    selector: '.o_portal_my_doc_table',
    events: {
        'click .filter-status': '_onFilterStatus',
        'input .search-books': '_onSearchBooks',
        'change .sort-books': '_onSortBooks',
    },

    start: function() {
        this._super.apply(this, arguments);
        this._initializeFilters();
        this._highlightOverdue();
        return Promise.resolve();
    },

    _initializeFilters: function() {
        // Add search input if not exists
        if (!this.$('.search-books').length) {
            const searchHTML = `
                <div class="input-group mb-3">
                    <input type="text" class="form-control search-books" placeholder="Search books...">
                    <div class="input-group-append">
                        <span class="input-group-text"><i class="fa fa-search"></i></span>
                    </div>
                </div>
            `;
            this.$el.before(searchHTML);
        }
    },

    _highlightOverdue: function() {
        // Highlight overdue books
        this.$('tr').each((index, row) => {
            const $row = $(row);
            const statusBadge = $row.find('.badge-danger');
            if (statusBadge.length && statusBadge.text().trim().toLowerCase().includes('overdue')) {
                $row.addClass('table-danger');
            }
        });

        // Add urgency indicators
        this._addUrgencyIndicators();
    },

    _addUrgencyIndicators: function() {
        this.$('tbody tr').each((index, row) => {
            const $row = $(row);
            const dueDateCell = $row.find('td:nth-child(3)'); // Due date column
            const dueDateText = dueDateCell.text().trim();
            
            if (dueDateText) {
                const dueDate = new Date(dueDateText.split('\n')[0]); // Get main date, ignore extension text
                const today = new Date();
                const diffTime = dueDate - today;
                const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

                let indicator = '';
                let indicatorClass = '';

                if (diffDays < 0) {
                    indicator = '<i class="fa fa-exclamation-triangle text-danger"></i> Overdue';
                    indicatorClass = 'table-danger';
                } else if (diffDays === 0) {
                    indicator = '<i class="fa fa-clock-o text-warning"></i> Due Today';
                    indicatorClass = 'table-warning';
                } else if (diffDays <= 2) {
                    indicator = '<i class="fa fa-clock-o text-warning"></i> Due Soon';
                    indicatorClass = 'table-warning';
                } else if (diffDays <= 7) {
                    indicator = '<i class="fa fa-calendar text-info"></i> Due This Week';
                    indicatorClass = 'table-info';
                }

                if (indicator) {
                    $row.addClass(indicatorClass);
                    dueDateCell.append(`<br><small>${indicator}</small>`);
                }
            }
        });
    },

    _onFilterStatus: function(ev) {
        const status = $(ev.currentTarget).data('status');
        this._filterByStatus(status);
    },

    _onSearchBooks: function(ev) {
        const searchTerm = $(ev.currentTarget).val().toLowerCase();
        this._searchBooks(searchTerm);
    },

    _onSortBooks: function(ev) {
        const sortBy = $(ev.currentTarget).val();
        this._sortBooks(sortBy);
    },

    _filterByStatus: function(status) {
        this.$('tbody tr').each((index, row) => {
            const $row = $(row);
            const statusCell = $row.find('.badge');
            const statusText = statusCell.text().toLowerCase().trim();

            if (status === 'all' || statusText.includes(status.toLowerCase())) {
                $row.show();
            } else {
                $row.hide();
            }
        });

        this._updateFilterButtons(status);
    },

    _searchBooks: function(searchTerm) {
        this.$('tbody tr').each((index, row) => {
            const $row = $(row);
            const bookTitle = $row.find('td:first-child').text().toLowerCase();
            const bookAuthor = $row.find('td:first-child small').text().toLowerCase();
            
            if (bookTitle.includes(searchTerm) || bookAuthor.includes(searchTerm)) {
                $row.show();
            } else {
                $row.hide();
            }
        });
    },

    _sortBooks: function(sortBy) {
        const tbody = this.$('tbody');
        const rows = tbody.find('tr').get();

        rows.sort((a, b) => {
            let aVal, bVal;

            switch (sortBy) {
                case 'title':
                    aVal = $(a).find('td:first-child').text().trim();
                    bVal = $(b).find('td:first-child').text().trim();
                    return aVal.localeCompare(bVal);
                
                case 'due_date':
                    aVal = new Date($(a).find('td:nth-child(3)').text().trim().split('\n')[0]);
                    bVal = new Date($(b).find('td:nth-child(3)').text().trim().split('\n')[0]);
                    return aVal - bVal;
                
                case 'status':
                    aVal = $(a).find('.badge').text().trim();
                    bVal = $(b).find('.badge').text().trim();
                    return aVal.localeCompare(bVal);
                
                default:
                    return 0;
            }
        });

        tbody.empty().append(rows);
    },

    _updateFilterButtons: function(activeStatus) {
        this.$('.filter-status').removeClass('active');
        this.$(`.filter-status[data-status="${activeStatus}"]`).addClass('active');
    },
});

// Extension request status tracking
publicWidget.registry.ExtensionRequestStatus = publicWidget.Widget.extend({
    selector: '.extension-request-table',
    
    start: function() {
        this._super.apply(this, arguments);
        this._addStatusIcons();
        this._addTimestamps();
        return Promise.resolve();
    },

    _addStatusIcons: function() {
        this.$('.badge-warning').prepend('<i class="fa fa-clock-o me-1"></i>');
        this.$('.badge-success').prepend('<i class="fa fa-check-circle me-1"></i>');
        this.$('.badge-danger').prepend('<i class="fa fa-times-circle me-1"></i>');
    },

    _addTimestamps: function() {
        this.$('tr').each((index, row) => {
            const $row = $(row);
            const requestDate = $row.find('td:nth-child(3)').text();
            
            if (requestDate) {
                const date = new Date(requestDate);
                const now = new Date();
                const diffTime = Math.abs(now - date);
                const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
                const diffHours = Math.floor(diffTime / (1000 * 60 * 60));
                
                let timeAgo = '';
                if (diffDays > 0) {
                    timeAgo = `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
                } else if (diffHours > 0) {
                    timeAgo = `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
                } else {
                    timeAgo = 'Just now';
                }
                
                $row.find('td:nth-child(3)').append(`<br><small class="text-muted">${timeAgo}</small>`);
            }
        });
    },
});

// Smart notifications for portal users
publicWidget.registry.SmartNotifications = publicWidget.Widget.extend({
    selector: '.o_portal_my_doc_table, .extension-request-table',
    
    start: function() {
        this._super.apply(this, arguments);
        this._showSmartNotifications();
        return Promise.resolve();
    },

    _showSmartNotifications: function() {
        const overdueCount = this.$('.table-danger').length;
        const dueTodayCount = this.$('.table-warning').length;
        const pendingExtensions = this.$('.badge-warning').length;

        // Show overdue notification
        if (overdueCount > 0) {
            this._showNotification(
                'danger',
                `You have ${overdueCount} overdue book${overdueCount > 1 ? 's' : ''}. Please return them to avoid additional fines.`,
                'fa-exclamation-triangle'
            );
        }
        
        // Show due today notification
        else if (dueTodayCount > 0) {
            this._showNotification(
                'warning',
                `You have ${dueTodayCount} book${dueTodayCount > 1 ? 's' : ''} due today. Consider returning or requesting an extension.`,
                'fa-clock-o'
            );
        }

        // Show pending extensions notification
        if (pendingExtensions > 0) {
            this._showNotification(
                'info',
                `You have ${pendingExtensions} pending extension request${pendingExtensions > 1 ? 's' : ''}. We'll notify you once reviewed.`,
                'fa-hourglass-half'
            );
        }
    },

    _showNotification: function(type, message, icon) {
        const notification = `
            <div class="alert alert-${type} alert-dismissible fade show smart-notification" role="alert">
                <i class="fa ${icon} me-2"></i>
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `;
        
        this.$el.before(notification);
    },
});