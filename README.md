# Belami Asset Template Automation Tool

A professional Streamlit application that automates the process of filling Belami Asset Templates with vendor data according to strict Belami Asset Master Instructions.

## Features

- **Automatic Template Filling**: Processes vendor Excel files and generates properly formatted Asset Templates
- **Manufacturer Mapping**: Built-in manufacturer ID lookup from your reference file
- **Validation & Logging**: Generates detailed processing logs with warnings and flags
- **Professional UI**: Clean, corporate interface suitable for US employee use
- **Strict Compliance**: Follows all Belami Asset Master Instructions rules:
  - Lowercase code and label-en_US (identical values)
  - Proper image path construction
  - Correct asset family identification
  - Automatic mediatype determination
  - Video file exclusion
  - No empty columns in output

## Installation

### Local Setup

1. Install Python 3.8 or higher
2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Add the manufacturer mapping file (`Manufacturer_ID_s.xlsx`) to the root directory

4. Run the application:
```bash
streamlit run app.py
```

### Streamlit Cloud Deployment

1. Push this repository to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repository
4. Set main file path to `app.py`
5. Upload `Manufacturer_ID_s.xlsx` to the deployed app directory or include it in the repo
6. Deploy

## Usage

1. **Configure Vendor Information**:
   - Enter vendor name (e.g., "AFX", "Dainolite")
   - System will auto-suggest manufacturer prefix if found in mapping
   - Confirm or manually enter manufacturer prefix
   - Brand folder name is auto-filled (can be edited)

2. **Upload Files**:
   - Upload vendor data file (Excel with product data)
   - Upload empty Asset Template (Asset Template.xlsx)

3. **Process**:
   - Click "Generate Asset Template" button
   - Review summary metrics and preview data
   - Check validation flags for any warnings

4. **Download Results**:
   - Download filled Asset Template Excel file
   - Download processing log (text file with validation flags)

## File Structure

```
.
├── app.py                      # Main Streamlit application
├── requirements.txt            # Python dependencies
├── Manufacturer_ID_s.xlsx      # Manufacturer ID mapping (required)
└── README.md                   # This file
```

## Processing Rules

### File Naming
- **Images**: `manufacturerprefix_filename_new_1k` (all lowercase)
- **PDFs**: `manufacturerprefix_filename_specs` (all lowercase)

### Asset Family Types
- `main_product_image`: First image (white background, full product view)
- `media`: Additional product images
- `spec_sheet`: Specification PDFs
- `install_sheet`: Installation instruction PDFs

### Media Types (for media assets)
- `lifestyle`: Product in environment/room
- `dimension`: Measurements, drawings, diagrams
- `detail`: Close-up views (default if unclear)
- `angle`: Alternate viewing angles
- `informational`: Charts, callouts, infographics
- `swatch`: Color/finish swatches

### Image Link Paths
- Main images: `brand/products/filename_new_1k.jpg`
- Media images: `brand/media/filename_new_1k.jpg`
- PDFs: `brand/specsheets/filename_new.pdf`

## Important Notes

- All paths and filenames are converted to lowercase
- Video files are automatically skipped
- Each row represents one real asset (image or PDF)
- No empty columns in generated rows
- Code and label-en_US are always identical
- Product reference includes manufacturer prefix

## Validation & Quality Checks

The tool performs the following checks:
- Verifies at least one main product image exists
- Detects duplicate filenames
- Logs skipped video files
- Flags uncertain mediatype assignments

## Support

For questions or issues, please contact the development team or submit an issue in the repository.

## Version

Version 1.0 - Initial Release
