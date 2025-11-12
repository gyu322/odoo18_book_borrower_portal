# Installation Guide

## Quick Start

### Prerequisites Checklist
- [ ] Odoo 18.0 running
- [ ] Access to Odoo Apps management
- [ ] Git installed
- [ ] Admin access to Odoo

### 🔄 Step-by-Step Installation

#### 1. Install Base Library Management System

```bash
# Navigate to your Odoo addons directory
cd /path/to/your/odoo/addons

# Clone the base module
git clone https://github.com/your-username/library_management_1.git

# Restart Odoo
sudo systemctl restart odoo
# OR for development
./odoo-bin -d your_database --addons-path /path/to/addons
```

**In Odoo Interface:**
1. Go to **Apps**
2. Click **Update Apps List**
3. Search for **"Library Management System"**
4. Click **Install**
5. ✅ Wait for installation to complete

#### 2. Install Book Borrower Portal

```bash
# In the same addons directory
git clone https://github.com/your-username/book_borrower_portal.git

# Restart Odoo again
sudo systemctl restart odoo
```

**In Odoo Interface:**
1. Go to **Apps**
2. Click **Update Apps List**
3. Remove the "Apps" filter to see all modules
4. Search for **"Book Borrower Portal"**
5. Click **Install**
6. ✅ Wait for installation to complete

#### 3. Initial Configuration

**Create a Librarian:**
1. Go to **Library → Configuration → Librarians**
2. Click **Create**
3. Fill in librarian details
4. Save

**Create Test Data (Optional):**
1. Go to **Library → Books** → Add some books
2. Go to **Library → Members** → Add some members
3. Create a few borrowing records for testing

**Enable Portal Access:**
1. Go to **Library → Members**
2. Select a member
3. Click **"Create Portal User"** button
4. Member will receive login email

#### 4. Test Portal Access

1. Open new browser window/incognito mode
2. Go to `your-odoo-url/my`
3. Login with member credentials
4. Should see "My Borrowed Books" menu
5. ✅ Test extension request functionality

## ⚠️ Troubleshooting

### Installation Issues

**"Module library_management_1 not found"**
```bash
# Check if base module is in addons path
ls /path/to/addons/library_management_1

# If not found, clone it first:
git clone https://github.com/your-username/library_management_1.git
```

**"Dependencies not satisfied"**
```bash
# Check if portal and mail modules are installed
# Usually these come with Odoo by default
```

**"Access denied" errors**
```bash
# Make sure you have admin privileges
# Check if modules are in the correct addons path
# Restart Odoo after adding modules
```

### Runtime Issues

**Portal user creation fails**
- ✅ Check member has valid email
- ✅ Check email is not already used
- ✅ Check user permissions

**Extension requests not working**
- ✅ Book must be currently borrowed
- ✅ Not overdue
- ✅ Within extension limits

## 🔧 Configuration Options

### System Parameters
Go to **Settings → Technical → Parameters → System Parameters**

| Parameter | Default | Description |
|-----------|---------|-------------|
| `book_borrower_portal.max_extensions` | 2 | Maximum extensions per book |
| `book_borrower_portal.max_extension_days` | 14 | Maximum days per extension |
| `book_borrower_portal.min_days_before_expiry` | 3 | Minimum days before expiry to request |

### Email Templates
Configure in **Settings → Technical → Email → Templates**
- Extension Request Submitted
- Extension Request Approved  
- Extension Request Rejected

## 🏗 Development Setup

For development environment:

```bash
# Clone both modules to development addons path
cd /path/to/dev/addons
git clone https://github.com/your-username/library_management_1.git
git clone https://github.com/your-username/book_borrower_portal.git

# Run Odoo in development mode
./odoo-bin -d dev_database --addons-path /path/to/dev/addons --dev all
```

## 🔄 Updating

### Update Base Module
```bash
cd library_management_1
git pull origin main
# Restart Odoo and upgrade module in Apps
```

### Update Portal Module  
```bash
cd book_borrower_portal
git pull origin main
# Restart Odoo and upgrade module in Apps
```

## ✅ Verification

After installation, verify these features work:

### Backend (Admin)
- [ ] Library menu appears
- [ ] Can create books, members, librarians
- [ ] Borrowing workflow works
- [ ] Extension requests appear in menu

### Portal (Member)
- [ ] Can login to /my
- [ ] "My Borrowed Books" menu visible
- [ ] Can view borrowed books
- [ ] Can request extensions (if eligible)
- [ ] Can view request status

### Email Notifications
- [ ] Extension request emails sent
- [ ] Approval/rejection emails sent
- [ ] Member portal creation emails sent

## 🆘 Getting Help

If you encounter issues:

1. **Check Logs**: Look at Odoo server logs for error messages
2. **Debug Mode**: Add `?debug=1` to URL for more details  
3. **GitHub Issues**: [Report bugs here](https://github.com/your-username/book_borrower_portal/issues)
4. **Community**: Ask on Odoo Community forums

## 📋 Uninstallation

To remove the modules:

1. **Uninstall Portal Module first**:
   - Apps → Book Borrower Portal → Uninstall

2. **Uninstall Base Module**:
   - Apps → Library Management System → Uninstall

3. **Remove files**:
   ```bash
   rm -rf book_borrower_portal
   rm -rf library_management_1
   ```