import streamlit as st
import pandas as pd
import io
from pathlib import Path
import traceback
import re
from collections import defaultdict

# ============================================================================
# ADVANCED COLUMN DETECTION SYSTEM - Enterprise Level
# ============================================================================

class AdvancedColumnDetector:
    """
    Advanced intelligent column detection system that identifies image and PDF
    columns with high accuracy across various vendor formats and naming conventions.
    """
    
    def __init__(self):
        # Image-related keywords with weight scores (higher = more confident)
        self.image_keywords = {
            'image': 10, 'photo': 10, 'picture': 9, 'pic': 8,
            'visual': 8, 'graphic': 8, 'asset': 7, 'artwork': 9,
            'illustration': 8, 'diagram': 7, 'sketch': 7, 'render': 9,
            'product': 6, 'main': 5, 'primary': 5, 'hero': 7,
            'thumbnail': 8, 'thumb': 7, 'lifestyle': 8, 'lifestyle_image': 10,
            'angle': 6, 'gallery': 7, 'carousel': 7, 'media': 7,
            'visual_asset': 10, 'product_image': 10, 'file_path': 6,
            'url': 5, 'link': 4, 'href': 4, 'swatch': 9, 'sample': 6,
            'model': 6, 'photo_1': 9, 'photo_2': 9, 'img': 7,
            'infographic': 10, 'bb_image': 10, 'dimension': 8
        }
        
        # PDF-related keywords
        self.pdf_keywords = {
            'pdf': 10, 'spec': 9, 'sheet': 8, 'spec_sheet': 10,
            'datasheet': 10, 'specification': 9, 'document': 7,
            'catalog': 9, 'manual': 8, 'guide': 7, 'drawing': 8,
            'diagram': 7, 'blueprint': 9, 'installation': 9,
            'assembly': 9, 'instruction': 8, 'doc': 6,
            'technical': 8, 'brochure': 8, 'flyer': 7
        }
        
        # File extensions for validation
        self.image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg'}
        self.pdf_extensions = {'.pdf'}
        
    def analyze_column(self, col_name, col_data_sample):
        """
        Analyze a single column and return detection result with confidence score.
        
        Returns: {
            'column_name': str,
            'type': 'image' | 'pdf' | 'other',
            'confidence': float (0-100),
            'category': str (main_product_image, media, spec_sheet, etc),
            'reasoning': str (explanation of detection)
        }
        """
        col_lower = col_name.lower()
        result = {
            'column_name': col_name,
            'type': 'other',
            'confidence': 0,
            'category': None,
            'reasoning': []
        }
        
        # ===== STEP 1: Analyze Column Name =====
        name_score_image = 0
        name_score_pdf = 0
        name_reason = []
        
        # Check for keyword matches in column name
        words = re.split(r'[\s_\-\.\(\\)/]', col_lower)
        
        for word in words:
            if word in self.image_keywords:
                score = self.image_keywords[word]
                name_score_image += score
                name_reason.append(f"Image keyword '{word}' (+{score})")
            elif word in self.pdf_keywords:
                score = self.pdf_keywords[word]
                name_score_pdf += score
                name_reason.append(f"PDF keyword '{word}' (+{score})")
        
        # Check for numeric patterns (Image 1, Photo 2, etc)
        if re.search(r'\d+', col_lower):
            if any(kw in col_lower for kw in ['image', 'photo', 'pic', 'file']):
                name_score_image += 5
                name_reason.append("Numeric pattern with image keyword (+5)")
        
        # ===== STEP 2: Analyze Column Data =====
        data_score_image = 0
        data_score_pdf = 0
        data_reason = []
        
        valid_samples = [str(v).strip() for v in col_data_sample if pd.notna(v) and str(v).strip()]
        
        if valid_samples:
            # Check for file paths and extensions
            extension_matches_image = 0
            extension_matches_pdf = 0
            url_pattern_count = 0
            
            for sample in valid_samples[:10]:  # Check first 10 samples
                sample_lower = sample.lower()
                
                # Check for common file patterns
                if any(sample_lower.endswith(ext) for ext in self.image_extensions):
                    extension_matches_image += 1
                    data_score_image += 8
                    
                if any(sample_lower.endswith(ext) for ext in self.pdf_extensions):
                    extension_matches_pdf += 1
                    data_score_pdf += 8
                
                # Check for URL patterns
                if any(domain in sample_lower for domain in ['http://', 'https://', 'www.', '.com', '.net', '.org']):
                    url_pattern_count += 1
                    data_score_image += 4
                
                # Check for file path patterns
                if any(sep in sample for sep in ['/', '\\']) and len(sample) > 5:
                    data_score_image += 5
                    data_reason.append(f"File path pattern detected: {sample[:40]}...")
            
            if extension_matches_image > 0:
                data_reason.append(f"Found {extension_matches_image} image file(s)")
            if extension_matches_pdf > 0:
                data_reason.append(f"Found {extension_matches_pdf} PDF file(s)")
            if url_pattern_count > 0:
                data_reason.append(f"Found {url_pattern_count} URL pattern(s)")
            
            # Data quality score (higher if more non-null values)
            data_quality = len(valid_samples) / len(col_data_sample)
            if data_quality > 0.5:
                data_score_image += 5
                data_score_pdf += 5
                data_reason.append(f"Good data quality ({len(valid_samples)}/{len(col_data_sample)} filled)")
        
        # ===== STEP 3: Determine Final Classification =====
        total_image_score = name_score_image + data_score_image
        total_pdf_score = name_score_pdf + data_score_pdf
        
        # Normalize to 0-100 confidence
        if total_image_score > total_pdf_score and total_image_score > 10:
            result['type'] = 'image'
            result['confidence'] = min(100, (total_image_score / 20) * 100)
            result['reasoning'] = name_reason + data_reason
            result['category'] = self._categorize_image_column(col_lower)
            
        elif total_pdf_score > total_image_score and total_pdf_score > 10:
            result['type'] = 'pdf'
            result['confidence'] = min(100, (total_pdf_score / 20) * 100)
            result['reasoning'] = name_reason + data_reason
            result['category'] = self._categorize_pdf_column(col_lower)
        
        return result
    
    def _categorize_image_column(self, col_lower):
        """Categorize detected image column into specific type"""
        
        if any(x in col_lower for x in ['main', 'primary', 'hero', 'product_image']):
            return 'main_product_image'
        elif any(x in col_lower for x in ['thumbnail', 'thumb']):
            return 'media_thumbnail'
        elif any(x in col_lower for x in ['lifestyle', 'lifestyle_image']):
            return 'media_lifestyle'
        elif any(x in col_lower for x in ['angle', 'bb_image', 'b/b']):
            return 'media_angle'
        elif any(x in col_lower for x in ['infographic', 'info']):
            return 'media_infographic'
        elif any(x in col_lower for x in ['diagram', 'dimension', 'dimensional']):
            return 'media_dimension'
        elif any(x in col_lower for x in ['swatch', 'color']):
            return 'media_swatch'
        else:
            return 'media'
    
    def _categorize_pdf_column(self, col_lower):
        """Categorize detected PDF column into specific type"""
        
        if any(x in col_lower for x in ['spec', 'datasheet', 'specification']):
            return 'spec_sheet'
        elif any(x in col_lower for x in ['installation', 'assembly', 'instruction']):
            return 'install_sheet'
        elif any(x in col_lower for x in ['diagram', 'drawing', 'blueprint']):
            return 'technical_drawing'
        else:
            return 'document'
    
    def detect_all_columns(self, df):
        """
        Detect all image and PDF columns in dataframe.
        
        Returns: {
            'detected_columns': list of detection results,
            'summary': {
                'images': count,
                'pdfs': count,
                'total': count,
                'confidence_avg': float
            }
        }
        """
        detected = []
        
        for col_name in df.columns:
            # Sample up to 10 non-null values from column
            col_data = df[col_name].dropna().head(10)
            
            # Skip if column is mostly empty
            if len(col_data) == 0:
                continue
            
            analysis = self.analyze_column(col_name, col_data)
            
            # Only include if it's a detected type with confidence > 30%
            if analysis['type'] in ['image', 'pdf'] and analysis['confidence'] > 30:
                detected.append(analysis)
        
        # Sort by confidence (highest first)
        detected.sort(key=lambda x: x['confidence'], reverse=True)
        
        # Generate summary
        image_cols = [d for d in detected if d['type'] == 'image']
        pdf_cols = [d for d in detected if d['type'] == 'pdf']
        avg_confidence = sum(d['confidence'] for d in detected) / len(detected) if detected else 0
        
        return {
            'detected_columns': detected,
            'summary': {
                'images': len(image_cols),
                'pdfs': len(pdf_cols),
                'total': len(detected),
                'confidence_avg': round(avg_confidence, 1)
            }
        }

