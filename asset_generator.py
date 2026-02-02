import streamlit as st
import pandas as pd
import io
from pathlib import Path
import traceback

def show():
    st.markdown('<div class="title">Asset Template Generator</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Professional asset template automation</div>', unsafe_allow_html=True)
    
    # Load manufacturer mapping
    @st.cache_data
    def load_manufacturer_mapping():
        try:
            df = pd.read_excel('Manufacturer_ID_s.xlsx')
            mapping = dict(zip(df['Brand'].str.strip(), df['Manu ID'].astype(str)))
            vendor_list = sorted(df['Brand'].str.strip().tolist())
            return mapping, vendor_list
        except:
            return {}, []
    
    mfg_mapping, vendor_list = load_manufacturer_mapping()
    
    # Session state for better state management
    if 'selected_sheet' not in st.session_state:
        st.session_state.selected_sheet = None
    if 'selected_header_row' not in st.session_state:
        st.session_state.selected_header_row = None
    if 'sku_column' not in st.session_state:
        st.session_state.sku_column = None
    if 'available_columns' not in st.session_state:
        st.session_state.available_columns = []
    
    # Configuration section
    st.markdown("### Configuration")
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if vendor_list:
            vendor_name = st.selectbox(
                "Vendor Name",
                options=[""] + vendor_list,
                index=0
            )
        else:
            vendor_name = st.text_input("Vendor Name", placeholder="AFX")
    
    with col2:
        suggested = ""
        if vendor_name and vendor_name in mfg_mapping:
            suggested = mfg_mapping[vendor_name]
        
        mfg_prefix = st.text_input(
            "Manufacturer ID",
            value=suggested,
            placeholder="2605"
        )
    
    with col3:
        brand_folder = st.text_input(
            "Brand Folder",
            value=vendor_name.lower().replace(' ', '') if vendor_name else "",
            placeholder="afx"
        )
    
    # Upload section
    st.markdown("### Upload Files")
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        vendor_file = st.file_uploader("Vendor Data File", type=['xlsx', 'xls'])
    
    with col2:
        template_file = st.file_uploader("Asset Template", type=['xlsx'])
    
    # Sheet selection
    selected_sheet = None
    if vendor_file:
        try:
            excel_file = pd.ExcelFile(vendor_file)
            sheets = excel_file.sheet_names
            
            if len(sheets) > 1:
                st.markdown("---")
                st.markdown("### Select Data Sheet")
                
                cols = st.columns(min(len(sheets), 5))
                for idx, sheet in enumerate(sheets):
                    with cols[idx % 5]:
                        button_type = "primary" if st.session_state.selected_sheet == sheet else "secondary"
                        if st.button(sheet, key=f"sheet_{idx}", use_container_width=True, type=button_type):
                            st.session_state.selected_sheet = sheet
                            st.session_state.selected_header_row = None  # Reset header row
                            st.session_state.sku_column = None  # Reset SKU column
                            st.rerun()
                
                if st.session_state.selected_sheet:
                    selected_sheet = st.session_state.selected_sheet
                    st.success(f"Selected: {selected_sheet}")
            else:
                selected_sheet = sheets[0]
                st.session_state.selected_sheet = selected_sheet
        except Exception as e:
            st.error(f"Error reading file: {e}")
    
    # Header Row Selection - IMPROVED
    selected_header_row = None
    if vendor_file and selected_sheet:
        try:
            st.markdown("---")
            st.markdown("### Step 1: Select Header Row")
            st.write("Which row contains your column names?")
            
            # Read first 20 rows
            preview_df = pd.read_excel(vendor_file, sheet_name=selected_sheet, header=None, nrows=20)
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                # Simple dropdown: just show row numbers
                row_number = st.selectbox(
                    "Header Row",
                    options=list(range(1, min(21, len(preview_df) + 1))),
                    format_func=lambda x: f"Row {x}",
                    key="header_selector"
                )
                selected_header_row = row_number - 1  # Convert to 0-indexed
                st.session_state.selected_header_row = selected_header_row
            
            # Show what columns will be read
            with col2:
                if selected_header_row is not None:
                    try:
                        temp_preview = pd.read_excel(
                            vendor_file, 
                            sheet_name=selected_sheet, 
                            header=selected_header_row,
                            nrows=1
                        )
                        col_count = len(temp_preview.columns)
                        st.success(f"Row {row_number} selected - Found {col_count} columns")
                    except:
                        st.info(f"Row {row_number} selected")
        
        except Exception as e:
            st.error(f"Error reading file: {e}")
    
    # SKU Column Selection - DYNAMIC
    sku_column_selected = None
    if vendor_file and selected_sheet and st.session_state.selected_header_row is not None:
        try:
            st.markdown("---")
            st.markdown("### Step 2: Select SKU Column")
            st.write("Which column contains the product SKU/Item Number?")
            
            # Read with the selected header row to get actual columns
            temp_df = pd.read_excel(
                vendor_file, 
                sheet_name=selected_sheet, 
                header=st.session_state.selected_header_row, 
                nrows=0
            )
            available_columns = [str(col) for col in temp_df.columns]
            st.session_state.available_columns = available_columns
            
            # Common SKU column names for auto-detection
            common_sku_names = [
                'SKU', 'sku', 'Sku', 'SKU Number',
                'Model Number', 'model_number', 'Model_Number', 'MODEL_NUMBER',
                'Item Number', 'item_number', 'Item_Number', 'ITEM_NUMBER',
                'Item Num', 'item_num', 'Item_Num',
                'Product Code', 'product_code', 'Product_Code',
                'Product Number', 'product_number',
                'Part Number', 'part_number', 'Part_Number',
                'Item Code', 'item_code', 'Item_Code',
                'Article Number', 'article_number',
                'Catalog Number', 'catalog_number',
                'Material Number', 'material_number',
                'Style Number', 'style_number'
            ]
            
            # Try to auto-detect
            auto_detected = None
            for common_name in common_sku_names:
                if common_name in available_columns:
                    auto_detected = common_name
                    break
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Dropdown with ONLY actual columns from file
                default_index = 0
                if auto_detected and auto_detected in available_columns:
                    default_index = available_columns.index(auto_detected) + 1
                
                sku_column_selected = st.selectbox(
                    "Select SKU Column",
                    options=["-- Select Column --"] + available_columns,
                    index=default_index,
                    help="Choose the column that contains product identifiers"
                )
                
                if sku_column_selected != "-- Select Column --":
                    st.session_state.sku_column = sku_column_selected
                else:
                    sku_column_selected = None
            
            with col2:
                st.info(f"Total columns found: {len(available_columns)}")
                st.write("Auto-detect: " + (f"Detected '{auto_detected}'" if auto_detected else "No match found"))
        
        except Exception as e:
            st.error(f"Error reading columns: {e}")
    
    # Status indicators
    st.markdown("---")
    st.markdown("### Status")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if vendor_name and mfg_prefix and brand_folder:
            st.success("Config: Ready")
        else:
            st.warning("Config: Incomplete")
    
    with col2:
        if vendor_file:
            st.success("File: Uploaded")
        else:
            st.warning("File: Missing")
    
    with col3:
        if selected_sheet:
            st.success("Sheet: Selected")
        else:
            st.warning("Sheet: Select")
    
    with col4:
        if template_file:
            st.success("Template: Ready")
        else:
            st.warning("Template: Missing")
    
    # Process button
    st.markdown("---")
    can_process = all([
        vendor_file, 
        template_file, 
        vendor_name, 
        mfg_prefix, 
        brand_folder, 
        selected_sheet, 
        sku_column_selected and sku_column_selected != "-- Select Column --",
        st.session_state.selected_header_row is not None
    ])
    
    if st.button("Generate Asset Template", disabled=not can_process, use_container_width=True, type="primary"):
        with st.spinner("Processing..."):
            try:
                # Read vendor data with selected header row
                df = pd.read_excel(
                    vendor_file, 
                    sheet_name=selected_sheet, 
                    header=st.session_state.selected_header_row
                )
                st.info(f"Processing {len(df)} rows from: {selected_sheet} (Header row: {st.session_state.selected_header_row + 1})")
                
                # Process
                output_df, flags, error = process_vendor_file(df, mfg_prefix, brand_folder, sku_column_selected)
                
                if error:
                    st.error(error)
                else:
                    st.success(f"Created {len(output_df)} assets successfully")
                    
                    # Metrics
                    st.markdown("---")
                    st.markdown("### Results")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Total Assets", len(output_df))
                    
                    with col2:
                        main = len(output_df[output_df['assetFamilyIdentifier'] == 'main_product_image'])
                        st.metric("Main Images", main)
                    
                    with col3:
                        media = len(output_df[output_df['assetFamilyIdentifier'] == 'media'])
                        st.metric("Media Assets", media)
                    
                    with col4:
                        pdfs = len(output_df[output_df['assetFamilyIdentifier'].isin(['spec_sheet', 'install_sheet'])])
                        st.metric("Documents", pdfs)
                    
                    # Preview
                    with st.expander("View Generated Data"):
                        st.dataframe(output_df.head(20), use_container_width=True)
                    
                    # Download
                    st.markdown("---")
                    st.markdown("### Download Results")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        output_excel = io.BytesIO()
                        with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
                            output_df.to_excel(writer, sheet_name='Sheet1', index=False)
                        output_excel.seek(0)
                        
                        st.download_button(
                            "Download Asset Template (Excel)",
                            data=output_excel,
                            file_name=f"{vendor_name}_Asset_Template.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True,
                            type="primary"
                        )
                    
                    with col2:
                        log = f"Processing Log - {vendor_name}\n{'='*50}\n{flags}"
                        st.download_button(
                            "Download Log (Text)",
                            data=log,
                            file_name=f"{vendor_name}_log.txt",
                            mime="text/plain",
                            use_container_width=True
                        )
            
            except Exception as e:
                st.error(f"Error: {e}")
                st.code(traceback.format_exc())

