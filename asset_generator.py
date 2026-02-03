import streamlit as st
import pandas as pd
import io
from pathlib import Path
import traceback


# ===========================================================================
# CONSTANTS
# ===========================================================================

IMAGE_EXTS  = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg'}
PDF_EXTS    = {'.pdf'}
VIDEO_EXTS  = {'.mp4', '.mov', '.avi', '.wmv', '.webm'}

# Keywords that point toward an image / PDF / video column.
# Detection checks the column NAME first; values are confirmed in step-2.
IMAGE_KEYWORDS = [
    'image', 'photo', 'picture', 'pic', 'img',
    'lifestyle', 'swatch', 'infographic', 'diagram',
    'sketch', 'dimensional', 'bb', 'b/b',
    'render', 'visual', 'asset', 'artwork',
    'gallery', 'thumbnail', 'file',
]
PDF_KEYWORDS = [
    'spec', 'sheet', 'install', 'assembly', 'instruction',
    'manual', 'guide', 'datasheet', 'specification',
    'document', 'catalog', 'brochure', 'dimmer',
    'warranty', 'care', 'energy', 'collection',
    'material', 'blueprint', 'drawing',
]
VIDEO_KEYWORDS = ['video', 'brand video']

# mediatype assigned based on keywords found in the column name
MEDIATYPE_MAP = {
    'lifestyle':     'lifestyle',
    'swatch':        'swatch',
    'infographic':   'informational',
    'diagram':       'dimension',
    'dimensional':   'dimension',
    'install':       '',            # PDF → empty mediatype
    'assembly':      '',
    'spec':          '',
    'sheet':         '',
}

# SKU column name candidates (compared case-insensitively)
SKU_CANDIDATES = [
    'sku', 'item number', 'item_number', 'item num', 'item_num',
    'model number', 'model_number', 'model no', 'model_no',
    'product code', 'product_code', 'product number', 'product_number',
    'part number', 'part_number', 'part no', 'part_no',
    'item code', 'item_code', 'article number', 'article_number',
    'catalog number', 'catalog_number', 'material number', 'material_number',
    'style number', 'style_number', 'style no', 'style_no',
    'upc', 'gtin', 'barcode', 'bar code',
    'product id', 'product_id', 'item id', 'item_id',
    'sku number', 'sku_number', 'sku no', 'sku_no',
    'reference', 'ref', 'identifier',
    'asin', 'mfg part', 'mfg_part', 'manufacturer part',
    'vendor sku', 'vendor_sku', 'supplier sku', 'supplier_sku',
]


# ===========================================================================
# HELPERS  (no regex, no .lower() on raw column objects)
# ===========================================================================

def _safe_lower(val) -> str:
    """Convert anything to a lowercased string safely."""
    return str(val).lower()


def _is_url_column(col_name: str) -> bool:
    """True for duplicate URL / Box-Link columns we want to skip."""
    n = col_name.upper()
    return 'URL' in n or n.startswith('BOX LINK')


def _clean_code(raw: str) -> str:
    """Lowercase + replace every non-alnum char with underscore, collapse runs."""
    out = []
    for ch in raw.lower():
        out.append(ch if (ch.isalnum() or ch == '_') else '_')
    result = ''.join(out)
    while '__' in result:
        result = result.replace('__', '_')
    return result.strip('_')


def _auto_detect_sku(columns: list) -> str:
    """Return first column name whose lowered form matches a SKU candidate."""
    lower_map = {_safe_lower(c): str(c) for c in columns}
    for cand in SKU_CANDIDATES:
        if cand in lower_map:
            return lower_map[cand]
    return ""


# ===========================================================================
# TWO-STEP AI COLUMN DETECTOR
# ===========================================================================

