# Belami Asset Template Automation - Deployment Guide

## Quick Start for Streamlit Cloud

### Step 1: Prepare Your Repository

1. Create a new GitHub repository
2. Upload these files to your repository:
   - `app.py` (main application)
   - `requirements.txt` (dependencies)
   - `Manufacturer_ID_s.xlsx` (manufacturer mapping)
   - `.streamlit/config.toml` (configuration)
   - `README.md` (documentation)

### Step 2: Deploy to Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click "New app"
3. Connect your GitHub account (if not already connected)
4. Select your repository
5. Set the following:
   - **Main file path**: `app.py`
   - **Python version**: 3.9 or higher
6. Click "Deploy"

### Step 3: Initial Setup

Once deployed, the app will be accessible via a URL like:
`https://your-app-name.streamlit.app`

## User Guide

### Getting Started

1. **Open the Application**
   - Navigate to your deployed Streamlit app URL
   - You'll see the main interface with sidebar configuration

2. **Configure Vendor Information** (Left Sidebar)
   - Enter the vendor name (e.g., "AFX", "Dainolite", "Hinkley")
   - The system will automatically suggest the manufacturer prefix if found
   - Verify or manually enter the manufacturer prefix
   - The brand folder name is auto-filled (lowercase brand name)

3. **Upload Files** (Main Area)
   - **Vendor Data File**: Upload the Excel file from your vendor
     - Common sheet names: "Entities", "All", or "Sheet1"
     - Must contain SKU and image columns
   - **Asset Template**: Upload the empty Asset Template Excel file
     - This should be the standard "Asset Template.xlsx" file

4. **Process the Data**
   - Verify all status indicators show green checkmarks
   - Click "Generate Asset Template" button
   - Wait for processing to complete (usually 5-30 seconds)

5. **Review Results**
   - Check summary metrics (Total Assets, Main Images, Media Images, PDFs)
   - Review the data preview table
   - Read any validation flags or warnings

6. **Download Outputs**
   - Click "Download Filled Asset Template" to get the Excel file
   - Click "Download Processing Log" to get the validation report

### Understanding the Output

#### Excel File Structure
The output Excel file contains 6 columns:
- **code**: Lowercase identifier (manufacturerprefix_filename_new_1k)
- **label-en_US**: Identical to code (required by Belami)
- **product_reference**: Full SKU with manufacturer prefix
- **imagelink**: Path to the asset file (lowercase)
- **assetFamilyIdentifier**: Asset type (main_product_image, media, spec_sheet, install_sheet)
- **mediatype**: Type of media (for media assets only)

#### Processing Log
The log file includes:
- Processing timestamp
- Total assets processed
- Validation flags and warnings
- Any issues detected (missing main images, duplicate filenames, etc.)

### Common Issues and Solutions

#### Issue: "No image columns found in vendor file"
**Solution**: Verify your vendor file has columns with names containing "image", "photo", or "url"

#### Issue: "No SKU columns found in vendor file"
**Solution**: Verify your vendor file has columns with names containing "sku", "item", or "product"

#### Issue: "No main product images found" warning
**Solution**: Ensure your vendor file has at least one image per product. The first image becomes the main product image.

#### Issue: Manufacturer prefix not found
**Solution**: Manually enter the manufacturer prefix. If this vendor is new, you may need to update the Manufacturer_ID_s.xlsx file.

#### Issue: Wrong brand folder name
**Solution**: Manually edit the brand folder field in the sidebar. Use lowercase, no spaces (e.g., "hudsonvalley" not "Hudson Valley")

### Advanced Tips

#### Multiple Images per Product
- The first image for each SKU becomes the main_product_image
- All subsequent images are classified as "media"
- PDFs are automatically classified as spec_sheet or install_sheet

#### Custom Media Type Assignment
The system automatically determines media types based on filename keywords:
- Files with "lifestyle", "room", "environment" → lifestyle
- Files with "dimension", "measurement", "drawing" → dimension
- Files with "detail", "closeup", "zoom" → detail
- Files with "angle", "view", "perspective" → angle
- Files with "swatch", "color", "finish" → swatch
- Files with "chart", "info", "callout" → informational
- Default → detail

#### Video Files
- Video files are automatically skipped
- A flag is logged for each skipped video
- YouTube links are handled separately (not included in asset template)

### Best Practices

1. **Data Preparation**
   - Clean your vendor file before upload
   - Ensure SKUs are properly formatted
   - Verify image URLs or filenames are complete

2. **Review Before Processing**
   - Check vendor name spelling matches manufacturer database
   - Verify manufacturer prefix is correct
   - Confirm brand folder name follows naming conventions

3. **Quality Control**
   - Always review the data preview before downloading
   - Check validation flags for warnings
   - Verify main product images were detected
   - Spot-check a few rows in the output file

4. **File Management**
   - Save output files with descriptive names
   - Keep processing logs for audit trail
   - Archive vendor source files with corresponding outputs

## Troubleshooting

### Application Won't Load
- Check that all required files are in the repository
- Verify requirements.txt has correct dependencies
- Check Streamlit Cloud logs for error messages

### Processing Errors
- Verify Excel files are not corrupted
- Ensure files are in .xlsx format (not .xls or .csv)
- Check that files contain expected sheet names

### Output Quality Issues
- Review vendor file structure
- Verify column names match expected patterns
- Check for special characters in filenames

## Maintenance

### Updating Manufacturer Mapping
1. Edit the Manufacturer_ID_s.xlsx file
2. Add new brands/manufacturers as needed
3. Push updated file to GitHub
4. Redeploy the app (or it will auto-update)

### Application Updates
1. Modify app.py as needed
2. Test locally using `streamlit run app.py`
3. Push changes to GitHub
4. Streamlit Cloud will auto-redeploy

## Support

For technical support or feature requests:
1. Check this guide and README.md first
2. Review validation flags in processing logs
3. Contact your development team
4. Submit issues via GitHub (if applicable)

## Security Notes

- Do not share the application URL publicly
- Only upload vendor files you have permission to process
- Processed files may contain sensitive product information
- Follow your company's data handling policies

## Version History

- **v1.0** - Initial release with core functionality
  - Automatic template filling
  - Manufacturer mapping
  - Validation and logging
  - Professional UI
