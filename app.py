import streamlit as st
import pandas as pd
import openpyxl
from openpyxl import load_workbook, Workbook
from openpyxl.styles import Font, PatternFill, Alignment
import re
import io
from datetime import datetime
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="Belami Asset Template Automation",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 600;
        color: #1f2937;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #6b7280;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.3rem;
        font-weight: 600;
        color: #374151;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #e5e7eb;
        padding-bottom: 0.5rem;
    }
    .info-box {
        background-color: #f3f4f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #3b82f6;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #d1fae5;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #10b981;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fef3c7;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #f59e0b;
        margin: 1rem 0;
    }
    .stButton>button {
        width: 100%;
        background-color: #3b82f6;
        color: white;
        font-weight: 500;
        padding: 0.5rem 1rem;
        border-radius: 0.375rem;
        border: none;
    }
    .stButton>button:hover {
        background-color: #2563eb;
    }
    </style>
    """, unsafe_allow_html=True)

# Load manufacturer mapping
@st.cache_data
def load_manufacturer_mapping():
    """Load manufacturer ID mapping from uploaded file"""
    try:
        df = pd.read_excel('Manufacturer_ID_s.xlsx')
        # Create mapping dictionary (brand name -> ID)
        mapping = dict(zip(df['Brand'].str.lower().str.strip(), df['Manu ID'].astype(str)))
        return mapping, df
    except Exception as e:
        st.error(f"Error loading manufacturer mapping: {e}")
        return {}, pd.DataFrame()

def clean_filename(filename):
    """Clean filename according to Belami rules"""
    # Remove extension
    name = Path(filename).stem
    # Replace spaces, commas, slashes, special chars with underscore
    name = re.sub(r'[,\s/\\]+', '_', name)
    # Remove other special characters except underscore and hyphen
    name = re.sub(r'[^a-zA-Z0-9_-]', '', name)
    # Make lowercase
    name = name.lower()
    return name

def determine_mediatype(filename, row_data):
    """Determine mediatype based on filename and context"""
    filename_lower = filename.lower()
    
    # Keywords for different media types
    if any(word in filename_lower for word in ['lifestyle', 'room', 'environment', 'scene']):
        return 'lifestyle'
    elif any(word in filename_lower for word in ['dimension', 'measurement', 'drawing', 'diagram']):
        return 'dimension'
    elif any(word in filename_lower for word in ['detail', 'closeup', 'close-up', 'zoom']):
        return 'detail'
    elif any(word in filename_lower for word in ['angle', 'view', 'perspective']):
        return 'angle'
    elif any(word in filename_lower for word in ['swatch', 'color', 'finish']):
        return 'swatch'
    elif any(word in filename_lower for word in ['chart', 'info', 'callout', 'infographic']):
        return 'informational'
    else:
        # Default to detail if unclear
        return 'detail'

def get_brand_folder(vendor_name):
    """Get brand folder name (lowercase)"""
    # Map common vendor names to brand folders
    brand_mapping = {
        'afx': 'afx',
        'dainolite': 'dainolite',
        'hinkley': 'hinkley',
        'justice design': 'justicedesign',
        'justicedesign': 'justicedesign',
        'crystorama': 'crystorama',
        'hudson valley': 'hudsonvalley',
    }
    
    vendor_lower = vendor_name.lower().strip()
    return brand_mapping.get(vendor_lower, vendor_lower.replace(' ', ''))

def process_vendor_file(vendor_file, template_file, mfg_mapping, vendor_name, mfg_prefix, brand_folder):
    """Process vendor file and create filled asset template"""
    
    # Read vendor file
    try:
        # Try common sheet names
        sheet_names = ['Entities', 'All', 'Sheet1']
        vendor_df = None
        
        for sheet_name in sheet_names:
            try:
                vendor_df = pd.read_excel(vendor_file, sheet_name=sheet_name)
                break
            except:
                continue
        
        if vendor_df is None:
            # Try first sheet
            vendor_df = pd.read_excel(vendor_file)
            
    except Exception as e:
        return None, None, f"Error reading vendor file: {e}"
    
    # Initialize outputs
    output_rows = []
    flags = []
    
    # Find image and SKU columns
    image_cols = [col for col in vendor_df.columns if 'image' in col.lower() or 'photo' in col.lower() or 'url' in col.lower()]
    sku_cols = [col for col in vendor_df.columns if 'sku' in col.lower() or 'item' in col.lower() or 'product' in col.lower()]
    
    if not image_cols:
        return None, None, "No image columns found in vendor file"
    
    if not sku_cols:
        return None, None, "No SKU columns found in vendor file"
    
    # Process each row
    main_image_count = 0
    
    for idx, row in vendor_df.iterrows():
        sku = str(row[sku_cols[0]]) if pd.notna(row[sku_cols[0]]) else None
        
        if not sku or sku.lower() in ['nan', 'none', '']:
            continue
        
        # Track images for this SKU
        images_processed = []
        is_first_image = True
        
        # Process all image columns
        for img_col in image_cols:
            img_value = row[img_col]
            
            if pd.isna(img_value) or str(img_value).strip() == '':
                continue
            
            # Handle multiple images in one cell (separated by comma, semicolon, or newline)
            img_urls = re.split(r'[,;\n]+', str(img_value))
            
            for img_url in img_urls:
                img_url = img_url.strip()
                
                if not img_url:
                    continue
                
                # Skip videos
                if any(ext in img_url.lower() for ext in ['.mp4', '.mov', '.avi', '.wmv', 'youtube', 'vimeo']):
                    flags.append(f"Skipped video for SKU {sku}: {img_url}")
                    continue
                
                # Extract filename from URL
                filename = img_url.split('/')[-1] if '/' in img_url else img_url
                
                # Check if it's a PDF
                is_pdf = filename.lower().endswith('.pdf')
                
                # Clean filename
                clean_name = clean_filename(filename)
                
                # Determine asset type
                if is_pdf:
                    # Check if spec or install sheet
                    if 'install' in filename.lower():
                        asset_family = 'install_sheet'
                        suffix = '_specs'  # Use specs suffix for PDFs
                        path_folder = 'specsheets'
                        extension = '.pdf'
                    else:
                        asset_family = 'spec_sheet'
                        suffix = '_specs'
                        path_folder = 'specsheets'
                        extension = '.pdf'
                    
                    mediatype_value = ''
                    
                else:
                    # Image file
                    suffix = '_new_1k'
                    extension = '.jpg'
                    
                    if is_first_image:
                        asset_family = 'main_product_image'
                        path_folder = 'products'
                        mediatype_value = ''
                        is_first_image = False
                        main_image_count += 1
                    else:
                        asset_family = 'media'
                        path_folder = 'media'
                        mediatype_value = determine_mediatype(filename, row)
                
                # Create code and label (identical and lowercase)
                code_label = f"{mfg_prefix}_{clean_name}{suffix}"
                
                # Create product_reference
                product_ref = f"{mfg_prefix}_{sku}"
                
                # Create imagelink (all lowercase)
                imagelink = f"{brand_folder}/{path_folder}/{clean_name}_new{extension}".lower()
                
                # Check for duplicates
                if code_label in images_processed:
                    flags.append(f"Duplicate filename detected for SKU {sku}: {code_label}")
                else:
                    images_processed.append(code_label)
                
                # Add row
                output_rows.append({
                    'code': code_label,
                    'label-en_US': code_label,
                    'product_reference': product_ref,
                    'imagelink': imagelink,
                    'assetFamilyIdentifier': asset_family,
                    'mediatype': mediatype_value
                })
    
    # Create output DataFrame
    output_df = pd.DataFrame(output_rows)
    
    # Validation checks
    if main_image_count == 0:
        flags.append("WARNING: No main product images found")
    
    # Create flags text
    flags_text = "\n".join(flags) if flags else "No issues detected"
    
    return output_df, flags_text, None

# Main UI
st.markdown('<div class="main-header">Belami Asset Template Automation</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Automatically fill Asset Templates with vendor data according to Belami standards</div>', unsafe_allow_html=True)

# Load manufacturer mapping
mfg_mapping, mfg_df = load_manufacturer_mapping()

# Sidebar for configuration
with st.sidebar:
    st.markdown("### Configuration")
    
    st.markdown("#### Vendor Information")
    vendor_name = st.text_input("Vendor Name", help="e.g., AFX, Dainolite, Hinkley")
    
    # Auto-suggest manufacturer prefix
    suggested_prefix = None
    if vendor_name:
        vendor_lower = vendor_name.lower().strip()
        if vendor_lower in mfg_mapping:
            suggested_prefix = mfg_mapping[vendor_lower]
            st.success(f"Found manufacturer ID: {suggested_prefix}")
    
    mfg_prefix = st.text_input(
        "Manufacturer Prefix", 
        value=suggested_prefix if suggested_prefix else "",
        help="Manufacturer ID (e.g., 2605 for AFX)"
    )
    
    brand_folder = st.text_input(
        "Brand Folder Name",
        value=get_brand_folder(vendor_name) if vendor_name else "",
        help="Lowercase brand folder (e.g., afx, dainolite)"
    )
    
    st.markdown("---")
    
    st.markdown("#### File Upload")
    st.info("Upload the required files below")

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown('<div class="section-header">File Upload</div>', unsafe_allow_html=True)
    
    # Upload vendor file
    vendor_file = st.file_uploader(
        "Upload Vendor Data File",
        type=['xlsx', 'xls'],
        help="Excel file with vendor product data (usually 'Entities' or 'All' sheet)"
    )
    
    # Upload template file
    template_file = st.file_uploader(
        "Upload Asset Template",
        type=['xlsx'],
        help="Empty Belami Asset Template (Asset Template.xlsx)"
    )

with col2:
    st.markdown('<div class="section-header">Status</div>', unsafe_allow_html=True)
    
    # Status indicators
    status_items = []
    if vendor_name and mfg_prefix:
        status_items.append("✓ Vendor configured")
    else:
        status_items.append("⚠ Vendor info needed")
    
    if vendor_file:
        status_items.append("✓ Vendor file uploaded")
    else:
        status_items.append("⚠ Vendor file needed")
    
    if template_file:
        status_items.append("✓ Template uploaded")
    else:
        status_items.append("⚠ Template needed")
    
    for item in status_items:
        if "✓" in item:
            st.markdown(f'<div style="color: #10b981; padding: 0.25rem 0;">{item}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="color: #f59e0b; padding: 0.25rem 0;">{item}</div>', unsafe_allow_html=True)

# Process button
st.markdown('<div class="section-header">Processing</div>', unsafe_allow_html=True)

can_process = vendor_file and template_file and vendor_name and mfg_prefix and brand_folder

if not can_process:
    st.warning("Please provide all required information and files before processing")

if st.button("Generate Asset Template", disabled=not can_process, type="primary"):
    with st.spinner("Processing vendor data..."):
        # Process the file
        output_df, flags_text, error = process_vendor_file(
            vendor_file, template_file, mfg_mapping, 
            vendor_name, mfg_prefix, brand_folder
        )
        
        if error:
            st.error(f"Error: {error}")
        else:
            st.success(f"Successfully processed {len(output_df)} assets")
            
            # Display results
            st.markdown('<div class="section-header">Results</div>', unsafe_allow_html=True)
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Assets", len(output_df))
            
            with col2:
                main_images = len(output_df[output_df['assetFamilyIdentifier'] == 'main_product_image'])
                st.metric("Main Images", main_images)
            
            with col3:
                media_images = len(output_df[output_df['assetFamilyIdentifier'] == 'media'])
                st.metric("Media Images", media_images)
            
            with col4:
                pdfs = len(output_df[output_df['assetFamilyIdentifier'].isin(['spec_sheet', 'install_sheet'])])
                st.metric("PDFs", pdfs)
            
            # Preview data
            st.markdown("#### Data Preview")
            st.dataframe(output_df.head(20), use_container_width=True)
            
            # Flags/warnings
            if flags_text != "No issues detected":
                st.markdown("#### Validation Flags")
                st.markdown(f'<div class="warning-box">{flags_text.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
            
            # Download files
            st.markdown('<div class="section-header">Download Results</div>', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Create Excel file
                output_excel = io.BytesIO()
                with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
                    output_df.to_excel(writer, sheet_name='Sheet1', index=False)
                output_excel.seek(0)
                
                st.download_button(
                    label="Download Filled Asset Template",
                    data=output_excel,
                    file_name=f"{vendor_name}_Filled_Asset_Template.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            
            with col2:
                # Create flags file
                flags_file = f"Asset Template Processing Log - {vendor_name}\n"
                flags_file += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                flags_file += f"Total Assets: {len(output_df)}\n\n"
                flags_file += "Validation Flags:\n"
                flags_file += "=" * 50 + "\n"
                flags_file += flags_text
                
                st.download_button(
                    label="Download Processing Log",
                    data=flags_file,
                    file_name=f"{vendor_name}_asset_flags.txt",
                    mime="text/plain"
                )

# Information section at bottom
with st.expander("Processing Rules & Guidelines"):
    st.markdown("""
    ### Belami Asset Template Processing Rules
    
    **File Naming Convention:**
    - Images: `manufacturerprefix_filename_without_extension_new_1k`
    - PDFs: `manufacturerprefix_filename_without_extension_specs`
    - All filenames are converted to lowercase
    
    **Asset Family Types:**
    - `main_product_image`: First image with white background (full product view)
    - `media`: Additional product images
    - `spec_sheet`: Specification PDFs
    - `install_sheet`: Installation instruction PDFs
    
    **Media Types (for media assets only):**
    - `lifestyle`: Product in room/environment
    - `dimension`: Measurements, drawings, diagrams
    - `detail`: Close-up views
    - `angle`: Alternate viewing angles
    - `informational`: Charts, callouts, infographics
    - `swatch`: Color/finish swatches
    
    **Image Link Paths:**
    - Main images: `brand/products/filename_new_1k.jpg`
    - Media images: `brand/media/filename_new_1k.jpg`
    - PDFs: `brand/specsheets/filename_new.pdf`
    
    **Important Notes:**
    - Video files are automatically skipped
    - Each row represents one real asset (image or PDF)
    - All paths and filenames must be lowercase
    - No empty columns in generated rows
    """)

# Footer
st.markdown("---")
st.markdown(
    '<div style="text-align: center; color: #6b7280; padding: 1rem;">Belami Asset Template Automation Tool | Version 1.0</div>', 
    unsafe_allow_html=True
)
