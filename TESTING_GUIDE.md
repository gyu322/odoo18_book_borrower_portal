# Extension Request System - Complete Testing Guide

## 🎯 Overview
This guide provides comprehensive testing steps to verify that the extension request functionality is working correctly in the Book Borrower Portal.

---

## ⚠️ Prerequisites

### 1. Module Status Check
**Ensure the module is properly installed:**
1. Go to **Apps** in Odoo
2. Search for "Book Borrower Portal"
3. Status should be "Installed" (green)
4. If not, click **Install** or **Upgrade**

### 2. User Access Verification
**Check your user has proper access:**
1. Go to **Settings → Users & Companies → Users**
2. Find your user account
3. Verify you have **Internal User** or **Administrator** access
4. Check **Groups** tab includes relevant permissions

---

## 📋 Test Data Setup

### Step 1: Create Test Data (if not exists)

#### **A. Create Library Members**
1. Go to **Library Management 01 → Members**
2. Create at least 2 test members:
   ```
   Member 1:
   - Name: Test Portal User
   - Email: portal@test.com
   - Phone: 123-456-7890
   - Member Status: Active
   
   Member 2:
   - Name: Admin Test User  
   - Email: admin@test.com
   - Phone: 098-765-4321
   - Member Status: Active
   ```

#### **B. Create Test Books**
1. Go to **Library Management 01 → Books**
2. Create test books:
   ```
   Book 1:
   - Title: "Test Book for Extension"
   - Author: "Test Author"
   - ISBN: "978-0000000001"
   - Available Copies: 5
   
   Book 2:
   - Title: "Second Test Book"
   - Author: "Another Author" 
   - ISBN: "978-0000000002"
   - Available Copies: 3
   ```

#### **C. Create Borrowing Records**
1. Go to **Library Management 01 → Borrowing Records**
2. Create test borrowing records:
   ```
   Record 1:
   - Member: Test Portal User
   - Book: Test Book for Extension
   - Borrow Date: Today
   - Expected Return Date: Today + 14 days
   - Status: Borrowed
   ```

---

## 🧪 Core Functionality Tests

### Test 1: Portal Access & Member Creation
**Objective**: Verify portal users can access and create member accounts

#### **Steps:**
1. **Create Portal User Account:**
   - Go to **Settings → Users & Companies → Users**
   - Click **Create**
   - Fill in:
     ```
     Name: Portal Test User
     Email: portal@test.com
     Password: test123
     User Type: Portal User
     ```
   - Save the user

2. **Test Portal Access:**
   - Open incognito/private browser window
   - Go to your Odoo URL (e.g., `http://localhost:8069`)
   - Login with portal credentials (`portal@test.com` / `test123`)

3. **Test Member Auto-Creation:**
   - After login, you should see portal dashboard
   - Click **"Register as Member"** if prompted
   - Or go to `/my/create-member`
   - Verify member account is created automatically

**✅ Expected Results:**
- Portal user can login successfully
- Member account is created with portal user details
- Portal dashboard shows library-related cards

---

### Test 2: Borrowed Books List
**Objective**: Verify borrowed books are displayed correctly

#### **Steps:**
1. **Access Borrowed Books:**
   - In portal, click **"My Borrowed Books"** card
   - Or navigate to `/my/borrowed-books`

2. **Test List Functionality:**
   - Verify borrowed books are displayed
   - Test **Filter** dropdown (All Books, Currently Borrowed, Overdue, Returned)
   - Test **Sort** dropdown (Record Number, Borrow Date, Due Date, Book Title)
   - Test **Search** by book title
   - Test **Pagination** if more than 20 records

3. **Test Book Details:**
   - Click on a book title
   - Should navigate to `/my/borrowed-books/<record_id>`
   - Verify book details are displayed correctly

**✅ Expected Results:**
- Books list displays with proper filtering and sorting
- Search functionality works
- Book detail pages load correctly
- Status badges show correct colors (Borrowed=blue, Overdue=red, Returned=green)

---

### Test 3: Extension Request Creation
**Objective**: Test the core extension request functionality

#### **Steps:**
1. **Navigate to Book Details:**
   - Go to **My Borrowed Books**
   - Click on an active borrowed book
   - Should see book details page

2. **Request Extension:**
   - Look for **"Request Extension"** button
   - If button is not visible, check:
     - Book status is "Borrowed"
     - Book is not overdue
   - Click **"Request Extension"** button

3. **Fill Extension Request Form:**
   - Should navigate to `/my/borrowed-books/<id>/request-extension`
   - Form should show:
     ```
     - Book information
     - Current due date
     - Requested new due date (auto-filled +14 days)
     - Reason field (optional)
     ```

4. **Submit Request:**
   - Optionally enter a reason
   - Click **"Submit Extension Request"**
   - Should show success message

**✅ Expected Results:**
- Extension request form loads correctly
- Default dates are calculated properly
- Request submission succeeds
- Success/error messages are displayed

---

### Test 4: Extension Request Tracking
**Objective**: Verify users can track their extension requests

#### **Steps:**
1. **Access Extension Requests List:**
   - In portal, click **"Extension Requests"** card
   - Or navigate to `/my/extension-requests`

2. **Test List Features:**
   - Verify submitted requests are displayed
   - Test **Filter** by status (All, Pending, Approved, Rejected)
   - Test **Sort** options (Request Date, Status, Book Title)
   - Check status badges are colored correctly:
     - **Pending**: Yellow/Warning
     - **Approved**: Green/Success  
     - **Rejected**: Red/Danger

