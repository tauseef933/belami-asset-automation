# Belami Asset Template Automation Tool - Complete Setup Package

## What's Included

This package contains everything you need to deploy the Belami Asset Template Automation tool:

### Core Application Files
- **app.py** - Main Streamlit application (professional UI)
- **requirements.txt** - Python dependencies
- **.streamlit/config.toml** - Streamlit configuration for styling
- **gitignore.txt** - Git ignore file (rename to .gitignore when using)

### Data Files
- **Manufacturer_ID_s.xlsx** - Manufacturer ID mapping database
- **Asset_Template.xlsx** - Sample empty asset template

### Documentation
- **README.md** - Project overview and basic usage
- **DEPLOYMENT_GUIDE.md** - Complete deployment and user guide
- **VENDOR_FILE_FORMAT.md** - Vendor data file specifications

## Quick Deployment Steps

### Option 1: Streamlit Cloud (Recommended)

1. **Prepare GitHub Repository**
   ```
   1. Create new GitHub repository
   2. Upload all files from this package
   3. Rename gitignore.txt to .gitignore
   4. Create .streamlit folder and add config.toml inside it
   5. Commit and push
   ```

2. **Deploy to Streamlit Cloud**
   ```
   1. Go to https://share.streamlit.io
   2. Click "New app"
   3. Connect your GitHub repository
   4. Select: Main file = app.py
   5. Click "Deploy"
   ```

3. **Access Your App**
   ```
   Your app will be available at:
   https://[your-app-name].streamlit.app
   ```

### Option 2: Local Development/Testing

1. **Install Python Requirements**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application**
   ```bash
   streamlit run app.py
   ```

3. **Access Locally**
   ```
   Open browser to http://localhost:8501
   ```

## File Organization for Deployment

Your repository should look like this:

```
belami-asset-automation/
├── .streamlit/
│   └── config.toml
├── .gitignore
├── app.py
├── requirements.txt
├── Manufacturer_ID_s.xlsx
├── Asset_Template.xlsx
├── README.md
├── DEPLOYMENT_GUIDE.md
└── VENDOR_FILE_FORMAT.md
```

## First-Time Setup Checklist

- [ ] Create GitHub repository
- [ ] Upload all files to repository
- [ ] Verify Manufacturer_ID_s.xlsx is included
- [ ] Rename gitignore.txt to .gitignore
- [ ] Create .streamlit folder with config.toml
- [ ] Connect repository to Streamlit Cloud
- [ ] Deploy application
- [ ] Test with sample vendor file
- [ ] Share URL with team

## Using the Tool

### Step 1: Configure Vendor
1. Enter vendor name (e.g., "AFX", "Dainolite")
2. System auto-suggests manufacturer prefix
3. Verify brand folder name

### Step 2: Upload Files
1. Upload vendor data Excel file
2. Upload Asset Template Excel file

### Step 3: Process
1. Click "Generate Asset Template"
2. Review results and metrics
3. Check validation flags

### Step 4: Download
1. Download filled Asset Template
2. Download processing log

## Key Features

### Automatic Processing
- Extracts SKU and image data from vendor files
- Generates proper code/label combinations
- Creates correct image paths
- Assigns asset family types
- Determines media types

### Validation & Quality Control
- Checks for main product images
- Detects duplicate filenames
- Logs skipped video files
- Flags uncertain media type assignments

### Professional UI
- Clean, corporate design
- No emojis or AI-like elements
- Clear status indicators
- Organized layout
- Proper error handling

## Important Rules (Built Into Tool)

The tool automatically enforces these Belami rules:

1. **Code and Label**: Always identical and lowercase
2. **Filenames**: Clean, lowercase, proper suffixes
3. **Asset Families**: Correct classification
4. **Image Paths**: Proper folder structure
5. **No Videos**: Automatically skipped
6. **No Empty Columns**: All 6 columns filled

## Troubleshooting

### Common Issues

**Tool won't load**
- Check requirements.txt is present
- Verify Python version is 3.8+
- Check Streamlit Cloud logs

**Manufacturer prefix not found**
- Manually enter the prefix
- Update Manufacturer_ID_s.xlsx if needed

**No images processed**
- Verify vendor file has image columns
- Check column names contain "image", "photo", or "url"
- Review VENDOR_FILE_FORMAT.md

**Wrong brand folder**
- Manually edit in sidebar
- Use lowercase, no spaces

## Support & Documentation

- **README.md** - Quick overview
- **DEPLOYMENT_GUIDE.md** - Detailed deployment steps and user guide
- **VENDOR_FILE_FORMAT.md** - Vendor file requirements and examples

## Updates & Maintenance

### Adding New Manufacturers
1. Edit Manufacturer_ID_s.xlsx
2. Add new row with Brand name and Manu ID
3. Upload to repository
4. App will auto-update mapping

### Modifying Processing Rules
1. Edit app.py
2. Test locally first
3. Push changes to GitHub
4. Streamlit Cloud auto-redeploys

## Security & Best Practices

- Keep repository private if handling sensitive data
- Only share app URL with authorized users
- Follow company data handling policies
- Keep processing logs for audit trail
- Review validation flags before finalizing

## Version Information

**Version**: 1.0  
**Release Date**: January 2026  
**Compatibility**: Python 3.8+, Streamlit 1.31+

## Questions?

1. Check the documentation files first
2. Review validation flags in processing logs
3. Test with sample data locally
4. Contact your development team

---

**Ready to deploy?** Follow the Quick Deployment Steps above to get started!
