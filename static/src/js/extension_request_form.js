/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { _t } from "@web/core/l10n/translation";

publicWidget.registry.ExtensionRequestForm = publicWidget.Widget.extend({
    selector: '#extension_request_form, form.s_website_form',
    events: {
        'submit': '_onSubmitForm',
        'change input[name="requested_expiry_date"]': '_onDateChange',
        'keyup textarea[name="request_reason"]': '_onReasonChange',
    },

    start: function() {
        this._super.apply(this, arguments);
        this._validateForm();
        this._initDateConstraints();
        return Promise.resolve();
    },

    _initDateConstraints: function() {
        const dateInput = this.$('input[name="requested_expiry_date"]');
        if (dateInput.length) {
            // Set minimum date to tomorrow
            const tomorrow = new Date();
            tomorrow.setDate(tomorrow.getDate() + 1);
            const minDate = tomorrow.toISOString().split('T')[0];
            dateInput.attr('min', minDate);

            // Set maximum date (30 days from current due date)
            const currentDueDate = new Date(dateInput.data('current-due-date') || minDate);
            const maxDate = new Date(currentDueDate);
            maxDate.setDate(maxDate.getDate() + 30);
            dateInput.attr('max', maxDate.toISOString().split('T')[0]);
        }
    },

    _onSubmitForm: function(ev) {
        ev.preventDefault();
        
        if (!this._validateForm()) {
            return false;
        }

        // Show loading state
        const submitBtn = this.$('button[type="submit"]');
        const originalText = submitBtn.html();
        submitBtn.prop('disabled', true).html('<i class="fa fa-spinner fa-spin"></i> Submitting...');

        // Submit form
        setTimeout(() => {
            ev.target.submit();
        }, 500);
    },

    _onDateChange: function(ev) {
        const selectedDate = new Date($(ev.currentTarget).val());
        const currentDueDate = new Date($(ev.currentTarget).data('current-due-date'));
        
        if (selectedDate && currentDueDate) {
            const diffTime = selectedDate - currentDueDate;
            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
            
            // Update extension days display
            const extensionDaysDisplay = this.$('.extension-days-display');
            if (extensionDaysDisplay.length) {
                extensionDaysDisplay.text(diffDays > 0 ? diffDays : 0);
            }
        }
        
        this._validateForm();
    },

    _onReasonChange: function(ev) {
        const textarea = $(ev.currentTarget);
        const maxLength = 500;
        const currentLength = textarea.val().length;
        
        // Update character count
        const charCount = this.$('.char-count');
        if (charCount.length) {
            charCount.text(`${currentLength}/${maxLength}`);
            charCount.toggleClass('text-danger', currentLength > maxLength);
        }
        
        this._validateForm();
    },

    _validateForm: function() {
        const errors = [];
        let isValid = true;

        // Clear previous errors
        this.$('.text-danger.error-message').remove();
        this.$('.is-invalid').removeClass('is-invalid');

        // Validate requested date
        const dateInput = this.$('input[name="requested_expiry_date"]');
        if (dateInput.length) {
            const selectedDate = new Date(dateInput.val());
            const currentDueDate = new Date(dateInput.data('current-due-date'));
            const today = new Date();
            today.setHours(0, 0, 0, 0);

            if (!dateInput.val()) {
                errors.push({field: dateInput, message: _t('New expiry date is required.')});
                isValid = false;
            } else if (selectedDate <= currentDueDate) {
                errors.push({field: dateInput, message: _t('New expiry date must be after current due date.')});
                isValid = false;
            } else if (selectedDate <= today) {
                errors.push({field: dateInput, message: _t('New expiry date must be in the future.')});
                isValid = false;
            } else {
                const diffTime = selectedDate - currentDueDate;
                const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
                if (diffDays > 30) {
                    errors.push({field: dateInput, message: _t('Extension cannot exceed 30 days.')});
                    isValid = false;
                }
            }
        }

        // Validate reason length
        const reasonTextarea = this.$('textarea[name="request_reason"]');
        if (reasonTextarea.length && reasonTextarea.val().length > 500) {
            errors.push({field: reasonTextarea, message: _t('Reason cannot exceed 500 characters.')});
            isValid = false;
        }

        // Display errors
        errors.forEach(error => {
            error.field.addClass('is-invalid');
            error.field.after(`<div class="text-danger error-message"><small>${error.message}</small></div>`);
        });

        // Enable/disable submit button
        const submitBtn = this.$('button[type="submit"]');
        submitBtn.prop('disabled', !isValid);

        return isValid;
    },
});