def detect_columns(df: pd.DataFrame) -> dict:
    """
    Two-step detection:
        Step 1 – keyword match on column NAME  →  candidate list
        Step 2 – scan actual cell VALUES for file extensions  →  confirm or reject

    Returns {
        'images':  [ {col, mediatype, confidence, sample}, … ],
        'pdfs':    [ … ],
        'videos':  [ … ],
        'skipped': [ (col, reason), … ]          # keyword hit but value check failed
    }
    """
    images, pdfs, videos, skipped = [], [], [], []

    for col in df.columns:
        col_str   = str(col)
        col_lower = _safe_lower(col)

        # ── skip URL / Box-Link duplicates immediately ────────────────────
        if _is_url_column(col_str):
            continue

        # ── STEP 1: keyword match on column name ──────────────────────────
        hit_image = any(kw in col_lower for kw in IMAGE_KEYWORDS)
        hit_pdf   = any(kw in col_lower for kw in PDF_KEYWORDS)
        hit_video = any(kw in col_lower for kw in VIDEO_KEYWORDS)

        if not (hit_image or hit_pdf or hit_video):
            continue          # no keyword match at all → skip silently

        # ── STEP 2: scan up to 30 actual values for extensions ────────────
        samples = df[col].dropna().astype(str).str.strip()
        samples = samples[samples != '']

        n_img, n_pdf, n_vid = 0, 0, 0
        for val in samples.head(30):
            ext = Path(val).suffix.lower()
            if ext in IMAGE_EXTS:  n_img += 1
            if ext in PDF_EXTS:    n_pdf += 1
            if ext in VIDEO_EXTS:  n_vid += 1

        total = len(samples)

        # ── decide final type  (values override name hints) ──────────────
        # e.g. "Spec Sheet Image" has image keyword but values are .pdf → PDF
        if n_pdf > 0 and n_img == 0 and n_vid == 0:
            final_type = 'pdf'
        elif n_vid > 0 and n_img == 0 and n_pdf == 0:
            final_type = 'video'
        elif n_img > 0:
            final_type = 'image'
        else:
            # keyword matched but ZERO file extensions in values → reject
            skipped.append((col_str, f"keyword hit but 0 file extensions in {total} values"))
            continue

        # ── confidence = % of sampled values that have a valid extension ──
        confirmed = n_img + n_pdf + n_vid
        confidence = round((confirmed / min(total, 30)) * 100, 1) if total else 0

        # ── determine mediatype from column name ──────────────────────────
        mediatype = 'detail'          # default for images
        if final_type in ('pdf', 'video'):
            mediatype = ''
        else:
            for kw, mt in MEDIATYPE_MAP.items():
                if kw in col_lower:
                    mediatype = mt
                    break
            # "Image File 1" with no other keyword → main_product_image for the first one
            # We mark it 'angle' here; the processing loop will upgrade row-0 to main.

        # ── pick first non-empty sample for preview ──────────────────────
        sample_val = str(samples.iloc[0])[:60] if total > 0 else ""

        entry = {
            'col':        col_str,
            'mediatype':  mediatype,
            'confidence': confidence,
            'sample':     sample_val,
            'total':      total,
        }

        if   final_type == 'image':  images.append(entry)
        elif final_type == 'pdf':    pdfs.append(entry)
        elif final_type == 'video':  videos.append(entry)

    # sort each list by confidence desc
    for lst in (images, pdfs, videos):
        lst.sort(key=lambda x: x['confidence'], reverse=True)

    return {'images': images, 'pdfs': pdfs, 'videos': videos, 'skipped': skipped}


# ===========================================================================
# PROCESSING  →  produces the 6-column Belami output
# ===========================================================================

