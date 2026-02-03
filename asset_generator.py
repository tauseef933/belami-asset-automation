import streamlit as st
import pandas as pd
import io
from pathlib import Path
import traceback


# ---------------------------------------------------------------------------
# EXACT column-to-output mapping derived from your filled template.
# Key:   column name as it appears in vendor files (the "filename" columns,
#        NOT the duplicate "URL" columns).
# Value: (assetFamilyIdentifier, folder, mediatype)
#        folder  -> products | media | specsheets
#        mediatype -> lifestyle | angle | informational | dimension | swatch | detail | "" (empty)
# ---------------------------------------------------------------------------
KNOWN_IMAGE_COLUMNS = {
    # ── main product image ────────────────────────────────────────────────
    "Image File 1":                        ("main_product_image", "products",    ""),

    # ── additional product angles ─────────────────────────────────────────
    "Image File 2":                        ("media", "media", "angle"),
    "Image File 3":                        ("media", "media", "angle"),

    # ── lifestyle / application shots ─────────────────────────────────────
    "Lifestyle Image 1":                   ("media", "media", "lifestyle"),
    "Lifestyle Image 2":                   ("media", "media", "lifestyle"),
    "Lifestyle Image 3":                   ("media", "media", "lifestyle"),

    # ── box / beauty shots ────────────────────────────────────────────────
    "B/B Image 1":                         ("media", "media", "angle"),
    "B/B Image 2":                         ("media", "media", "angle"),
    "B/B Image 3":                         ("media", "media", "angle"),
    "B/B Image Dimensional":               ("media", "media", "dimension"),

    # ── swatch images ─────────────────────────────────────────────────────
    "Swatch Image 1":                      ("media", "media", "swatch"),
    "Swatch Image 2":                      ("media", "media", "swatch"),
    "Swatch Image 3":                      ("media", "media", "swatch"),
    "Swatch Image 4":                      ("media", "media", "swatch"),

    # ── infographics ──────────────────────────────────────────────────────
    "Infographic Image 1":                 ("media", "media", "informational"),
    "Infographic Image 2":                 ("media", "media", "informational"),
    "Infographic Image 3":                 ("media", "media", "informational"),
    "Infographic Image 4":                 ("media", "media", "informational"),
    "Infographic Image 5":                 ("media", "media", "informational"),
    "Infographic Image 6":                 ("media", "media", "informational"),
    "Infographic Image 7":                 ("media", "media", "informational"),
    "Infographic Image 8":                 ("media", "media", "informational"),
    "Infographic Image 9":                 ("media", "media", "informational"),
    "Infographic Image 10":                ("media", "media", "informational"),
    "Infographic Image 11":                ("media", "media", "informational"),
    "Infographic Image 12":                ("media", "media", "informational"),

    # ── diagrams / dimensions ─────────────────────────────────────────────
    "Diagram Image 1":                     ("media", "media", "dimension"),
    "Diagram Image 2":                     ("media", "media", "dimension"),
    "Diagram Image 3":                     ("media", "media", "dimension"),
    "Diagram Image 4":                     ("media", "media", "dimension"),

    # ── sketches ──────────────────────────────────────────────────────────
    "Sketch Image":                        ("media", "media", "detail"),

    # ── 3-D renders ───────────────────────────────────────────────────────
    "3 Dimensional Image 1":               ("media", "media", "detail"),
    "3 Dimensional Image 2":               ("media", "media", "detail"),
    "3 Dimensional Image 3":               ("media", "media", "detail"),
    "3 Dimensional Image 4":               ("media", "media", "detail"),
    "3 Dimensional Image 5":               ("media", "media", "detail"),
    "3 Dimensional Image 6":               ("media", "media", "detail"),
    "3 Dimensional Image 7":               ("media", "media", "detail"),
    "3 Dimensional Image 8":               ("media", "media", "detail"),
    "3 Dimensional Image 9":               ("media", "media", "detail"),

    # ── spec / install PDFs ───────────────────────────────────────────────
    "Spec Sheet Image":                    ("spec_sheet",   "specsheets", ""),
    "Installation/Assembly Image 1":       ("install_sheet","specsheets", ""),
    "Installation/Assembly Image 2":       ("install_sheet","specsheets", ""),
    "Installation/Assembly Image 3":       ("install_sheet","specsheets", ""),

    # ── collection / care / energy / material / dimmer / warranty ─────────
    "Collection Image":                    ("media", "media", "detail"),
    "Care Guide Image":                    ("media", "media", "detail"),
    "Energy Label Image":                  ("media", "media", "detail"),
    "Collection Spec Sheet Image 1":       ("spec_sheet",   "specsheets", ""),
    "Material Statements Image 1":         ("media", "media", "detail"),
    "Material Statements Image 2":         ("media", "media", "detail"),
    "Dimmer Sheet Image":                  ("spec_sheet",   "specsheets", ""),
    "Warranty Image 1":                    ("media", "media", "detail"),
    "Warranty Image 2":                    ("media", "media", "detail"),

    # ── brand / product videos (kept as-is, no _new_1k) ──────────────────
    "Video 1":                             ("media", "media", "detail"),
    "Video 2":                             ("media", "media", "detail"),
    "Video 3":                             ("media", "media", "detail"),
    "Brand Video 1":                       ("media", "media", "detail"),
}