# Initialize detector
detector = AdvancedColumnDetector()

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
    
    # ====== ADVANCED COLUMN AUTO-DETECTION ======
    detected_image_columns = []
    detected_pdf_columns = []
    
    if vendor_file and selected_sheet and st.session_state.selected_header_row is not None:
        try:
            st.markdown("---")
            st.markdown("### Step 3: Auto-Detect Image & PDF Columns")
            st.write("Advanced AI-powered column detection using intelligent pattern matching")
            
            # Read full data for detection
            full_df = pd.read_excel(
                vendor_file, 
                sheet_name=selected_sheet, 
                header=st.session_state.selected_header_row
            )
            
            # Run advanced detection
            detection_result = detector.detect_all_columns(full_df)
            detected_columns = detection_result['detected_columns']
            summary = detection_result['summary']
            
            # Store in session state
            st.session_state.detected_columns = detected_columns
            
            if detected_columns:
                # Show summary
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Images Found", summary['images'])
                with col2:
                    st.metric("PDFs Found", summary['pdfs'])
                with col3:
                    st.metric("Total Assets", summary['total'])
                with col4:
                    st.metric("Avg Confidence", f"{summary['confidence_avg']}%")
                
                # Show detected columns with details
                st.markdown("#### Detected Columns:")
                
                for idx, detection in enumerate(detected_columns):
                    with st.expander(
                        f"{detection['column_name']} - {detection['type'].upper()} ({detection['confidence']:.0f}% confidence)",
                        expanded=(idx == 0)
                    ):
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            st.write("**Type:**", detection['type'])
                            st.write("**Category:**", detection['category'] or 'Auto')
                            st.write("**Confidence:**", f"{detection['confidence']:.1f}%")
                            
                            if detection['reasoning']:
                                with st.expander("Detection reasoning (click to expand)", expanded=False):
                                    for reason in detection['reasoning']:
                                        st.write(f"• {reason}")
                        
                        with col2:
                            # Show sample data
                            sample_values = full_df[detection['column_name']].dropna().head(3).tolist()
                            if sample_values:
                                st.write("**Sample data:**")
                                for val in sample_values:
                                    val_str = str(val)[:50]
                                    st.write(f"• {val_str}")
                
                # Separate detected columns by type
                detected_image_columns = [d for d in detected_columns if d['type'] == 'image']
                detected_pdf_columns = [d for d in detected_columns if d['type'] == 'pdf']
                
                # Manual adjustment section
                st.markdown("---")
                st.markdown("#### Column Management")
                
                col1, col2, col3 = st.columns(3)
                
                # Remove columns
                with col1:
                    st.write("**Remove Columns (Uncheck to exclude):**")
                    columns_to_remove = []
                    
                    if detected_image_columns:
                        st.write("*Images:*")
                        for col_def in detected_image_columns:
                            col_name = col_def['column_name']
                            if not st.checkbox(f"  ✓ {col_name}", value=True, key=f"keep_img_{col_name}"):
                                columns_to_remove.append(col_name)
                    
                    if detected_pdf_columns:
                        st.write("*PDFs:*")
                        for col_def in detected_pdf_columns:
                            col_name = col_def['column_name']
                            if not st.checkbox(f"  ✓ {col_name}", value=True, key=f"keep_pdf_{col_name}"):
                                columns_to_remove.append(col_name)
                
                # Add columns
                with col2:
                    st.write("**Add Missing Columns:**")
                    additional_image_col = st.selectbox(
                        "Add image column",
                        options=["-- None --"] + [c for c in available_columns if c not in [d['column_name'] for d in detected_image_columns]],
                        key="manual_image_col"
                    )
                    if additional_image_col != "-- None --":
                        detected_image_columns.append({
                            'column_name': additional_image_col,
                            'type': 'image',
                            'confidence': 50,
                            'category': 'media',
                            'reasoning': ['Manually added']
                        })
                
                with col3:
                    additional_pdf_col = st.selectbox(
                        "Add PDF column",
                        options=["-- None --"] + [c for c in available_columns if c not in [d['column_name'] for d in detected_pdf_columns]],
                        key="manual_pdf_col"
                    )
                    if additional_pdf_col != "-- None --":
                        detected_pdf_columns.append({
                            'column_name': additional_pdf_col,
                            'type': 'pdf',
                            'confidence': 50,
                            'category': 'document',
                            'reasoning': ['Manually added']
                        })
                
                # Remove unchecked columns
                detected_image_columns = [d for d in detected_image_columns if d['column_name'] not in columns_to_remove]
                detected_pdf_columns = [d for d in detected_pdf_columns if d['column_name'] not in columns_to_remove]
                
                st.session_state.detected_image_columns = detected_image_columns
                st.session_state.detected_pdf_columns = detected_pdf_columns
            
            else:
                st.warning("No image or PDF columns detected. Please check your file structure or manually select columns below.")
        
        except Exception as e:
            st.error(f"Error in auto-detection: {e}")
            import traceback
            st.code(traceback.format_exc())
    
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
                
                # Get detected columns from session state
                detected_image_cols = st.session_state.get('detected_image_columns', [])
                detected_pdf_cols = st.session_state.get('detected_pdf_columns', [])
                
                # Process with detected columns
                output_df, flags, error = process_vendor_file(
                    df, 
                    mfg_prefix, 
                    brand_folder, 
                    sku_column_selected,
                    detected_image_cols=detected_image_cols,
                    detected_pdf_cols=detected_pdf_cols
                )
                
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

