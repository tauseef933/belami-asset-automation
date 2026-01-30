# Streamlit Cloud Deployment Checklist

Use this checklist to ensure proper deployment of the Belami Asset Template Automation tool.

## Pre-Deployment Setup

### 1. Repository Setup
- [ ] Create new GitHub repository (public or private)
- [ ] Name it appropriately (e.g., "belami-asset-automation")
- [ ] Initialize with README (optional, we have our own)

### 2. File Upload to GitHub
- [ ] Upload **app.py**
- [ ] Upload **requirements.txt**
- [ ] Upload **Manufacturer_ID_s.xlsx**
- [ ] Upload **Asset_Template.xlsx** (optional, for reference)
- [ ] Upload **README.md**
- [ ] Upload **DEPLOYMENT_GUIDE.md**
- [ ] Upload **VENDOR_FILE_FORMAT.md**
- [ ] Upload **SETUP_INSTRUCTIONS.md**

### 3. Create Folder Structure
- [ ] Create **.streamlit** folder in repository
- [ ] Upload **config.toml** into .streamlit folder
- [ ] Create **.gitignore** file (rename gitignore.txt)

### 4. Verify Repository Structure
Your repository should look like this:
```
your-repo/
├── .streamlit/
│   └── config.toml
├── .gitignore
├── app.py
├── requirements.txt
├── Manufacturer_ID_s.xlsx
├── Asset_Template.xlsx
├── README.md
├── DEPLOYMENT_GUIDE.md
├── VENDOR_FILE_FORMAT.md
└── SETUP_INSTRUCTIONS.md
```

## Streamlit Cloud Deployment

### 5. Access Streamlit Cloud
- [ ] Go to https://share.streamlit.io
- [ ] Sign in with GitHub account
- [ ] Authorize Streamlit to access your repositories

### 6. Create New App
- [ ] Click "New app" button
- [ ] Select deployment method: "From existing repo"

### 7. Configure Deployment
- [ ] **Repository**: Select your GitHub repository
- [ ] **Branch**: main (or master)
- [ ] **Main file path**: app.py
- [ ] **Python version**: 3.9 or 3.10 (recommended)

### 8. Advanced Settings (Optional)
- [ ] Set custom app URL (if available)
- [ ] Configure secrets (if needed - not required for this app)

### 9. Deploy
- [ ] Click "Deploy!" button
- [ ] Wait for deployment (usually 2-5 minutes)
- [ ] Watch build logs for any errors

## Post-Deployment Verification

### 10. Initial Testing
- [ ] App loads successfully
- [ ] UI displays correctly (no layout issues)
- [ ] Sidebar configuration visible
- [ ] File upload areas present

### 11. Functionality Testing
- [ ] Enter vendor name (test with "AFX")
- [ ] Verify manufacturer prefix auto-fills (should show "2605")
- [ ] Upload a test vendor file
- [ ] Upload Asset Template file
- [ ] Click "Generate Asset Template"
- [ ] Verify processing completes
- [ ] Check data preview displays
- [ ] Download filled template
- [ ] Download processing log
- [ ] Open downloaded files to verify content

### 12. Manufacturer Mapping Test
- [ ] Test with known vendor (e.g., AFX, Dainolite)
- [ ] Verify prefix auto-suggests correctly
- [ ] Test with unknown vendor
- [ ] Verify manual entry works

### 13. Error Handling Test
- [ ] Try uploading wrong file type
- [ ] Try processing without all fields filled
- [ ] Verify error messages display properly
- [ ] Check that app doesn't crash

## Documentation Review

### 14. Documentation Accessibility
- [ ] README.md displays on GitHub repo home
- [ ] All .md files are readable
- [ ] Links in documentation work
- [ ] Examples are clear

### 15. User Access
- [ ] Share app URL with test users
- [ ] Verify they can access without issues
- [ ] Collect initial feedback
- [ ] Make any necessary adjustments

## Maintenance Setup

### 16. Update Process
- [ ] Document how to update Manufacturer_ID_s.xlsx
- [ ] Test updating a file and redeploying
- [ ] Verify auto-redeploy works
- [ ] Document rollback process (if needed)

### 17. Monitoring
- [ ] Bookmark Streamlit Cloud dashboard
- [ ] Check app analytics (if enabled)
- [ ] Monitor for error reports
- [ ] Set up notifications for downtime (if needed)

## Security & Access

### 18. Access Control
- [ ] Determine who needs access
- [ ] Share app URL with authorized users only
- [ ] Document access policy
- [ ] Keep repository private (if handling sensitive data)

### 19. Data Security
- [ ] Verify no sensitive data in repository
- [ ] Check that uploaded files are not stored permanently
- [ ] Review Streamlit Cloud security policies
- [ ] Document data handling procedures

## Final Steps

### 20. Team Onboarding
- [ ] Send app URL to team
- [ ] Share DEPLOYMENT_GUIDE.md
- [ ] Share VENDOR_FILE_FORMAT.md
- [ ] Provide quick start tutorial
- [ ] Schedule training session (if needed)

### 21. Documentation
- [ ] Save deployment date and URL
- [ ] Document any custom configuration
- [ ] Create internal wiki/docs (if applicable)
- [ ] Set up support channel

### 22. Backup
- [ ] Export working version of app
- [ ] Save local copy of all files
- [ ] Document version number
- [ ] Create backup of Manufacturer_ID_s.xlsx

## Troubleshooting Checklist

If deployment fails, check:
- [ ] All files are in correct locations
- [ ] requirements.txt has no typos
- [ ] Python version is compatible
- [ ] No file size limits exceeded
- [ ] GitHub repository is accessible
- [ ] Streamlit Cloud account has no issues

If app runs but has errors:
- [ ] Check Streamlit Cloud logs
- [ ] Verify file paths in code
- [ ] Test with different vendor files
- [ ] Review error messages carefully
- [ ] Test locally if needed

## Success Criteria

Your deployment is successful when:
- ✓ App loads without errors
- ✓ All UI elements display correctly
- ✓ File upload works
- ✓ Processing completes successfully
- ✓ Output files download correctly
- ✓ Validation logs are accurate
- ✓ Users can access and use the app
- ✓ Documentation is clear and accessible

## Contact Information

**For Technical Issues:**
- Check Streamlit Cloud status page
- Review app logs in dashboard
- Consult Streamlit documentation

**For Application Issues:**
- Review validation flags
- Check vendor file format
- Consult VENDOR_FILE_FORMAT.md
- Contact development team

---

**Deployment Date**: _______________

**Deployed By**: _______________

**App URL**: _______________

**Version**: 1.0

**Status**: [ ] In Progress  [ ] Completed  [ ] Verified

---

**Notes:**

_________________________________________________

_________________________________________________

_________________________________________________