3. **Test Request Details:**
   - Click on a request to view details (if detail view exists)
   - Verify all request information is displayed

**✅ Expected Results:**
- Extension requests list displays correctly
- Filter and sort functionality works
- Status badges show appropriate colors
- Request details are accessible

---

### Test 5: Backend Administration
**Objective**: Test librarian/admin workflow for managing requests

#### **Steps:**
1. **Access Backend Extension Requests:**
   - Login as Administrator
   - Go to **Library Management 01 → Extension Requests**
   - Should see list of all extension requests

2. **Test Request Approval:**
   - Open a pending request in form view
   - Click **"Approve"** button
   - Verify:
     - Status changes to "Approved"
     - Review date is set
     - Borrowing record due date is updated

3. **Test Request Rejection:**
   - Open another pending request
   - Click **"Reject"** button
   - Enter rejection reason
   - Verify status changes to "Rejected"

4. **Check Email Notifications** (if configured):
   - Verify emails are sent to members on status changes
   - Check email templates are working

**✅ Expected Results:**
- Admin can view all extension requests
- Approval workflow works correctly
- Rejection workflow works with reason capture
- Borrowing record dates are updated on approval

---

## 🔍 Edge Cases & Error Testing

### Test 6: Extension Request Validation
**Objective**: Test business logic and validation rules

#### **Steps:**
1. **Test Eligibility Rules:**
   - Try requesting extension for:
     - ❌ **Overdue book** - should be blocked
     - ❌ **Returned book** - should be blocked  
     - ❌ **Book with pending request** - should be blocked
   - Verify appropriate error messages

2. **Test Date Validation:**
   - Try submitting extension with:
     - ❌ **Past date** - should be rejected
     - ❌ **Same due date** - should be rejected
     - ❌ **Too far in future** - should be limited

3. **Test Multiple Requests:**
   - Try creating multiple extension requests for same book
   - Should prevent duplicate pending requests

**✅ Expected Results:**
- Validation rules prevent invalid requests
- Clear error messages guide users
- System prevents business rule violations

---

### Test 7: Security & Access Control
**Objective**: Verify security measures are working

#### **Steps:**
1. **Test Portal User Restrictions:**
   - Portal users should only see their own:
     - Borrowed books
     - Extension requests
   - Should NOT access other users' data

2. **Test URL Access Control:**
   - Try accessing other user's book details:
     - `/my/borrowed-books/<other_user_record_id>`
   - Should get "Not Found" or "Access Denied"

3. **Test Backend Access:**
   - Portal users should NOT access:
     - Backend extension request management
     - Other users' records in backend

**✅ Expected Results:**
- Users only access their own data
- URL manipulation is blocked
- Proper security boundaries enforced

---

## 📊 Performance & UI Testing

### Test 8: User Experience
**Objective**: Verify the interface is user-friendly

#### **Steps:**
1. **Test Responsive Design:**
   - Access portal on different screen sizes
   - Check mobile responsiveness
   - Verify tables are scrollable on small screens

2. **Test Navigation:**
   - Verify breadcrumbs work correctly
   - Check "Back" buttons function properly
   - Test menu navigation flow

3. **Test Error Handling:**
   - Test with invalid data
   - Check error messages are helpful
   - Verify system gracefully handles failures

**✅ Expected Results:**
- Interface is mobile-friendly
- Navigation is intuitive
- Error messages are clear and helpful

---

## 🐛 Troubleshooting Common Issues

### Issue 1: "Template not found" Errors
**Solution:**
1. Upgrade the module: **Apps → Book Borrower Portal → Upgrade**
2. Clear browser cache
3. Check all XML files are properly loaded

### Issue 2: "Access Denied" Errors  
**Solution:**
1. Verify user has proper permissions
2. Check security rules in `ir.model.access.csv`
3. Ensure user belongs to correct groups

### Issue 3: Extension Request Not Saving
**Solution:**
1. Check database constraints
2. Verify model dependencies are loaded
3. Check server logs for validation errors

### Issue 4: Dates Not Calculating Correctly
**Solution:**
1. Check system configuration parameters
2. Verify timezone settings
3. Test with different date ranges

---

## ✅ Final Verification Checklist

**Portal User Experience:**
- [ ] Can login to portal successfully
- [ ] Can create/view member profile
- [ ] Can view borrowed books list with filters
- [ ] Can access book details
- [ ] Can submit extension requests
- [ ] Can track extension request status
- [ ] Receives appropriate error messages
- [ ] Interface is responsive and user-friendly

**Admin/Librarian Experience:**
- [ ] Can view all extension requests
- [ ] Can approve/reject requests
- [ ] Extension approval updates borrowing records
- [ ] Email notifications work (if configured)
- [ ] Proper access controls enforced

**System Functionality:**
- [ ] All templates render without errors
- [ ] Business rules enforced correctly
- [ ] Data validation works properly
- [ ] Security measures prevent unauthorized access
- [ ] Performance is acceptable

---

## 📞 Support

**If any tests fail:**
1. Check the error message details
2. Review server logs for additional information
3. Refer to `DEVELOPMENT_LOG.md` for known issues and solutions
4. Verify module dependencies are properly installed

**Module Status**: Ready for Production Use ✅  
**Last Tested**: 2025-11-11  
**Test Environment**: Odoo 18.0