# ---------------------------------------------------------------------------
# All plausible names a vendor might use for the SKU / product-id column.
# Detection is case-insensitive.  User can also type a custom name.
# ---------------------------------------------------------------------------
SKU_COLUMN_CANDIDATES = [
    "sku", "item number", "item_number", "item num", "item_num",
    "model number", "model_number", "model no", "model_no",
    "product code", "product_code", "product number", "product_number",
    "part number", "part_number", "part no", "part_no",
    "item code", "item_code", "article number", "article_number",
    "catalog number", "catalog_number", "material number", "material_number",
    "style number", "style_number", "style no", "style_no",
    "upc", "gtin", "barcode", "bar code",
    "product id", "product_id", "item id", "item_id",
    "sku number", "sku_number", "sku no", "sku_no",
    "reference", "ref", "code", "identifier",
    "asin", "mfg part", "mfg_part", "manufacturer part",
    "vendor sku", "vendor_sku", "supplier sku", "supplier_sku",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _clean_code(raw_name: str) -> str:
    """Lowercase + replace every non-alphanumeric char with underscore, collapse runs."""
    out = []
    for ch in raw_name.lower():
        if ch.isalnum() or ch == '_':
            out.append(ch)
        else:
            out.append('_')
    result = ''.join(out)
    # collapse multiple underscores
    while '__' in result:
        result = result.replace('__', '_')
    return result.strip('_')


def _is_video(filename: str) -> bool:
    ext = Path(filename).suffix.lower()
    return ext in ('.mp4', '.mov', '.avi', '.wmv', '.webm') or 'youtube' in filename.lower() or 'vimeo' in filename.lower()


def _is_pdf(filename: str) -> bool:
    return Path(filename).suffix.lower() == '.pdf'


def _auto_detect_sku(columns: list) -> str:
    """Return the first column whose lowered name matches a known SKU candidate, or empty string."""
    col_lower_map = {str(c).lower(): str(c) for c in columns}
    for candidate in SKU_COLUMN_CANDIDATES:
        if candidate in col_lower_map:
            return col_lower_map[candidate]
    return ""


def _columns_present(df, known_map: dict) -> list:
    """Return only the keys from known_map that actually exist in df.columns."""
    df_cols = set(str(c) for c in df.columns)
    return [k for k in known_map if k in df_cols]


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
def show():
    st.markdown('<div class="title">Asset Template Generator</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Generates Belami-compliant asset templates from any vendor file</div>', unsafe_allow_html=True)

    # ── manufacturer list ─────────────────────────────────────────────────
    @st.cache_data
    def _load_mfg():
        try:
            df = pd.read_excel("Manufacturer_ID_s.xlsx")
            mapping = dict(zip(df["Brand"].str.strip(), df["Manu ID"].astype(str)))
            vendors = sorted(df["Brand"].str.strip().tolist())
            return mapping, vendors
        except Exception:
            return {}, []

    mfg_mapping, vendor_list = _load_mfg()

    # ── session state init ────────────────────────────────────────────────
    for key in ("selected_sheet", "header_row"):
        if key not in st.session_state:
            st.session_state[key] = None

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 1 – Configuration
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
    # SECTION 2 – Upload
    # ══════════════════════════════════════════════════════════════════════
    st.markdown("### Upload Files")
    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        vendor_file = st.file_uploader("Vendor Data File", type=["xlsx", "xls"])
    with c2:
        template_file = st.file_uploader("Asset Template (empty)", type=["xlsx"])

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 3 – Sheet selection
    # ══════════════════════════════════════════════════════════════════════
    selected_sheet = None
    if vendor_file:
        try:
            xls = pd.ExcelFile(vendor_file)
            sheets = xls.sheet_names

            if len(sheets) > 1:
                st.markdown("---")
                st.markdown("### Select Sheet")
                cols = st.columns(min(len(sheets), 5))
                for i, s in enumerate(sheets):
                    with cols[i % 5]:
                        btn_type = "primary" if st.session_state.selected_sheet == s else "secondary"
                        if st.button(s, key=f"sh_{i}", use_container_width=True, type=btn_type):
                            st.session_state.selected_sheet = s
                            st.session_state.header_row = None       # reset downstream
                            st.rerun()
                if st.session_state.selected_sheet:
                    selected_sheet = st.session_state.selected_sheet
                    st.success(f"Selected: {selected_sheet}")
            else:
                selected_sheet = sheets[0]
                st.session_state.selected_sheet = selected_sheet
        except Exception as exc:
            st.error(f"Error reading file: {exc}")

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 4 – Header-row picker  (most vendor files use row 2 = index 1)
    # ══════════════════════════════════════════════════════════════════════
    header_row = None           # 0-based index that pandas will use
    if vendor_file and selected_sheet:
        st.markdown("---")
        st.markdown("### Select Header Row")

        # read first 5 raw rows so user can see which row has the column names
        try:
            preview = pd.read_excel(vendor_file, sheet_name=selected_sheet, header=None, nrows=5)
            st.markdown("First 5 rows of the sheet (pick the row that has column names):")
            st.dataframe(preview, use_container_width=True)
        except Exception:
            pass

        row_pick = st.selectbox(
            "Which row number contains column headers?",
            options=list(range(1, 6)),
            format_func=lambda x: f"Row {x}",
            index=1,          # default Row 2 (index 1) – correct for most vendor files
            key="hdr_pick"
        )
        header_row = row_pick - 1          # pandas header= is 0-based
        st.session_state.header_row = header_row

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 5 – SKU column selector
    # ══════════════════════════════════════════════════════════════════════
    sku_col = None
    df_columns = []                        # keep reference for later use

    if vendor_file and selected_sheet and header_row is not None:
        st.markdown("---")
        st.markdown("### Select SKU Column")
        try:
            # read 0 data-rows just to get column list
            tmp = pd.read_excel(vendor_file, sheet_name=selected_sheet, header=header_row, nrows=0)
            df_columns = [str(c) for c in tmp.columns]

            auto = _auto_detect_sku(df_columns)
            if auto:
                st.success(f"Auto-detected SKU column: {auto}")

            c1, c2 = st.columns(2)
            with c1:
                default_idx = (df_columns.index(auto) + 1) if auto and auto in df_columns else 0
                sku_col = st.selectbox(
                    "Select from file columns",
                    ["-- pick a column --"] + df_columns,
                    index=default_idx
                )
                if sku_col == "-- pick a column --":
                    sku_col = None

            with c2:
                custom = st.text_input("Or type column name manually", placeholder="e.g. Model Number")
                if custom.strip():
                    sku_col = custom.strip()

            if sku_col:
                st.info(f"Will use column: {sku_col}")
        except Exception as exc:
            st.error(f"Error reading columns: {exc}")

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 6 – Show which image columns were found in the file
    # ══════════════════════════════════════════════════════════════════════
    if vendor_file and selected_sheet and header_row is not None:
        try:
            tmp = pd.read_excel(vendor_file, sheet_name=selected_sheet, header=header_row, nrows=0)
            found = _columns_present(tmp, KNOWN_IMAGE_COLUMNS)

            st.markdown("---")
            st.markdown("### Image / PDF Columns Detected in Your File")

            if found:
                # show counts per category
                families = {}
                for col in found:
                    fam = KNOWN_IMAGE_COLUMNS[col][0]
                    families.setdefault(fam, []).append(col)

                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.metric("Main Image",     len(families.get("main_product_image", [])))
                with c2:
                    st.metric("Media Columns",  len(families.get("media", [])))
                with c3:
                    st.metric("Spec Sheets",    len(families.get("spec_sheet", [])))
                with c4:
                    st.metric("Install Sheets", len(families.get("install_sheet", [])))

                with st.expander("Full column list", expanded=False):
                    for col in found:
                        fam, folder, mtype = KNOWN_IMAGE_COLUMNS[col]
                        st.write(f"  {col}  ->  family={fam}, folder={folder}, mediatype={mtype}")
            else:
                st.warning("None of the known image/PDF columns were found in this sheet.")
        except Exception:
            pass

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 7 – Status bar
    # ══════════════════════════════════════════════════════════════════════
    st.markdown("---")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        (st.success if (vendor_name and mfg_prefix and brand_folder) else st.warning)("Config")
    with c2:
        (st.success if vendor_file   else st.warning)("Vendor File")
    with c3:
        (st.success if selected_sheet else st.warning)("Sheet")
    with c4:
        (st.success if sku_col        else st.warning)("SKU Column")
    with c5:
        (st.success if template_file  else st.warning)("Template")

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 8 – Generate
    # ══════════════════════════════════════════════════════════════════════
    st.markdown("---")
    ready = all([vendor_file, template_file, vendor_name, mfg_prefix, brand_folder, selected_sheet, sku_col, header_row is not None])

    if st.button("Generate Asset Template", disabled=not ready, use_container_width=True, type="primary"):
        with st.spinner("Processing …"):
            try:
                df = pd.read_excel(vendor_file, sheet_name=selected_sheet, header=header_row)
                st.info(f"Read {len(df)} rows  |  sheet = {selected_sheet}  |  header row = {header_row + 1}")

                output_df, log = _process(df, mfg_prefix, brand_folder, sku_col)

                if output_df is None or len(output_df) == 0:
                    st.error("No assets were generated. Check the log for details.")
                    st.text(log)
                else:
                    st.success(f"Generated {len(output_df)} asset rows")

                    # metrics
                    st.markdown("---")
                    c1, c2, c3, c4 = st.columns(4)
                    with c1:
                        st.metric("Total Assets",  len(output_df))
                    with c2:
                        st.metric("Main Images",   int((output_df["assetFamilyIdentifier"] == "main_product_image").sum()))
                    with c3:
                        st.metric("Media",         int((output_df["assetFamilyIdentifier"] == "media").sum()))
                    with c4:
                        st.metric("PDFs",          int(output_df["assetFamilyIdentifier"].isin(["spec_sheet","install_sheet"]).sum()))

                    with st.expander("Preview (first 20 rows)"):
                        st.dataframe(output_df.head(20), use_container_width=True)

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
                                           data=log,
                                           file_name=f"{vendor_name}_log.txt",
                                           mime="text/plain",
                                           use_container_width=True)
            except Exception as exc:
                st.error(str(exc))
                st.code(traceback.format_exc())