def process_vendor_file(df, mfg_prefix, brand_folder, sku_column):
    """Process vendor data to create asset template - ROBUST VERSION"""
    
    # Verify SKU column exists
    if sku_column not in df.columns:
        return None, None, f"SKU column '{sku_column}' not found in the data"
    
    output_rows = []
    flags = []
    skipped_rows = []
    processed_skus = set()
    
    # Image column mappings - comprehensive list
    image_mappings = {
        'Image File 1': ('main_product_image', 'products', ''),
        'Image File 2': ('media', 'media', 'angle'),
        'Image File 3': ('media', 'media', 'angle'),
        'Lifestyle Image 1': ('media', 'media', 'lifestyle'),
        'Lifestyle Image 2': ('media', 'media', 'lifestyle'),
        'Lifestyle Image 3': ('media', 'media', 'lifestyle'),
        'B/B Image 1': ('media', 'media', 'angle'),
        'B/B Image 2': ('media', 'media', 'angle'),
        'B/B Image 3': ('media', 'media', 'angle'),
        'B/B Image Dimensional': ('media', 'media', 'dimension'),
        'Infographic Image 1': ('media', 'media', 'informational'),
        'Infographic Image 2': ('media', 'media', 'informational'),
        'Infographic Image 3': ('media', 'media', 'informational'),
        'Infographic Image 4': ('media', 'media', 'informational'),
        'Infographic Image 5': ('media', 'media', 'informational'),
        'Infographic Image 6': ('media', 'media', 'informational'),
        'Infographic Image 7': ('media', 'media', 'informational'),
        'Infographic Image 8': ('media', 'media', 'informational'),
        'Infographic Image 9': ('media', 'media', 'informational'),
        'Infographic Image 10': ('media', 'media', 'informational'),
        'Diagram Image 1': ('media', 'media', 'dimension'),
        'Diagram Image 2': ('media', 'media', 'dimension'),
        'Diagram Image 3': ('media', 'media', 'dimension'),
        'Diagram Image 4': ('media', 'media', 'dimension'),
        'Swatch Image 1': ('media', 'media', 'swatch'),
        'Swatch Image 2': ('media', 'media', 'swatch'),
        'Swatch Image 3': ('media', 'media', 'swatch'),
        'Swatch Image 4': ('media', 'media', 'swatch'),
        'Spec Sheet Image': ('spec_sheet', 'specsheets', ''),
        'Installation/Assembly Image 1': ('install_sheet', 'specsheets', ''),
        'Installation/Assembly Image 2': ('install_sheet', 'specsheets', ''),
    }
    
    main_count = 0
    media_count = 0
    pdf_count = 0
    row_count = 0
    
    # ROBUST DATA READING - Handle all rows
    for idx, row in df.iterrows():
        row_count += 1
        current_sku = None
        
        # Extract SKU - handle various data types
        try:
            sku_value = row[sku_column]
            
            # Skip null/empty values
            if pd.isna(sku_value):
                skipped_rows.append(f"Row {idx+1}: SKU is empty")
                continue
            
            current_sku = str(sku_value).strip()
            
            # Skip if empty after stripping
            if not current_sku or current_sku.lower() == 'nan' or current_sku == '':
                skipped_rows.append(f"Row {idx+1}: SKU is empty after cleaning")
                continue
            
        except Exception as e:
            skipped_rows.append(f"Row {idx+1}: Error reading SKU - {str(e)}")
            continue
        
        # Skip duplicate SKUs
        if current_sku in processed_skus:
            skipped_rows.append(f"Row {idx+1}: Duplicate SKU {current_sku}")
            continue
        
        processed_skus.add(current_sku)
        product_ref = f"{mfg_prefix}_{current_sku}"
        
        # Process EACH column in the file - don't skip any
        for col_name in df.columns:
            # Check if column exists in mappings
            if col_name not in image_mappings:
                continue
            
            asset_family, folder, mediatype = image_mappings[col_name]
            
            try:
                img_value = row[col_name]
                
                # Skip empty cells
                if pd.isna(img_value) or str(img_value).strip() == '' or str(img_value).lower() == 'nan':
                    continue
                
                filename = str(img_value).strip()
                
                # Skip videos
                if any(ext in filename.lower() for ext in ['.mp4', '.mov', '.avi', '.wmv', 'youtube', 'vimeo']):
                    flags.append(f"Skipped video in {col_name}: {filename}")
                    continue
                
                # Get file extension
                file_ext = Path(filename).suffix.lower()
                is_pdf = file_ext == '.pdf'
                
                # Get base filename without extension
                base_name = Path(filename).stem
                
                # Create code (lowercase, cleaned)
                code_clean = base_name.lower()
                
                # Remove special characters
                special_chars = [' ', ',', '/', '\\', '(', ')', '[', ']', '{', '}', 
                                '&', '#', '@', '!', '*', '+', '=', '%', '$', '^', 
                                '~', '`', ';', ':', '"', "'", '<', '>', '?', '|', '.']
                
                for char in special_chars:
                    code_clean = code_clean.replace(char, '_')
                
                # Remove multiple underscores
                while '__' in code_clean:
                    code_clean = code_clean.replace('__', '_')
                
                # Remove leading/trailing underscores
                code_clean = code_clean.strip('_')
                
                if is_pdf:
                    code = f"{mfg_prefix}_{code_clean}_specs"
                    imagelink = f"{brand_folder}/{folder}/{base_name}_new.pdf"
                    pdf_count += 1
                else:
                    code = f"{mfg_prefix}_{code_clean}_new_1k"
                    imagelink = f"{brand_folder}/{folder}/{base_name}_new_1k.jpg"
                    if asset_family == 'main_product_image':
                        main_count += 1
                    else:
                        media_count += 1
                
                # Add row
                output_rows.append({
                    'code': code,
                    'label-en_US': code,
                    'product_reference': product_ref,
                    'imagelink': imagelink,
                    'assetFamilyIdentifier': asset_family,
                    'mediatype': mediatype if mediatype else ''
                })
            
            except Exception as e:
                flags.append(f"Error processing {col_name} in row {idx+1}: {str(e)}")
                continue
    
    if not output_rows:
        return None, None, "No images found in vendor file"
    
    output_df = pd.DataFrame(output_rows)
    
    # Build flags report
    flags.insert(0, f"Total rows processed: {row_count}")
    flags.insert(1, f"Rows with data: {len(processed_skus)}")
    flags.insert(2, f"Main images: {main_count}")
    flags.insert(3, f"Media images: {media_count}")
    flags.insert(4, f"PDFs: {pdf_count}")
    flags.insert(5, f"Total assets generated: {len(output_df)}")
    
    if skipped_rows:
        flags.append(f"\nSkipped {len(skipped_rows)} rows:")
        for skip in skipped_rows[:10]:  # Show first 10
            flags.append(f"  - {skip}")
        if len(skipped_rows) > 10:
            flags.append(f"  ... and {len(skipped_rows) - 10} more")
    
    return output_df, "\n".join(flags), None