def _process(df: pd.DataFrame,
             mfg_prefix: str,
             brand_folder: str,
             sku_col: str,
             image_cols: list,      # list of col-name strings the user confirmed
             pdf_cols: list,
             video_cols: list,
             col_mediatype: dict):  # {col_name: mediatype} — user can edit
    """
    Returns (output_df, log_text).
    output_df columns (in order):
        code | label-en_US | product_reference | imagelink | assetFamilyIdentifier | mediatype
    """
    log = []
    log.append("=== BELAMI ASSET TEMPLATE GENERATION LOG ===")
    log.append(f"Manufacturer Prefix : {mfg_prefix}")
    log.append(f"Brand Folder        : {brand_folder}")
    log.append(f"SKU Column          : {sku_col}")
    log.append(f"Image columns       : {image_cols}")
    log.append(f"PDF columns         : {pdf_cols}")
    log.append(f"Video columns       : {video_cols}")
    log.append("")

    # ── resolve SKU column (case-insensitive fallback) ────────────────────
    col_lower_map = {_safe_lower(c): str(c) for c in df.columns}
    actual_sku = sku_col if sku_col in df.columns else col_lower_map.get(_safe_lower(sku_col))
    if actual_sku is None:
        log.append(f"ERROR: SKU column '{sku_col}' not found.")
        return None, "\n".join(log)

    rows_out = []
    seen_codes = set()
    skipped_rows = []

    # ── track whether we have already output a main_product_image per SKU ─
    # "Image File 1" (or whatever the first image column is) becomes main for each SKU.
    # Everything else is media.

    for row_idx, row in df.iterrows():
        # ── SKU ────────────────────────────────────────────────────────────
        raw_sku = row[actual_sku]
        if pd.isna(raw_sku) or str(raw_sku).strip() == '':
            skipped_rows.append(f"Row {row_idx + 2}: empty SKU")
            continue
        sku = str(raw_sku).strip()
        product_ref = f"{mfg_prefix}_{sku}"

        main_done = False      # reset per SKU

        # ── IMAGE columns ─────────────────────────────────────────────────
        for col in image_cols:
            if col not in df.columns:
                continue
            cell = row[col]
            if pd.isna(cell) or str(cell).strip() == '':
                continue

            filename = str(cell).strip()
            stem     = Path(filename).stem          # original case
            ext      = Path(filename).suffix.lower()
            if ext not in IMAGE_EXTS:
                continue                            # safety: skip non-image values

            code = f"{mfg_prefix}_{_clean_code(stem)}_new_1k"
            if code in seen_codes:
                continue
            seen_codes.add(code)

            # first image per SKU → main_product_image / products/
            if not main_done:
                fam    = 'main_product_image'
                folder = 'products'
                mtype  = ''
                main_done = True
            else:
                fam    = 'media'
                folder = 'media'
                mtype  = col_mediatype.get(col, 'detail')

            rows_out.append({
                'code':                   code,
                'label-en_US':            code,
                'product_reference':      product_ref,
                'imagelink':              f"{brand_folder}/{folder}/{stem}_new_1k.jpg",
                'assetFamilyIdentifier':  fam,
                'mediatype':              mtype,
            })

        # ── PDF columns ───────────────────────────────────────────────────
        for col in pdf_cols:
            if col not in df.columns:
                continue
            cell = row[col]
            if pd.isna(cell) or str(cell).strip() == '':
                continue

            filename = str(cell).strip()
            stem     = Path(filename).stem
            ext      = Path(filename).suffix.lower()
            if ext not in PDF_EXTS:
                continue

            code = f"{mfg_prefix}_{_clean_code(stem)}_specs"
            if code in seen_codes:
                continue
            seen_codes.add(code)

            # install vs spec: if "install" or "assembly" in column name → install_sheet
            col_lower = _safe_lower(col)
            if 'install' in col_lower or 'assembly' in col_lower:
                fam = 'install_sheet'
            else:
                fam = 'spec_sheet'

            rows_out.append({
                'code':                   code,
                'label-en_US':            code,
                'product_reference':      product_ref,
                'imagelink':              f"{brand_folder}/specsheets/{stem}_new.pdf",
                'assetFamilyIdentifier':  fam,
                'mediatype':              '',
            })

        # ── VIDEO columns ─────────────────────────────────────────────────
        for col in video_cols:
            if col not in df.columns:
                continue
            cell = row[col]
            if pd.isna(cell) or str(cell).strip() == '':
                continue

            filename = str(cell).strip()
            stem     = Path(filename).stem
            ext      = Path(filename).suffix.lower()
            if ext not in VIDEO_EXTS:
                continue

            code = f"{mfg_prefix}_{_clean_code(stem)}"
            if code in seen_codes:
                continue          # brand video repeats every row – only once
            seen_codes.add(code)

            rows_out.append({
                'code':                   code,
                'label-en_US':            code,
                'product_reference':      product_ref,
                'imagelink':              f"{brand_folder}/media/{filename}",
                'assetFamilyIdentifier':  'media',
                'mediatype':              'detail',
            })

    # ── build output ──────────────────────────────────────────────────────
    COLS = ['code', 'label-en_US', 'product_reference', 'imagelink',
            'assetFamilyIdentifier', 'mediatype']
    output_df = pd.DataFrame(rows_out, columns=COLS) if rows_out else pd.DataFrame(columns=COLS)

    # ── summary ───────────────────────────────────────────────────────────
    log.append("=== SUMMARY ===")
    log.append(f"Total asset rows      : {len(output_df)}")
    log.append(f"  main_product_image  : {int((output_df['assetFamilyIdentifier'] == 'main_product_image').sum())}")
    log.append(f"  media               : {int((output_df['assetFamilyIdentifier'] == 'media').sum())}")
    log.append(f"  spec_sheet          : {int((output_df['assetFamilyIdentifier'] == 'spec_sheet').sum())}")
    log.append(f"  install_sheet       : {int((output_df['assetFamilyIdentifier'] == 'install_sheet').sum())}")
    if skipped_rows:
        log.append(f"\nSkipped ({len(skipped_rows)}):")
        for s in skipped_rows[:20]:
            log.append(f"  {s}")
        if len(skipped_rows) > 20:
            log.append(f"  … and {len(skipped_rows) - 20} more")

    return output_df, "\n".join(log)


