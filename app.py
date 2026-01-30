import streamlit as st
import pandas as pd
import openpyxl
from openpyxl import load_workbook, Workbook
from openpyxl.styles import Font, PatternFill, Alignment
import re
import io
from datetime import datetime
from pathlib import Path
import traceback

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

def find_columns(df, patterns, column_type):
    """Robust column finder that checks multiple patterns"""
    found_cols = []
    
    for col in df.columns:
        col_lower = str(col).lower().strip()
        for pattern in patterns:
            if pattern in col_lower:
                found_cols.append(col)
                break
    
    if not found_cols:
        st.warning(f"⚠️ No {column_type} columns found automatically. Available columns:")
        st.write(list(df.columns))
    
    return found_cols

def process_vendor_file(vendor_file, template_file, mfg_mapping, vendor_name, mfg_prefix, brand_folder):
    """Process vendor file and create filled asset template"""
    
    try:
        # Read vendor file - try multiple approaches
        vendor_df = None
        sheet_used = None
        
        # Get all sheet names first
        try:
            excel_file = pd.ExcelFile(vendor_file)
            available_sheets = excel_file.sheet_names
            st.info(f"📋 Available sheets: {', '.join(available_sheets)}")
        except Exception as e:
            return None, None, f"Error reading Excel file structure: {str(e)}"
        
        # Try common sheet names in order
        sheet_priority = ['Entities', 'entities', 'All', 'all', 'Sheet1', 'sheet1', 'Data', 'data']
        
        for sheet_name in sheet_priority:
            if sheet_name in available_sheets:
                try:
                    vendor_df = pd.read_excel(vendor_file, sheet_name=sheet_name)
                    sheet_used = sheet_name
                    st.success(f"✓ Using sheet: {sheet_name}")
                    break
                except Exception as e:
                    continue
        
        # If no priority sheet found, use first sheet
        if vendor_df is None:
            try:
                vendor_df = pd.read_excel(vendor_file, sheet_name=0)
                sheet_used = available_sheets[0]
                st.success(f"✓ Using first sheet: {sheet_used}")
            except Exception as e:
                return None, None, f"Error reading Excel file: {str(e)}"
        
        # Display column information
        st.info(f"📊 Found {len(vendor_df.columns)} columns and {len(vendor_df)} rows")
        
        with st.expander("Show all columns in vendor file"):
            st.write(list(vendor_df.columns))
        
        # Find image columns with expanded patterns
        image_patterns = [
            'image', 'photo', 'picture', 'pic', 'img',
            'url', 'link', 'path', 'file',
            'media', 'asset', 'visual',
            'main', 'primary', 'additional', 'alt',
            'http', 'www', '.jpg', '.png', '.pdf'
        ]
        
        image_cols = find_columns(vendor_df, image_patterns, "image")
        
        if not image_cols:
            # Manual column selection
            st.error("❌ Could not auto-detect image columns")
            st.write("**Please select image columns manually:**")
            return None, None, "No image columns detected. Please check your file format."
        
        st.success(f"✓ Found {len(image_cols)} image column(s): {', '.join(image_cols)}")
        
        # Find SKU columns with expanded patterns
        sku_patterns = [
            'sku', 'item', 'product', 'part', 'model',
            'code', 'number', 'id', 'identifier',
            'catalog', 'reference', 'style'
        ]
        
        sku_cols = find_columns(vendor_df, sku_patterns, "SKU")
        
        if not sku_cols:
            st.error("❌ Could not auto-detect SKU columns")
            return None, None, "No SKU columns detected. Please check your file format."
        
        st.success(f"✓ Found SKU column: {sku_cols[0]}")
        
        # Initialize outputs
        output_rows = []
        flags = []
        
        # Statistics
        total_rows = 0
        skipped_rows = 0
        processed_skus = 0
        total_assets = 0
        skipped_videos = 0
        
        # Process each row
        main_image_count = 0
        
        for idx, row in vendor_df.iterrows():
            total_rows += 1
            
            # Get SKU
            sku = None
            for sku_col in sku_cols:
                if pd.notna(row[sku_col]):
                    sku = str(row[sku_col]).strip()
                    if sku and sku.lower() not in ['nan', 'none', '', 'null']:
                        break
            
            if not sku:
                skipped_rows += 1
                continue
            
            processed_skus += 1
            
            # Track images for this SKU
            images_processed = []
            is_first_image = True
            sku_asset_count = 0
            
            # Process all image columns
            for img_col in image_cols:
                if img_col not in row.index:
                    continue
                    
                img_value = row[img_col]
                
                if pd.isna(img_value) or str(img_value).strip() == '':
                    continue
                
                # Handle multiple images in one cell (separated by various delimiters)
                img_urls = re.split(r'[,;\n\r\|]+', str(img_value))
                
                for img_url in img_urls:
                    img_url = img_url.strip()
                    
                    if not img_url or img_url.lower() in ['nan', 'none', 'null', '']:
                        continue
                    
                    # Skip videos
                    video_extensions = ['.mp4', '.mov', '.avi', '.wmv', '.flv', '.webm', '.mkv']
                    video_sites = ['youtube', 'vimeo', 'youtu.be']
                    
                    is_video = False
                    img_lower = img_url.lower()
                    
                    if any(ext in img_lower for ext in video_extensions):
                        is_video = True
                    if any(site in img_lower for site in video_sites):
                        is_video = True
                    
                    if is_video:
                        flags.append(f"⏭️ Skipped video for SKU {sku}: {img_url[:50]}...")
                        skipped_videos += 1
                        continue
                    
                    # Extract filename from URL or path
                    # Handle various URL formats
                    filename = img_url.split('/')[-1].split('\\')[-1]
                    if '?' in filename:
                        filename = filename.split('?')[0]
                    
                    # If no extension found, assume .jpg
                    if '.' not in filename:
                        filename = filename + '.jpg'
                    
                    # Check if it's a PDF
                    is_pdf = filename.lower().endswith('.pdf')
                    
                    # Clean filename
                    clean_name = clean_filename(filename)
                    
                    if not clean_name:
                        flags.append(f"⚠️ Could not clean filename for SKU {sku}: {filename}")
                        continue
                    
                    # Determine asset type
                    if is_pdf:
                        # Check if spec or install sheet
                        if 'install' in filename.lower():
                            asset_family = 'install_sheet'
                            suffix = '_specs'
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
                        flags.append(f"⚠️ Duplicate filename for SKU {sku}: {code_label}")
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
                    
                    sku_asset_count += 1
                    total_assets += 1
            
            if sku_asset_count == 0:
                flags.append(f"⚠️ No assets found for SKU: {sku}")
        
        # Create output DataFrame
        if not output_rows:
            return None, None, "No assets were processed. Please check your vendor file format."
        
        output_df = pd.DataFrame(output_rows)
        
        # Add processing statistics
        flags.insert(0, f"📊 Processing Summary:")
        flags.insert(1, f"  • Total rows in file: {total_rows}")
        flags.insert(2, f"  • SKUs processed: {processed_skus}")
        flags.insert(3, f"  • Total assets created: {total_assets}")
        flags.insert(4, f"  • Main images: {main_image_count}")
        flags.insert(5, f"  • Videos skipped: {skipped_videos}")
        flags.insert(6, f"  • Rows skipped (no SKU): {skipped_rows}")
        flags.insert(7, "")
        
        # Validation checks
        if main_image_count == 0:
            flags.append("⚠️ WARNING: No main product images found")
        
        if main_image_count < processed_skus:
            flags.append(f"⚠️ WARNING: Some SKUs missing main images ({main_image_count} main images for {processed_skus} SKUs)")
        
        # Create flags text
        flags_text = "\n".join(flags) if flags else "No issues detected"
        
        return output_df, flags_text, None
        
    except Exception as e:
        error_trace = traceback.format_exc()
        st.error("❌ Error during processing:")
        st.code(error_trace)
        return None, None, f"Processing error: {str(e)}\n\nFull trace:\n{error_trace}"

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
    
    # Show preview if file uploaded
    if vendor_file:
        try:
            with st.expander("📋 Preview Vendor File (first 5 rows)"):
                preview_df = pd.read_excel(vendor_file, sheet_name=0, nrows=5)
                st.dataframe(preview_df, use_container_width=True)
                st.caption(f"Columns: {', '.join(list(preview_df.columns))}")
        except Exception as e:
            st.error(f"Could not preview file: {e}")
    
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

# Add manual column selection option
if vendor_file and not can_process:
    try:
        excel_file = pd.ExcelFile(vendor_file)
        test_df = pd.read_excel(vendor_file, sheet_name=0, nrows=5)
        
        with st.expander("🔧 Advanced: Manual Column Selection"):
            st.info("If automatic detection fails, you can manually select columns here")
            
            col1, col2 = st.columns(2)
            with col1:
                sku_column_manual = st.selectbox(
                    "Select SKU Column",
                    options=["Auto-detect"] + list(test_df.columns),
                    help="Column containing product SKUs/Item numbers"
                )
            
            with col2:
                image_columns_manual = st.multiselect(
                    "Select Image Columns",
                    options=list(test_df.columns),
                    help="Columns containing image URLs or filenames"
                )
    except:
        pass

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
