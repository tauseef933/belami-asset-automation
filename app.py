import streamlit as st
import pandas as pd
import io
from datetime import datetime
from pathlib import Path
import traceback
import re

# Page config
st.set_page_config(
    page_title="Belami Asset Automation",
    page_icon="⚡",
    layout="wide"
)

# Beautiful CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

* { font-family: 'Inter', sans-serif; }

.main {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 1.5rem 1rem;
}

.block-container {
    background: white;
    border-radius: 20px;
    padding: 2rem;
    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
    max-width: 1400px;
}

.title {
    font-size: 2.5rem;
    font-weight: 700;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-align: center;
    margin-bottom: 0.5rem;
}

.subtitle {
    text-align: center;
    color: #6b7280;
    margin-bottom: 2rem;
}

.card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 15px;
    padding: 1.5rem;
    color: white;
    margin-bottom: 1.5rem;
}

.card-title {
    font-size: 1.2rem;
    font-weight: 600;
    margin-bottom: 1rem;
}

.stButton>button {
    width: 100%;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    font-weight: 600;
    padding: 0.75rem;
    border-radius: 10px;
    border: none;
    transition: all 0.3s;
}

.stButton>button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

.stDownloadButton>button {
    background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
}

.metric {
    background: #f9fafb;
    border-radius: 10px;
    padding: 1.5rem;
    text-align: center;
    border: 2px solid #e5e7eb;
}

.metric-value {
    font-size: 2rem;
    font-weight: 700;
    color: #667eea;
}

.metric-label {
    color: #6b7280;
    font-size: 0.9rem;
    margin-top: 0.5rem;
}

.status-badge {
    display: inline-block;
    padding: 0.4rem 0.8rem;
    border-radius: 15px;
    font-weight: 600;
    font-size: 0.85rem;
    margin: 0.2rem;
}