# ===========================================================================
# STREAMLIT UI
# ===========================================================================

def show():
    st.markdown('<div class="title">Asset Template Generator</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Two-step AI detection + manual fallback</div>', unsafe_allow_html=True)

    # ── manufacturer list ─────────────────────────────────────────────────
    @st.cache_data
    def _load_mfg():
        try:
            mdf = pd.read_excel("Manufacturer_ID_s.xlsx")
            mapping = dict(zip(mdf["Brand"].str.strip(), mdf["Manu ID"].astype(str)))
            return mapping, sorted(mdf["Brand"].str.strip().tolist())
        except Exception:
            return {}, []

    mfg_mapping, vendor_list = _load_mfg()

    # ── session-state keys ────────────────────────────────────────────────
    for k in ('selected_sheet', 'header_row',
              'det_images', 'det_pdfs', 'det_videos', 'det_skipped'):
        if k not in st.session_state:
            st.session_state[k] = None

    # ══════════════════════════════════════════════════════════════════════
    # 1  CONFIGURATION
    # ══════════════════════════════════════════════════════════════════════
    st.markdown("### Configuration")
    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    with c1:
        vendor_name = st.selectbox("Vendor Name", [""] + vendor_list) if vendor_list else st.text_input("Vendor Name")
    with c2:
        mfg_prefix = st.text_input("Manufacturer ID",
                                   value=mfg_mapping.get(vendor_name, "") if vendor_name else "",
                                   placeholder="2605")
    with c3:
        brand_folder = st.text_input("Brand Folder",
                                     value=vendor_name.lower().replace(" ", "") if vendor_name else "",
                                     placeholder="afx")

    # ══════════════════════════════════════════════════════════════════════
    # 2  UPLOAD
    # ══════════════════════════════════════════════════════════════════════
    st.markdown("### Upload Files")
    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        vendor_file = st.file_uploader("Vendor Data File", type=["xlsx", "xls"])
    with c2:
        template_file = st.file_uploader("Asset Template (empty)", type=["xlsx"])

    # ══════════════════════════════════════════════════════════════════════
    # 3  SHEET SELECTOR
    # ══════════════════════════════════════════════════════════════════════
    selected_sheet = None
    if vendor_file:
        try:
            xls    = pd.ExcelFile(vendor_file)
            sheets = xls.sheet_names
            if len(sheets) > 1:
                st.markdown("---")
                st.markdown("### Select Sheet")
                cols = st.columns(min(len(sheets), 5))
                for i, s in enumerate(sheets):
                    with cols[i % 5]:
                        t = "primary" if st.session_state.selected_sheet == s else "secondary"
                        if st.button(s, key=f"sh_{i}", use_container_width=True, type=t):
                            st.session_state.selected_sheet = s
                            st.session_state.header_row     = None
                            st.session_state.det_images     = None   # reset detection
                            st.session_state.det_pdfs       = None
                            st.session_state.det_videos     = None
                            st.rerun()
                if st.session_state.selected_sheet:
                    selected_sheet = st.session_state.selected_sheet
                    st.success(f"Selected: {selected_sheet}")
            else:
                selected_sheet = sheets[0]
                st.session_state.selected_sheet = selected_sheet
        except Exception as e:
            st.error(str(e))

    # ══════════════════════════════════════════════════════════════════════
    # 4  HEADER ROW PICKER
    # ══════════════════════════════════════════════════════════════════════
    header_row = None       # 0-based
    if vendor_file and selected_sheet:
        st.markdown("---")
        st.markdown("### Select Header Row")
        try:
            preview = pd.read_excel(vendor_file, sheet_name=selected_sheet, header=None, nrows=5)
            st.dataframe(preview, use_container_width=True)
        except Exception:
            pass

        pick = st.selectbox("Which row has column names?",
                            list(range(1, 6)),
                            format_func=lambda x: f"Row {x}",
                            index=1, key="hdr_pick")
        header_row = pick - 1
        st.session_state.header_row = header_row

    # ══════════════════════════════════════════════════════════════════════
    # 5  SKU COLUMN  (auto-detect + dropdown + manual)
    # ══════════════════════════════════════════════════════════════════════
    sku_col = None
    all_columns = []        # kept for manual fallback later

    if vendor_file and selected_sheet and header_row is not None:
        st.markdown("---")
        st.markdown("### Select SKU Column")
        try:
            tmp        = pd.read_excel(vendor_file, sheet_name=selected_sheet,
                                       header=header_row, nrows=0)
            all_columns = [str(c) for c in tmp.columns]
            auto_sku   = _auto_detect_sku(all_columns)

            if auto_sku:
                st.success(f"Auto-detected SKU column: **{auto_sku}**")

            c1, c2 = st.columns(2)
            with c1:
                default_idx = (all_columns.index(auto_sku) + 1) if auto_sku in all_columns else 0
                sku_col = st.selectbox("Pick from file columns",
                                       ["-- select --"] + all_columns,
                                       index=default_idx)
                if sku_col == "-- select --":
                    sku_col = None
            with c2:
                manual_sku = st.text_input("Or type column name", placeholder="e.g. Model Number")
                if manual_sku.strip():
                    sku_col = manual_sku.strip()

            if sku_col:
                st.info(f"Using SKU column: **{sku_col}**")
        except Exception as e:
            st.error(str(e))

    # ══════════════════════════════════════════════════════════════════════
    # 6  TWO-STEP AI DETECTION  +  MANUAL FALLBACK
    # ══════════════════════════════════════════════════════════════════════
    # These hold the FINAL confirmed column lists that go to _process()
    final_image_cols  = []
    final_pdf_cols    = []
    final_video_cols  = []
    col_mediatype     = {}      # {col_name: mediatype} – user can edit

    if vendor_file and selected_sheet and header_row is not None:
        st.markdown("---")
        st.markdown("### AI Column Detection")

        try:
            full_df = pd.read_excel(vendor_file, sheet_name=selected_sheet, header=header_row)

            # ── run detector ──────────────────────────────────────────────
            det = detect_columns(full_df)
            st.session_state.det_images  = det['images']
            st.session_state.det_pdfs    = det['pdfs']
            st.session_state.det_videos  = det['videos']
            st.session_state.det_skipped = det['skipped']

            # ── summary metrics ───────────────────────────────────────────
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.metric("Images detected",  len(det['images']))
            with c2: st.metric("PDFs detected",    len(det['pdfs']))
            with c3: st.metric("Videos detected",  len(det['videos']))
            with c4: st.metric("Rejected (no files)", len(det['skipped']))

            # ──────────────────────────────────────────────────────────────
            # IMAGE columns – checkboxes to keep/remove + mediatype editor
            # ──────────────────────────────────────────────────────────────
            if det['images']:
                st.markdown("#### Detected Image Columns")
                st.markdown("Uncheck any column you do **not** want. You can also change the mediatype.")

                MTYPE_OPTIONS = ['lifestyle', 'angle', 'informational', 'dimension', 'swatch', 'detail']

                for entry in det['images']:
                    col_name = entry['col']
                    c1, c2, c3 = st.columns([1, 2, 3])
                    with c1:
                        keep = st.checkbox(col_name, value=True, key=f"keep_img_{col_name}")
                    with c2:
                        mtype = st.selectbox("mediatype",
                                             MTYPE_OPTIONS,
                                             index=MTYPE_OPTIONS.index(entry['mediatype']) if entry['mediatype'] in MTYPE_OPTIONS else 5,
                                             key=f"mtype_{col_name}",
                                             label_visibility="hidden")
                    with c3:
                        st.caption(f"{entry['confidence']}% confidence | {entry['total']} values | e.g. {entry['sample']}")

                    if keep:
                        final_image_cols.append(col_name)
                        col_mediatype[col_name] = mtype

            # ──────────────────────────────────────────────────────────────
            # PDF columns
            # ──────────────────────────────────────────────────────────────
            if det['pdfs']:
                st.markdown("#### Detected PDF Columns")
                for entry in det['pdfs']:
                    col_name = entry['col']
                    c1, c2 = st.columns([1, 3])
                    with c1:
                        keep = st.checkbox(col_name, value=True, key=f"keep_pdf_{col_name}")
                    with c2:
                        st.caption(f"{entry['confidence']}% confidence | {entry['total']} values | e.g. {entry['sample']}")
                    if keep:
                        final_pdf_cols.append(col_name)

            # ──────────────────────────────────────────────────────────────
            # VIDEO columns
            # ──────────────────────────────────────────────────────────────
            if det['videos']:
                st.markdown("#### Detected Video Columns")
                for entry in det['videos']:
                    col_name = entry['col']
                    c1, c2 = st.columns([1, 3])
                    with c1:
                        keep = st.checkbox(col_name, value=True, key=f"keep_vid_{col_name}")
                    with c2:
                        st.caption(f"{entry['confidence']}% confidence | {entry['total']} values | e.g. {entry['sample']}")
                    if keep:
                        final_video_cols.append(col_name)

            # ──────────────────────────────────────────────────────────────
            # MANUAL FALLBACK  – dropdown for columns AI didn't pick
            # ──────────────────────────────────────────────────────────────
            already_picked = set(final_image_cols + final_pdf_cols + final_video_cols)
            remaining = [c for c in all_columns if c not in already_picked and not _is_url_column(c)]

            if remaining:
                st.markdown("---")
                st.markdown("#### Add Columns Manually (AI did not pick these)")
                st.caption("If you know a column has images or PDFs but the AI missed it, add it here.")

                c1, c2, c3 = st.columns(3)
                with c1:
                    add_img = st.multiselect("Add as IMAGE columns", remaining, key="manual_img")
                    final_image_cols.extend(add_img)
                    for c in add_img:
                        col_mediatype[c] = 'detail'   # default; user can change above if re-run

                with c2:
                    add_pdf = st.multiselect("Add as PDF columns",
                                            [c for c in remaining if c not in add_img],
                                            key="manual_pdf")
                    final_pdf_cols.extend(add_pdf)

                with c3:
                    add_vid = st.multiselect("Add as VIDEO columns",
                                            [c for c in remaining if c not in add_img and c not in add_pdf],
                                            key="manual_vid")
                    final_video_cols.extend(add_vid)

            # ──────────────────────────────────────────────────────────────
            # Show what was rejected and why (expandable)
            # ──────────────────────────────────────────────────────────────
            if det['skipped']:
                with st.expander(f"Rejected columns ({len(det['skipped'])}) – keyword matched but no file extensions in values"):
                    for col_name, reason in det['skipped']:
                        st.write(f"  {col_name} — {reason}")

        except Exception as e:
            st.error(str(e))
            st.code(traceback.format_exc())

    # ══════════════════════════════════════════════════════════════════════
    # 7  STATUS BAR
    # ══════════════════════════════════════════════════════════════════════
    st.markdown("---")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: (st.success if (vendor_name and mfg_prefix and brand_folder) else st.warning)("Config")
    with c2: (st.success if vendor_file   else st.warning)("File")
    with c3: (st.success if selected_sheet else st.warning)("Sheet")
    with c4: (st.success if sku_col        else st.warning)("SKU Col")
    with c5: (st.success if (final_image_cols or final_pdf_cols or final_video_cols) else st.warning)("Columns")

    # ══════════════════════════════════════════════════════════════════════
    # 8  GENERATE
    # ══════════════════════════════════════════════════════════════════════
    st.markdown("---")
    has_cols = bool(final_image_cols or final_pdf_cols or final_video_cols)
    ready    = all([vendor_file, template_file, vendor_name, mfg_prefix,
                    brand_folder, selected_sheet, sku_col, header_row is not None, has_cols])

    if not ready:
        missing = []
        if not vendor_file:      missing.append("Vendor file")
        if not template_file:    missing.append("Template file")
        if not vendor_name:      missing.append("Vendor name")
        if not mfg_prefix:       missing.append("Manufacturer ID")
        if not brand_folder:     missing.append("Brand folder")
        if not selected_sheet:   missing.append("Sheet")
        if not sku_col:          missing.append("SKU column")
        if not has_cols:         missing.append("At least one image/PDF/video column")
        if missing:
            st.warning("Still needed: " + ", ".join(missing))

    if st.button("Generate Asset Template", disabled=not ready,
                 use_container_width=True, type="primary"):
        with st.spinner("Processing …"):
            try:
                df = pd.read_excel(vendor_file, sheet_name=selected_sheet, header=header_row)
                st.info(f"Read {len(df)} rows | sheet = {selected_sheet} | header = row {header_row + 1}")

                output_df, log_text = _process(
                    df, mfg_prefix, brand_folder, sku_col,
                    final_image_cols, final_pdf_cols, final_video_cols, col_mediatype
                )

                if output_df is None or len(output_df) == 0:
                    st.error("No assets generated. Check the log below.")
                    st.text(log_text)
                else:
                    st.success(f"Generated {len(output_df)} asset rows")

                    # metrics
                    c1, c2, c3, c4 = st.columns(4)
                    with c1: st.metric("Total",          len(output_df))
                    with c2: st.metric("Main Images",    int((output_df['assetFamilyIdentifier'] == 'main_product_image').sum()))
                    with c3: st.metric("Media + Videos", int((output_df['assetFamilyIdentifier'] == 'media').sum()))
                    with c4: st.metric("PDFs",           int(output_df['assetFamilyIdentifier'].isin(['spec_sheet','install_sheet']).sum()))

                    with st.expander("Preview (first 25 rows)"):
                        st.dataframe(output_df.head(25), use_container_width=True)

                    # downloads
                    st.markdown("---")
                    c1, c2 = st.columns(2)
                    with c1:
                        buf = io.BytesIO()
                        with pd.ExcelWriter(buf, engine="openpyxl") as w:
                            output_df.to_excel(w, sheet_name="Sheet1", index=False)
                        buf.seek(0)
                        st.download_button("Download Asset Template",
                                           data=buf,
                                           file_name=f"{vendor_name}_Asset_Template.xlsx",
                                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                           use_container_width=True, type="primary")
                    with c2:
                        st.download_button("Download Processing Log",
                                           data=log_text,
                                           file_name=f"{vendor_name}_log.txt",
                                           mime="text/plain",
                                           use_container_width=True)
            except Exception as e:
                st.error(str(e))
                st.code(traceback.format_exc())