def process_vendor_file(df, mfg_prefix, brand_folder, sku_column, detected_image_cols=None, detected_pdf_cols=None):
    """
    Process vendor data following EXACT Belami Asset Template rules.
    
    Output columns (ONLY 6):
    - code: manufacturer_prefix_filename_postfix (all lowercase)
    - label-en_US: same as code
    - product_reference: full SKU
    - imagelink: full path with brand folder
    - assetFamilyIdentifier: main_product_image, media, spec_sheet, install_sheet
    - mediatype: lifestyle, dimension, detail, angle, informational, swatch (empty for main/spec/install)
    """
    
    if sku_column not in df.columns:
        return None, None, f"SKU column '{sku_column}' not found in the data"
    
    output_rows = []
    flags = []
    skipped_rows = []
    processed_skus = set()
    
    # Build mappings from detected columns
    image_mappings = {}
    if detected_image_cols:
        for col_def in detected_image_cols:
            col_name = col_def['column_name']
            category = col_def.get('category', 'media')
            image_mappings[col_name] = category
    
    pdf_mappings = {}
    if detected_pdf_cols:
        for col_def in detected_pdf_cols:
            col_name = col_def['column_name']
            category = col_def.get('category', 'document')
            pdf_mappings[col_name] = category
    
    main_count = 0
    media_count = 0
    spec_count = 0
    install_count = 0
    row_count = 0
    
    flags.append("=== BELAMI ASSET TEMPLATE GENERATION ===")
    flags.append(f"Manufacturer Prefix: {mfg_prefix}")
    flags.append(f"Brand Folder: {brand_folder}")
    flags.append(f"Image Columns Detected: {len(image_mappings)}")
    for col in image_mappings.keys():
        flags.append(f"  • {col}")
    flags.append(f"PDF Columns Detected: {len(pdf_mappings)}")
    for col in pdf_mappings.keys():
        flags.append(f"  • {col}")
    flags.append("")
    
    # Process each row
    for idx, row in df.iterrows():
        row_count += 1
        current_sku = None
        
        # Extract and validate SKU
        try:
            sku_value = row[sku_column]
            if pd.isna(sku_value):
                skipped_rows.append(f"Row {idx+1}: SKU is empty")
                continue
            
            current_sku = str(sku_value).strip()
            if not current_sku or current_sku.lower() == 'nan':
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
        
        # Process image columns
        first_image = True
        for col_name in image_mappings.keys():
            if col_name not in df.columns:
                continue
            
            try:
                img_value = row[col_name]
                if pd.isna(img_value) or str(img_value).strip() == '':
                    continue
                
                filename = str(img_value).strip()
                filename_lower = filename.lower()
                
                # Skip videos
                if any(ext in filename_lower for ext in ['.mp4', '.mov', '.avi', '.wmv']) or 'youtube' in filename_lower or 'vimeo' in filename_lower:
                    continue
                
                # Get file extension
                file_ext = Path(filename).suffix.lower()
                valid_image_ext = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg']
                
                if file_ext not in valid_image_ext:
                    continue
                
                # Get filename without extension (lowercase)
                base_name = Path(filename).stem.lower()
                
                # Clean filename (replace spaces/special chars with underscore)
                special_chars = [' ', ',', '/', '\\', '(', ')', '[', ']', '{', '}', '&', '#', '@', '!', '*', '+', '=', '%', '$', '^', '~', '`', ';', ':', '"', "'", '<', '>', '?', '|', '.']
                base_name_clean = base_name
                for char in special_chars:
                    base_name_clean = base_name_clean.replace(char, '_')
                
                # Remove multiple underscores
                while '__' in base_name_clean:
                    base_name_clean = base_name_clean.replace('__', '_')
                base_name_clean = base_name_clean.strip('_')
                
                # Determine asset type
                if first_image and image_mappings[col_name] != 'media_lifestyle':
                    # First image is main product image
                    asset_family = 'main_product_image'
                    media_type = ''
                    code = f"{mfg_prefix}_{base_name_clean}_new_1k"
                    imagelink = f"{brand_folder}/products/{base_name_clean}_new_1k.jpg"
                    main_count += 1
                    first_image = False
                else:
                    # Other images are media
                    asset_family = 'media'
                    
                    # Map category to mediatype
                    category = image_mappings[col_name]
                    if category == 'media_lifestyle':
                        media_type = 'lifestyle'
                    elif category == 'media_angle':
                        media_type = 'angle'
                    elif category == 'media_infographic':
                        media_type = 'informational'
                    elif category == 'media_dimension':
                        media_type = 'dimension'
                    elif category == 'media_swatch':
                        media_type = 'swatch'
                    else:
                        media_type = 'detail'
                    
                    code = f"{mfg_prefix}_{base_name_clean}_new_1k"
                    imagelink = f"{brand_folder}/media/{base_name_clean}_new_1k.jpg"
                    media_count += 1
                
                # Create row with ONLY 6 columns
                output_rows.append({
                    'code': code,
                    'label-en_US': code,
                    'product_reference': current_sku,
                    'imagelink': imagelink,
                    'assetFamilyIdentifier': asset_family,
                    'mediatype': media_type
                })
            
            except Exception as e:
                flags.append(f"Error processing image column {col_name} for SKU {current_sku}: {str(e)}")
                continue
        
        # Process PDF columns
        for col_name in pdf_mappings.keys():
            if col_name not in df.columns:
                continue
            
            try:
                pdf_value = row[col_name]
                if pd.isna(pdf_value) or str(pdf_value).strip() == '':
                    continue
                
                filename = str(pdf_value).strip()
                filename_lower = filename.lower()
                file_ext = Path(filename).suffix.lower()
                
                if file_ext != '.pdf':
                    continue
                
                # Get filename without extension (lowercase)
                base_name = Path(filename).stem.lower()
                
                # Clean filename
                special_chars = [' ', ',', '/', '\\', '(', ')', '[', ']', '{', '}', '&', '#', '@', '!', '*', '+', '=', '%', '$', '^', '~', '`', ';', ':', '"', "'", '<', '>', '?', '|', '.']
                base_name_clean = base_name
                for char in special_chars:
                    base_name_clean = base_name_clean.replace(char, '_')
                
                while '__' in base_name_clean:
                    base_name_clean = base_name_clean.replace('__', '_')
                base_name_clean = base_name_clean.strip('_')
                
                # Determine PDF type
                category = pdf_mappings[col_name]
                if category == 'install_sheet':
                    asset_family = 'install_sheet'
                    spec_type = 'install_sheet'
                    install_count += 1
                elif category == 'technical_drawing':
                    asset_family = 'spec_sheet'
                    spec_type = 'spec_sheet'
                    spec_count += 1
                else:
                    asset_family = 'spec_sheet'
                    spec_type = 'spec_sheet'
                    spec_count += 1
                
                code = f"{mfg_prefix}_{base_name_clean}_specs"
                imagelink = f"{brand_folder}/specsheets/{base_name_clean}_new.pdf"
                
                # Create row with ONLY 6 columns
                output_rows.append({
                    'code': code,
                    'label-en_US': code,
                    'product_reference': current_sku,
                    'imagelink': imagelink,
                    'assetFamilyIdentifier': asset_family,
                    'mediatype': ''
                })
            
            except Exception as e:
                flags.append(f"Error processing PDF column {col_name} for SKU {current_sku}: {str(e)}")
                continue
    
    # Generate summary
    flags.append("")
    flags.append("=== PROCESSING SUMMARY ===")
    flags.append(f"Total rows processed: {row_count}")
    flags.append(f"SKUs with assets: {len(processed_skus)}")
    flags.append(f"Total assets created: {len(output_rows)}")
    flags.append(f"  • Main product images: {main_count}")
    flags.append(f"  • Media assets: {media_count}")
    flags.append(f"  • Spec sheets: {spec_count}")
    flags.append(f"  • Install sheets: {install_count}")
    
    if skipped_rows:
        flags.append("")
        flags.append(f"=== SKIPPED ROWS ({len(skipped_rows)}) ===")
        for skip in skipped_rows[:15]:
            flags.append(skip)
        if len(skipped_rows) > 15:
            flags.append(f"... and {len(skipped_rows) - 15} more")
    
    # Create output DataFrame with ONLY 6 columns in correct order
    if output_rows:
        output_df = pd.DataFrame(output_rows)
        output_df = output_df[['code', 'label-en_US', 'product_reference', 'imagelink', 'assetFamilyIdentifier', 'mediatype']]
    else:
        output_df = pd.DataFrame(columns=['code', 'label-en_US', 'product_reference', 'imagelink', 'assetFamilyIdentifier', 'mediatype'])
    
    return output_df, "\n".join(flags), None