.status-success { background: #d1fae5; color: #065f46; }
.status-warning { background: #fef3c7; color: #92400e; }

@media (max-width: 768px) {
    .title { font-size: 1.8rem; }
    .block-container { padding: 1rem; }
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_manufacturer_mapping():
    try:
        df = pd.read_excel('Manufacturer_ID_s.xlsx')
        mapping = dict(zip(df['Brand'].str.lower().str.strip(), df['Manu ID'].astype(str)))
        return mapping
    except:
        return {}

def process_vendor_file(df, mfg_prefix, brand_folder):
    """Process vendor data to create asset template"""
    
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
        current_sku = str(row['SKU']) if pd.notna(row['SKU']) else None
        
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
            
            # Create code (lowercase, cleaned)
            code_clean = base_name.lower()
            code_clean = re.sub(r'[^a-z0-9_-]', '_', code_clean)
            
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
    
    flags.insert(0, f"✓ Main images: {main_count}")
    flags.insert(1, f"✓ Media images: {media_count}")
    flags.insert(2, f"✓ PDFs: {pdf_count}")
    flags.insert(3, f"✓ Total assets: {len(output_df)}")
    
    return output_df, "\n".join(flags), None

# UI
st.markdown('<div class="title">⚡ Belami Asset Automation</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Professional asset template generator</div>', unsafe_allow_html=True)

# Load mapping
mfg_mapping = load_manufacturer_mapping()

# Initialize session state
if 'sheet_selected' not in st.session_state:
    st.session_state.sheet_selected = False
if 'selected_sheet' not in st.session_state:
    st.session_state.selected_sheet = None

# Config card
st.markdown('<div class="card"><div class="card-title">⚙️ Configuration</div></div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    vendor_name = st.text_input("Vendor Name", placeholder="AFX")

with col2:
    suggested = mfg_mapping.get(vendor_name.lower().strip(), "") if vendor_name else ""
    mfg_prefix = st.text_input("Manufacturer ID", value=suggested, placeholder="2605")

with col3:
    brand_folder = st.text_input("Brand Folder", value=vendor_name.lower().replace(' ', '') if vendor_name else "", placeholder="afx")

# Upload card
st.markdown('<div class="card"><div class="card-title">📤 Upload Files</div></div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    vendor_file = st.file_uploader("Vendor Data File", type=['xlsx', 'xls'], key="vendor")

with col2:
    template_file = st.file_uploader("Asset Template", type=['xlsx'], key="template")

# Sheet selection
selected_sheet = None
if vendor_file:
    try:
        excel_file = pd.ExcelFile(vendor_file)
        sheets = excel_file.sheet_names
        
        if len(sheets) > 1:
            st.markdown("---")
            st.markdown("### 📋 Select Sheet")
            
            cols = st.columns(min(len(sheets), 5))
            for idx, sheet in enumerate(sheets):
                with cols[idx % 5]:
                    button_type = "primary" if st.session_state.selected_sheet == sheet else "secondary"
                    if st.button(sheet, key=f"sheet_{idx}", use_container_width=True, type=button_type):
                        st.session_state.selected_sheet = sheet
                        st.rerun()
            
            if st.session_state.selected_sheet:
                selected_sheet = st.session_state.selected_sheet
                st.success(f"✓ Using: **{selected_sheet}**")
        else:
            selected_sheet = sheets[0]
            st.session_state.selected_sheet = selected_sheet
    except Exception as e:
        st.error(f"Error reading file: {e}")

# Status
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)

with col1:
    if vendor_name and mfg_prefix and brand_folder:
        st.markdown('<span class="status-badge status-success">✓ Config</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-badge status-warning">⚠ Config</span>', unsafe_allow_html=True)

with col2:
    if vendor_file:
        st.markdown('<span class="status-badge status-success">✓ Vendor File</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-badge status-warning">⚠ Vendor</span>', unsafe_allow_html=True)

with col3:
    if selected_sheet:
        st.markdown('<span class="status-badge status-success">✓ Sheet</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-badge status-warning">⚠ Sheet</span>', unsafe_allow_html=True)

with col4:
    if template_file:
        st.markdown('<span class="status-badge status-success">✓ Template</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-badge status-warning">⚠ Template</span>', unsafe_allow_html=True)

# Process
st.markdown("---")
can_process = all([vendor_file, template_file, vendor_name, mfg_prefix, brand_folder, selected_sheet])

if st.button("⚡ Generate Asset Template", disabled=not can_process, use_container_width=True):
    with st.spinner("Processing..."):
        try:
            # Read vendor data (skip first row, use second row as header)
            df = pd.read_excel(vendor_file, sheet_name=selected_sheet, header=1)
            
            st.info(f"Processing {len(df)} rows from sheet: {selected_sheet}")
            
            # Process
            output_df, flags, error = process_vendor_file(df, mfg_prefix, brand_folder)
            
            if error:
                st.error(error)
            else:
                st.balloons()
                st.success(f"🎉 Created **{len(output_df)}** assets!")
                
                # Metrics
                st.markdown("---")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown(f'<div class="metric"><div class="metric-value">{len(output_df)}</div><div class="metric-label">Total Assets</div></div>', unsafe_allow_html=True)
                
                with col2:
                    main = len(output_df[output_df['assetFamilyIdentifier'] == 'main_product_image'])
                    st.markdown(f'<div class="metric"><div class="metric-value">{main}</div><div class="metric-label">Main Images</div></div>', unsafe_allow_html=True)
                
                with col3:
                    media = len(output_df[output_df['assetFamilyIdentifier'] == 'media'])
                    st.markdown(f'<div class="metric"><div class="metric-value">{media}</div><div class="metric-label">Media</div></div>', unsafe_allow_html=True)
                
                with col4:
                    pdfs = len(output_df[output_df['assetFamilyIdentifier'].isin(['spec_sheet', 'install_sheet'])])
                    st.markdown(f'<div class="metric"><div class="metric-value">{pdfs}</div><div class="metric-label">PDFs</div></div>', unsafe_allow_html=True)
                
                # Preview
                with st.expander("📋 Preview Data"):
                    st.dataframe(output_df.head(20), use_container_width=True)
                
                # Download
                st.markdown("---")
                col1, col2 = st.columns(2)
                
                with col1:
                    output_excel = io.BytesIO()
                    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
                        output_df.to_excel(writer, sheet_name='Sheet1', index=False)
                    output_excel.seek(0)
                    
                    st.download_button(
                        "📥 Download Asset Template",
                        data=output_excel,
                        file_name=f"{vendor_name}_Asset_Template.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                
                with col2:
                    log = f"Processing Log - {vendor_name}\n{'='*50}\n{flags}"
                    st.download_button(
                        "📄 Download Log",
                        data=log,
                        file_name=f"{vendor_name}_log.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
        
        except Exception as e:
            st.error(f"Error: {e}")
            st.code(traceback.format_exc())

st.markdown("---")
st.markdown('<div style="text-align:center;color:#9ca3af;">Belami Asset Automation v2.0</div>', unsafe_allow_html=True)
