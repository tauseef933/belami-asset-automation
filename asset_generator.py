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
    
    # Session state
    if 'selected_sheet' not in st.session_state:
        st.session_state.selected_sheet = None
    if 'sku_column' not in st.session_state:
        st.session_state.sku_column = None
    
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
                            st.rerun()
                
                if st.session_state.selected_sheet:
                    selected_sheet = st.session_state.selected_sheet
                    st.success(f"Selected: {selected_sheet}")
            else:
                selected_sheet = sheets[0]
                st.session_state.selected_sheet = selected_sheet
        except Exception as e:
            st.error(f"Error reading file: {e}")
    
    # SKU Column Selection - NEW FEATURE
    sku_column_selected = None
    if vendor_file and selected_sheet:
        try:
            # Read just to get columns
            temp_df = pd.read_excel(vendor_file, sheet_name=selected_sheet, header=1, nrows=0)
            available_columns = [str(col) for col in temp_df.columns]
            
            st.markdown("---")
            st.markdown("### Select SKU Column")
            
            # Common SKU column names for auto-detection
            common_sku_names = [
                'SKU', 'sku', 'Sku',
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
            
            # If auto-detected, show it
            if auto_detected:
                st.info(f"Auto-detected SKU column: {auto_detected}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Dropdown selector
                sku_column_selected = st.selectbox(
                    "Select SKU Column from Dropdown",
                    options=[""] + available_columns,
                    index=available_columns.index(auto_detected) + 1 if auto_detected else 0
                )
            
            with col2:
                # Manual input
                custom_sku_column = st.text_input(
                    "Or Enter Custom Column Name",
                    placeholder="Type exact column name"
                )
                
                if custom_sku_column:
                    sku_column_selected = custom_sku_column
            
            if sku_column_selected:
                st.success(f"Using SKU column: {sku_column_selected}")
                st.session_state.sku_column = sku_column_selected
        
        except Exception as e:
            st.error(f"Error reading columns: {e}")
    
    # Status indicators
    st.markdown("---")
    st.markdown("### Status")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if vendor_name and mfg_prefix and brand_folder:
            st.success("Config Ready")
        else:
            st.warning("Config Needed")
    
    with col2:
        if vendor_file:
            st.success("File Uploaded")
        else:
            st.warning("Upload File")
    
    with col3:
        if selected_sheet:
            st.success("Sheet Selected")
        else:
            st.warning("Select Sheet")
    
    with col4:
        if template_file:
            st.success("Template Ready")
        else:
            st.warning("Upload Template")
    
    # Process button
    st.markdown("---")
    can_process = all([vendor_file, template_file, vendor_name, mfg_prefix, brand_folder, selected_sheet, sku_column_selected])
    
    if not sku_column_selected and vendor_file and selected_sheet:
        st.warning("Please select SKU column before processing")
    
    if st.button("Generate Asset Template", disabled=not can_process, use_container_width=True):
        with st.spinner("Processing..."):
            try:
                # Read vendor data
                df = pd.read_excel(vendor_file, sheet_name=selected_sheet, header=1)
                st.info(f"Processing {len(df)} rows from: {selected_sheet}")
                
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
                        st.metric("Media", media)
                    
                    with col4:
                        pdfs = len(output_df[output_df['assetFamilyIdentifier'].isin(['spec_sheet', 'install_sheet'])])
                        st.metric("PDFs", pdfs)
                    
                    # Preview
                    with st.expander("Preview Data"):
                        st.dataframe(output_df.head(20), use_container_width=True)
                    
                    # Download
                    st.markdown("---")
                    st.markdown("### Download")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        output_excel = io.BytesIO()
                        with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
                            output_df.to_excel(writer, sheet_name='Sheet1', index=False)
                        output_excel.seek(0)
                        
                        st.download_button(
                            "Download Asset Template",
                            data=output_excel,
                            file_name=f"{vendor_name}_Asset_Template.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                    
                    with col2:
                        log = f"Processing Log - {vendor_name}\n{'='*50}\n{flags}"
                        st.download_button(
                            "Download Log",
                            data=log,
                            file_name=f"{vendor_name}_log.txt",
                            mime="text/plain",
                            use_container_width=True
                        )
            
            except Exception as e:
                st.error(f"Error: {e}")
                st.code(traceback.format_exc())

def process_vendor_file(df, mfg_prefix, brand_folder, sku_column):
    """Process vendor data to create asset template"""
    
    # Verify SKU column exists
    if sku_column not in df.columns:
        return None, None, f"SKU column '{sku_column}' not found in the data"
    
    output_rows = []
    flags = []
    
    # Image column mappings
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
    
    for idx, row in df.iterrows():
        current_sku = str(row[sku_column]) if pd.notna(row[sku_column]) else None
        
        if not current_sku or current_sku == 'nan':
            continue
        
        product_ref = f"{mfg_prefix}_{current_sku}"
        
        # Process each image column
        for col_name, (asset_family, folder, mediatype) in image_mappings.items():
            if col_name not in row.index:
                continue
                
            img_value = row[col_name]
            
            if pd.isna(img_value) or str(img_value).strip() == '' or str(img_value) == 'nan':
                continue
            
            filename = str(img_value).strip()
            
            # Skip videos
            if any(ext in filename.lower() for ext in ['.mp4', '.mov', '.avi', '.wmv', 'youtube', 'vimeo']):
                flags.append(f"Skipped video: {filename}")
                continue
            
            # Get file extension
            file_ext = Path(filename).suffix.lower()
            is_pdf = file_ext == '.pdf'
            
            # Get base filename without extension
            base_name = Path(filename).stem
            
            # Create code (lowercase, cleaned) - Simple replacement, no regex
            code_clean = base_name.lower()
            code_clean = code_clean.replace(' ', '_')
            code_clean = code_clean.replace(',', '_')
            code_clean = code_clean.replace('/', '_')
            code_clean = code_clean.replace('\\', '_')
            code_clean = code_clean.replace('(', '_')
            code_clean = code_clean.replace(')', '_')
            code_clean = code_clean.replace('[', '_')
            code_clean = code_clean.replace(']', '_')
            code_clean = code_clean.replace('{', '_')
            code_clean = code_clean.replace('}', '_')
            code_clean = code_clean.replace('&', '_')
            code_clean = code_clean.replace('#', '_')
            code_clean = code_clean.replace('@', '_')
            code_clean = code_clean.replace('!', '_')
            code_clean = code_clean.replace('*', '_')
            code_clean = code_clean.replace('+', '_')
            code_clean = code_clean.replace('=', '_')
            code_clean = code_clean.replace('%', '_')
            code_clean = code_clean.replace('$', '_')
            code_clean = code_clean.replace('^', '_')
            code_clean = code_clean.replace('~', '_')
            code_clean = code_clean.replace('`', '_')
            code_clean = code_clean.replace(';', '_')
            code_clean = code_clean.replace(':', '_')
            code_clean = code_clean.replace('"', '_')
            code_clean = code_clean.replace("'", '_')
            code_clean = code_clean.replace('<', '_')
            code_clean = code_clean.replace('>', '_')
            code_clean = code_clean.replace('?', '_')
            code_clean = code_clean.replace('|', '_')
            code_clean = code_clean.replace('.', '_')
            
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
    
    if not output_rows:
        return None, None, "No images found in vendor file"
    
    output_df = pd.DataFrame(output_rows)
    
    flags.insert(0, f"Main images: {main_count}")
    flags.insert(1, f"Media images: {media_count}")
    flags.insert(2, f"PDFs: {pdf_count}")
    flags.insert(3, f"Total assets: {len(output_df)}")
    
    return output_df, "\n".join(flags), None