// Profile form validation
publicWidget.registry.ProfileForm = publicWidget.Widget.extend({
    selector: 'form.s_website_form[action*="profile"]',
    events: {
        'submit': '_onSubmitForm',
        'change input[name="email"]': '_onEmailChange',
        'change input[name="phone"]': '_onPhoneChange',
    },

    _onSubmitForm: function(ev) {
        if (!this._validateForm()) {
            ev.preventDefault();
            return false;
        }
        
        // Show loading state
        const submitBtn = this.$('button[type="submit"]');
        submitBtn.prop('disabled', true).html('<i class="fa fa-spinner fa-spin"></i> Updating...');
    },

    _onEmailChange: function(ev) {
        const email = $(ev.currentTarget).val();
        this._validateEmail(email);
    },

    _onPhoneChange: function(ev) {
        const phone = $(ev.currentTarget).val();
        this._validatePhone(phone);
    },

    _validateForm: function() {
        let isValid = true;
        
        // Clear previous errors
        this.$('.text-danger.error-message').remove();
        this.$('.is-invalid').removeClass('is-invalid');

        // Validate name
        const nameInput = this.$('input[name="name"]');
        if (nameInput.length && !nameInput.val().trim()) {
            this._showFieldError(nameInput, _t('Name is required.'));
            isValid = false;
        }

        // Validate email
        const emailInput = this.$('input[name="email"]');
        if (emailInput.length) {
            if (!emailInput.val().trim()) {
                this._showFieldError(emailInput, _t('Email is required.'));
                isValid = false;
            } else if (!this._validateEmail(emailInput.val())) {
                isValid = false;
            }
        }

        // Validate phone (if provided)
        const phoneInput = this.$('input[name="phone"]');
        if (phoneInput.length && phoneInput.val().trim()) {
            if (!this._validatePhone(phoneInput.val())) {
                isValid = false;
            }
        }

        return isValid;
    },

    _validateEmail: function(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        const emailInput = this.$('input[name="email"]');
        
        if (!emailRegex.test(email)) {
            this._showFieldError(emailInput, _t('Please enter a valid email address.'));
            return false;
        } else {
            this._clearFieldError(emailInput);
            return true;
        }
    },

    _validatePhone: function(phone) {
        const phoneRegex = /^(\+?6?0?)(\d{8,10})$/;
        const phoneInput = this.$('input[name="phone"]');
        const cleanPhone = phone.replace(/[-\s]/g, '');
        
        if (!phoneRegex.test(cleanPhone)) {
            this._showFieldError(phoneInput, _t('Please enter a valid phone number.'));
            return false;
        } else {
            this._clearFieldError(phoneInput);
            return true;
        }
    },

    _showFieldError: function(field, message) {
        field.addClass('is-invalid');
        field.next('.error-message').remove();
        field.after(`<div class="text-danger error-message"><small>${message}</small></div>`);
    },

    _clearFieldError: function(field) {
        field.removeClass('is-invalid');
        field.next('.error-message').remove();
    },
});

// Auto-refresh for pending requests
publicWidget.registry.AutoRefresh = publicWidget.Widget.extend({
    selector: '.auto-refresh-pending',
    
    start: function() {
        this._super.apply(this, arguments);
        if (this.$el.data('has-pending')) {
            this._startAutoRefresh();
        }
        return Promise.resolve();
    },

    _startAutoRefresh: function() {
        // Refresh every 30 seconds if there are pending requests
        setTimeout(() => {
            location.reload();
        }, 30000);
    },
});