# ---------------------------------------------------------------------------
# Core processing – produces the 6-column output that matches your template
# ---------------------------------------------------------------------------
def _process(df: pd.DataFrame, mfg_prefix: str, brand_folder: str, sku_col: str):
    """
    Returns (output_df, log_text).
    output_df has exactly 6 columns in this order:
        code | label-en_US | product_reference | imagelink | assetFamilyIdentifier | mediatype
    """
    log_lines = []
    log_lines.append("=== BELAMI ASSET TEMPLATE GENERATION LOG ===")
    log_lines.append(f"Manufacturer Prefix : {mfg_prefix}")
    log_lines.append(f"Brand Folder        : {brand_folder}")
    log_lines.append(f"SKU Column          : {sku_col}")
    log_lines.append("")

    # ── validate SKU column exists ────────────────────────────────────────
    # normalise: compare lowered column names in case of case mismatch
    col_str_map = {str(c): c for c in df.columns}          # str -> original key
    col_lower_map = {str(c).lower(): str(c) for c in df.columns}

    actual_sku_col = None
    if sku_col in col_str_map:
        actual_sku_col = sku_col
    elif sku_col.lower() in col_lower_map:
        actual_sku_col = col_lower_map[sku_col.lower()]

    if actual_sku_col is None:
        log_lines.append(f"ERROR: SKU column '{sku_col}' not found.")
        log_lines.append(f"Available columns: {list(col_str_map.keys())}")
        return None, "\n".join(log_lines)

    log_lines.append(f"Using SKU column    : {actual_sku_col}")

    # ── figure out which known image columns exist in this file ───────────
    present_image_cols = _columns_present(df, KNOWN_IMAGE_COLUMNS)
    log_lines.append(f"Image/PDF columns found ({len(present_image_cols)}): {present_image_cols}")
    log_lines.append("")

    # ── iterate rows ──────────────────────────────────────────────────────
    rows_out = []
    skipped = []
    seen_codes = set()          # deduplicate on generated code

    for row_idx, row in df.iterrows():
        # --- extract SKU --------------------------------------------------
        raw_sku = row[actual_sku_col]
        if pd.isna(raw_sku) or str(raw_sku).strip() == "":
            skipped.append(f"Row {row_idx+2}: empty SKU")
            continue
        sku = str(raw_sku).strip()

        product_ref = f"{mfg_prefix}_{sku}"

        # --- iterate every known image/pdf column that exists --------------
        for col_name in present_image_cols:
            cell = row[col_name]
            if pd.isna(cell) or str(cell).strip() == "":
                continue

            filename = str(cell).strip()                  # e.g. "ALDF12LAJUDBK_App.jpg"
            stem    = Path(filename).stem                  # "ALDF12LAJUDBK_App"
            ext     = Path(filename).suffix.lower()        # ".jpg"

            fam, folder, mtype = KNOWN_IMAGE_COLUMNS[col_name]

            # ── VIDEO handling ──────────────────────────────────────────
            if _is_video(filename):
                # Videos are kept exactly: code = prefix_cleanedname (no _new_1k)
                # imagelink = brand/media/OriginalName.ext  (original case)
                code = f"{mfg_prefix}_{_clean_code(stem)}"
                if code in seen_codes:
                    continue                              # brand video repeats per SKU – keep only first
                seen_codes.add(code)
                rows_out.append({
                    "code":                   code,
                    "label-en_US":            code,
                    "product_reference":      product_ref,
                    "imagelink":              f"{brand_folder}/media/{filename}",
                    "assetFamilyIdentifier":  "media",
                    "mediatype":              "detail",
                })
                continue

            # ── PDF handling ────────────────────────────────────────────
            if _is_pdf(filename):
                # code   = prefix_cleanedStem_specs
                # imagelink = brand/specsheets/OriginalStem_new.pdf
                code = f"{mfg_prefix}_{_clean_code(stem)}_specs"
                if code in seen_codes:
                    continue
                seen_codes.add(code)
                rows_out.append({
                    "code":                   code,
                    "label-en_US":            code,
                    "product_reference":      product_ref,
                    "imagelink":              f"{brand_folder}/specsheets/{stem}_new.pdf",
                    "assetFamilyIdentifier":  fam,
                    "mediatype":              "",
                })
                continue

            # ── IMAGE handling ──────────────────────────────────────────
            # code      = prefix_cleanedStem_new_1k        (all lowercase)
            # imagelink = brand/folder/OriginalStem_new_1k.jpg  (original case stem)
            code = f"{mfg_prefix}_{_clean_code(stem)}_new_1k"
            if code in seen_codes:
                continue
            seen_codes.add(code)

            rows_out.append({
                "code":                   code,
                "label-en_US":            code,
                "product_reference":      product_ref,
                "imagelink":              f"{brand_folder}/{folder}/{stem}_new_1k.jpg",
                "assetFamilyIdentifier":  fam,
                "mediatype":              mtype,
            })

    # ── summary ───────────────────────────────────────────────────────────
    if rows_out:
        output_df = pd.DataFrame(rows_out)[
            ["code", "label-en_US", "product_reference", "imagelink", "assetFamilyIdentifier", "mediatype"]
        ]
    else:
        output_df = pd.DataFrame(
            columns=["code", "label-en_US", "product_reference", "imagelink", "assetFamilyIdentifier", "mediatype"]
        )

    log_lines.append("=== SUMMARY ===")
    log_lines.append(f"Total output rows     : {len(output_df)}")
    log_lines.append(f"main_product_image    : {int((output_df['assetFamilyIdentifier']=='main_product_image').sum())}")
    log_lines.append(f"media                 : {int((output_df['assetFamilyIdentifier']=='media').sum())}")
    log_lines.append(f"spec_sheet            : {int((output_df['assetFamilyIdentifier']=='spec_sheet').sum())}")
    log_lines.append(f"install_sheet         : {int((output_df['assetFamilyIdentifier']=='install_sheet').sum())}")
    if skipped:
        log_lines.append(f"\nSkipped rows ({len(skipped)}):")
        for s in skipped[:20]:
            log_lines.append(f"  {s}")
        if len(skipped) > 20:
            log_lines.append(f"  … and {len(skipped)-20} more")

    return output_df, "\n".join(log_lines)
