import streamlit as st
import pandas as pd
import io
import traceback
from pathlib import Path
from collections import Counter

import image_classifier as ic


# ===========================================================================
# CONSTANTS
# ===========================================================================

IMAGE_EXTS  = {'.jpg','.jpeg','.png','.gif','.bmp','.tiff','.webp','.svg'}
PDF_EXTS    = {'.pdf'}
VIDEO_EXTS  = {'.mp4','.mov','.avi','.wmv','.webm'}

IMAGE_KEYWORDS  = ['image','photo','picture','pic','img','lifestyle','swatch',
                   'infographic','diagram','sketch','dimensional','bb','b/b',
                   'render','visual','asset','artwork','gallery','thumbnail','file']
PDF_KEYWORDS    = ['spec','sheet','install','assembly','instruction','manual',
                   'guide','datasheet','specification','document','catalog',
                   'brochure','dimmer','warranty','care','energy','collection',
                   'material','blueprint','drawing']
VIDEO_KEYWORDS  = ['video','brand video']

MEDIATYPE_MAP   = {
    'lifestyle':'lifestyle','swatch':'swatch',
    'infographic':'informational','diagram':'dimension',
    'dimensional':'dimension','install':'','assembly':'','spec':'','sheet':'',
}

SKU_CANDIDATES  = [
    'sku','item number','item_number','item num','item_num',
    'model number','model_number','model no','model_no',
    'product code','product_code','product number','product_number',
    'part number','part_number','part no','part_no',
    'item code','item_code','article number','article_number',
    'catalog number','catalog_number','style number','style_number',
    'upc','gtin','barcode','product id','product_id',
    'sku number','sku_number','reference','ref','identifier',
    'asin','mfg part','mfg_part','vendor sku','vendor_sku',
]


# ===========================================================================
# HELPERS
# ===========================================================================

def _safe_lower(val) -> str:
    return str(val).lower()

def _is_url_column(col_name: str) -> bool:
    n = col_name.upper()
    return 'URL' in n or n.startswith('BOX LINK')

def _clean_code(raw: str) -> str:
    out = []
    for ch in raw.lower():
        out.append(ch if (ch.isalnum() or ch == '_') else '_')
    result = ''.join(out)
    while '__' in result:
        result = result.replace('__', '_')
    return result.strip('_')

def _auto_detect_sku(columns: list) -> str:
    lower_map = {_safe_lower(c): str(c) for c in columns}
    for cand in SKU_CANDIDATES:
        if cand in lower_map:
            return lower_map[cand]
    return ""


# ===========================================================================
# TWO-STEP COLUMN DETECTOR
# ===========================================================================

def detect_columns(df: pd.DataFrame) -> dict:
    images, pdfs, videos, skipped = [], [], [], []
    for col in df.columns:
        col_str   = str(col)
        col_lower = _safe_lower(col)
        if _is_url_column(col_str):
            continue
        hit_img = any(kw in col_lower for kw in IMAGE_KEYWORDS)
        hit_pdf = any(kw in col_lower for kw in PDF_KEYWORDS)
        hit_vid = any(kw in col_lower for kw in VIDEO_KEYWORDS)
        if not (hit_img or hit_pdf or hit_vid):
            continue

        samples = df[col].dropna().astype(str).str.strip()
        samples = samples[samples != '']
        n_img = n_pdf = n_vid = 0
        for val in samples.head(30):
            ext = Path(val).suffix.lower()
            if ext in IMAGE_EXTS:  n_img += 1
            if ext in PDF_EXTS:    n_pdf += 1
            if ext in VIDEO_EXTS:  n_vid += 1
        total = len(samples)

        if   n_pdf > 0 and n_img == 0 and n_vid == 0:  final = 'pdf'
        elif n_vid > 0 and n_img == 0 and n_pdf == 0:  final = 'video'
        elif n_img > 0:                                 final = 'image'
        else:
            skipped.append((col_str, f"keyword hit but 0 file extensions in {total} values"))
            continue

        confirmed  = n_img + n_pdf + n_vid
        confidence = round((confirmed / min(total,30)) * 100, 1) if total else 0
        mediatype  = 'detail'
        if final in ('pdf','video'):
            mediatype = ''
        else:
            for kw, mt in MEDIATYPE_MAP.items():
                if kw in col_lower:
                    mediatype = mt; break

        entry = dict(col=col_str, mediatype=mediatype,
                     confidence=confidence, sample=str(samples.iloc[0])[:60] if total else "",
                     total=total)
        if   final == 'image': images.append(entry)
        elif final == 'pdf':   pdfs.append(entry)
        elif final == 'video': videos.append(entry)

    for lst in (images, pdfs, videos):
        lst.sort(key=lambda x: x['confidence'], reverse=True)
    return dict(images=images, pdfs=pdfs, videos=videos, skipped=skipped)


# ===========================================================================
# URL COLUMN FINDER
# ===========================================================================

def find_url_columns(df: pd.DataFrame) -> list[dict]:
    results = []
    for col in df.columns:
        col_str = str(col)
        vals = df[col].dropna().astype(str).str.strip()
        vals = vals[vals.str.startswith('http')]
        if len(vals) == 0:
            continue
        has_asset = False
        for v in vals.head(10):
            ext = Path(v.split('?')[0]).suffix.lower()
            if ext in (IMAGE_EXTS | PDF_EXTS | VIDEO_EXTS):
                has_asset = True; break
        if not has_asset:
            continue
        paired = None
        c = col_str
        if   c.startswith("Image URL - "):
            cand = c.replace("Image URL - ", "")
            if cand in df.columns: paired = cand
        elif c.startswith("Box Link - "):
            cand = c.replace("Box Link - ", "")
            if cand in df.columns: paired = cand
        elif c.endswith(" URL"):
            cand = c[:-4]
            if cand in df.columns: paired = cand
        results.append(dict(col=col_str, paired=paired,
                            sample=str(vals.iloc[0])[:90], count=int(len(vals))))
    return results


# ===========================================================================
# PROCESSING  ->  6-column output
# ===========================================================================

def _process(df, mfg_prefix, brand_folder, sku_col,
             image_cols, pdf_cols, video_cols, col_mediatype):
    log = [f"=== LOG ===", f"Prefix={mfg_prefix} Brand={brand_folder} SKU={sku_col}",
           f"Images={image_cols}", f"PDFs={pdf_cols} Videos={video_cols}", ""]

    col_lower_map = {_safe_lower(c): str(c) for c in df.columns}
    actual_sku = sku_col if sku_col in df.columns else col_lower_map.get(_safe_lower(sku_col))
    if actual_sku is None:
        log.append(f"ERROR: SKU column '{sku_col}' not found.")
        return None, "\n".join(log)

    rows_out, seen, skipped = [], set(), []

    for row_idx, row in df.iterrows():
        raw_sku = row[actual_sku]
        if pd.isna(raw_sku) or str(raw_sku).strip() == '':
            skipped.append(f"Row {row_idx+2}: empty SKU"); continue
        sku         = str(raw_sku).strip()
        product_ref = f"{mfg_prefix}_{sku}"
        main_done   = False

        for col in image_cols:
            if col not in df.columns: continue
            cell = row[col]
            if pd.isna(cell) or str(cell).strip() == '': continue
            filename = str(cell).strip()
            stem = Path(filename).stem
            if Path(filename).suffix.lower() not in IMAGE_EXTS: continue
            code = f"{mfg_prefix}_{_clean_code(stem)}_new_1k"
            if code in seen: continue
            seen.add(code)
            if not main_done:
                fam, folder, mtype = 'main_product_image','products',''
                main_done = True
            else:
                fam, folder, mtype = 'media','media', col_mediatype.get(col,'detail')
            rows_out.append({"code":code,"label-en_US":code,"product_reference":product_ref,
                             "imagelink":f"{brand_folder}/{folder}/{stem}_new_1k.jpg",
                             "assetFamilyIdentifier":fam,"mediatype":mtype})

        for col in pdf_cols:
            if col not in df.columns: continue
            cell = row[col]
            if pd.isna(cell) or str(cell).strip() == '': continue
            filename = str(cell).strip()
            stem = Path(filename).stem
            if Path(filename).suffix.lower() not in PDF_EXTS: continue
            code = f"{mfg_prefix}_{_clean_code(stem)}_specs"
            if code in seen: continue
            seen.add(code)
            fam = 'install_sheet' if ('install' in _safe_lower(col) or 'assembly' in _safe_lower(col)) else 'spec_sheet'
            rows_out.append({"code":code,"label-en_US":code,"product_reference":product_ref,
                             "imagelink":f"{brand_folder}/specsheets/{stem}_new.pdf",
                             "assetFamilyIdentifier":fam,"mediatype":""})

        for col in video_cols:
            if col not in df.columns: continue
            cell = row[col]
            if pd.isna(cell) or str(cell).strip() == '': continue
            filename = str(cell).strip()
            stem = Path(filename).stem
            if Path(filename).suffix.lower() not in VIDEO_EXTS: continue
            code = f"{mfg_prefix}_{_clean_code(stem)}"
            if code in seen: continue
            seen.add(code)
            rows_out.append({"code":code,"label-en_US":code,"product_reference":product_ref,
                             "imagelink":f"{brand_folder}/media/{filename}",
                             "assetFamilyIdentifier":"media","mediatype":"detail"})

    COLS = ['code','label-en_US','product_reference','imagelink','assetFamilyIdentifier','mediatype']
    output_df = pd.DataFrame(rows_out, columns=COLS) if rows_out else pd.DataFrame(columns=COLS)

    log.append("=== SUMMARY ===")
    log.append(f"Total: {len(output_df)}")
    for fam in ('main_product_image','media','spec_sheet','install_sheet'):
        log.append(f"  {fam}: {int((output_df['assetFamilyIdentifier']==fam).sum())}")
    if skipped:
        log.append(f"Skipped: {len(skipped)}")
        for s in skipped[:20]: log.append(f"  {s}")
    return output_df, "\n".join(log)


# ===========================================================================
# STREAMLIT UI
# ===========================================================================

def show():
    st.markdown('<div class="title">Asset Template Generator</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Two-step AI detection  |  URL image classifier  |  manual fallback</div>', unsafe_allow_html=True)

    @st.cache_data
    def _load_mfg():
        try:
            mdf = pd.read_excel("Manufacturer_ID_s.xlsx")
            return (dict(zip(mdf["Brand"].str.strip(), mdf["Manu ID"].astype(str))),
                    sorted(mdf["Brand"].str.strip().tolist()))
        except Exception:
            return {}, []

    mfg_mapping, vendor_list = _load_mfg()

    for k in ('selected_sheet','header_row','classify_results'):
        if k not in st.session_state:
            st.session_state[k] = None

    # ── 1  CONFIG ──────────────────────────────────────────────────────
    st.markdown("### Configuration")
    st.markdown("---")
    c1,c2,c3 = st.columns(3)
    with c1:
        vendor_name = st.selectbox("Vendor Name", [""]+vendor_list) if vendor_list else st.text_input("Vendor Name")
    with c2:
        mfg_prefix = st.text_input("Manufacturer ID",
                                   value=mfg_mapping.get(vendor_name,"") if vendor_name else "",
                                   placeholder="2605")
    with c3:
        brand_folder = st.text_input("Brand Folder",
                                     value=vendor_name.lower().replace(" ","") if vendor_name else "",
                                     placeholder="afx")

    # ── 2  UPLOAD ──────────────────────────────────────────────────────
    st.markdown("### Upload Files")
    st.markdown("---")
    c1,c2 = st.columns(2)
    with c1: vendor_file   = st.file_uploader("Vendor Data File",      type=["xlsx","xls"])
    with c2: template_file = st.file_uploader("Asset Template (empty)", type=["xlsx"])

    # ── 3  SHEET ───────────────────────────────────────────────────────
    selected_sheet = None
    if vendor_file:
        try:
            sheets = pd.ExcelFile(vendor_file).sheet_names
            if len(sheets) > 1:
                st.markdown("---")
                st.markdown("### Select Sheet")
                cols = st.columns(min(len(sheets),5))
                for i, s in enumerate(sheets):
                    with cols[i%5]:
                        t = "primary" if st.session_state.selected_sheet == s else "secondary"
                        if st.button(s, key=f"sh_{i}", use_container_width=True, type=t):
                            st.session_state.selected_sheet = s
                            st.session_state.header_row     = None
                            st.session_state.classify_results = None
                            st.rerun()
                if st.session_state.selected_sheet:
                    selected_sheet = st.session_state.selected_sheet
                    st.success(f"Selected: {selected_sheet}")
            else:
                selected_sheet = sheets[0]
                st.session_state.selected_sheet = selected_sheet
        except Exception as e:
            st.error(str(e))

    # ── 4  HEADER ROW ─────────────────────────────────────────────────
    header_row = None
    if vendor_file and selected_sheet:
        st.markdown("---")
        st.markdown("### Select Header Row")
        try:
            st.dataframe(pd.read_excel(vendor_file, sheet_name=selected_sheet, header=None, nrows=5),
                         use_container_width=True)
        except Exception: pass
        pick       = st.selectbox("Which row has column names?", list(range(1,6)),
                                  format_func=lambda x: f"Row {x}", index=1, key="hdr_pick")
        header_row = pick - 1
        st.session_state.header_row = header_row

    # ── 5  SKU ─────────────────────────────────────────────────────────
    sku_col     = None
    all_columns = []
    if vendor_file and selected_sheet and header_row is not None:
        st.markdown("---")
        st.markdown("### Select SKU Column")
        try:
            tmp         = pd.read_excel(vendor_file, sheet_name=selected_sheet, header=header_row, nrows=0)
            all_columns = [str(c) for c in tmp.columns]
            auto_sku    = _auto_detect_sku(all_columns)
            if auto_sku:
                st.success(f"Auto-detected SKU column: **{auto_sku}**")
            c1,c2 = st.columns(2)
            with c1:
                didx    = (all_columns.index(auto_sku)+1) if auto_sku in all_columns else 0
                sku_col = st.selectbox("Pick from file columns",
                                       ["-- select --"]+all_columns, index=didx)
                if sku_col == "-- select --": sku_col = None
            with c2:
                manual = st.text_input("Or type column name", placeholder="e.g. Model Number")
                if manual.strip(): sku_col = manual.strip()
            if sku_col:
                st.info(f"Using SKU column: **{sku_col}**")
        except Exception as e:
            st.error(str(e))

    # ── 6  COLUMN DETECTION + MANUAL FALLBACK ─────────────────────────
    final_image_cols, final_pdf_cols, final_video_cols = [], [], []
    col_mediatype = {}

    if vendor_file and selected_sheet and header_row is not None:
        st.markdown("---")
        st.markdown("### AI Column Detection")
        try:
            full_df = pd.read_excel(vendor_file, sheet_name=selected_sheet, header=header_row)
            det = detect_columns(full_df)

            c1,c2,c3,c4 = st.columns(4)
            with c1: st.metric("Images",   len(det['images']))
            with c2: st.metric("PDFs",     len(det['pdfs']))
            with c3: st.metric("Videos",   len(det['videos']))
            with c4: st.metric("Rejected", len(det['skipped']))

            MTYPE_OPTIONS = ['lifestyle','angle','informational','dimension','swatch','detail']

            if det['images']:
                st.markdown("#### Detected Image Columns")
                for entry in det['images']:
                    cn = entry['col']
                    c1,c2,c3 = st.columns([1,2,3])
                    with c1:
                        keep = st.checkbox(cn, value=True, key=f"keep_img_{cn}")
                    with c2:
                        idx  = MTYPE_OPTIONS.index(entry['mediatype']) if entry['mediatype'] in MTYPE_OPTIONS else 5
                        mtype= st.selectbox("mediatype", MTYPE_OPTIONS, index=idx,
                                            key=f"mtype_{cn}", label_visibility="hidden")
                    with c3:
                        st.caption(f"{entry['confidence']}% | {entry['total']} vals | {entry['sample']}")
                    if keep:
                        final_image_cols.append(cn)
                        col_mediatype[cn] = mtype

            if det['pdfs']:
                st.markdown("#### Detected PDF Columns")
                for entry in det['pdfs']:
                    cn = entry['col']
                    c1,c2 = st.columns([1,3])
                    with c1: keep = st.checkbox(cn, value=True, key=f"keep_pdf_{cn}")
                    with c2: st.caption(f"{entry['confidence']}% | {entry['total']} vals | {entry['sample']}")
                    if keep: final_pdf_cols.append(cn)

            if det['videos']:
                st.markdown("#### Detected Video Columns")
                for entry in det['videos']:
                    cn = entry['col']
                    c1,c2 = st.columns([1,3])
                    with c1: keep = st.checkbox(cn, value=True, key=f"keep_vid_{cn}")
                    with c2: st.caption(f"{entry['confidence']}% | {entry['total']} vals | {entry['sample']}")
                    if keep: final_video_cols.append(cn)

            # manual fallback
            already   = set(final_image_cols + final_pdf_cols + final_video_cols)
            remaining = [c for c in all_columns if c not in already and not _is_url_column(c)]
            if remaining:
                st.markdown("---")
                st.markdown("#### Add Columns Manually")
                c1,c2,c3 = st.columns(3)
                with c1:
                    add_img = st.multiselect("Add as IMAGE", remaining, key="manual_img")
                    final_image_cols.extend(add_img)
                    for c in add_img: col_mediatype[c] = 'detail'
                with c2:
                    add_pdf = st.multiselect("Add as PDF", [c for c in remaining if c not in add_img], key="manual_pdf")
                    final_pdf_cols.extend(add_pdf)
                with c3:
                    add_vid = st.multiselect("Add as VIDEO",
                                            [c for c in remaining if c not in add_img and c not in add_pdf],
                                            key="manual_vid")
                    final_video_cols.extend(add_vid)

            if det['skipped']:
                with st.expander(f"Rejected columns ({len(det['skipped'])})"):
                    for name, reason in det['skipped']:
                        st.write(f"  {name} — {reason}")

        except Exception as e:
            st.error(str(e))
            st.code(traceback.format_exc())

    # ── 7  URL IMAGE CLASSIFIER  ───────────────────────────────────────
    if vendor_file and selected_sheet and header_row is not None:
        st.markdown("---")
        st.markdown("### Classify Images from URLs")
        st.caption("Downloads images from URL columns → Pillow heuristics (instant) → "
                   "Claude vision for uncertain ones (1-3 s each, very accurate).")
        try:
            full_df  = pd.read_excel(vendor_file, sheet_name=selected_sheet, header=header_row)
            url_cols = find_url_columns(full_df)

            if url_cols:
                url_col_names = [u['col'] for u in url_cols]
                st.markdown(f"Found **{len(url_cols)}** URL column(s) with downloadable assets:")
                for u in url_cols:
                    paired_txt = f" (paired with **{u['paired']}**)" if u['paired'] else ""
                    st.caption(f"  {u['col']} — {u['count']} URLs{paired_txt}  |  e.g. {u['sample'][:70]}")

                chosen = st.multiselect("Select URL columns to classify", url_col_names,
                                        default=[], key="chosen_url_cols")

                if chosen:
                    total_urls = sum(
                        int(full_df[col].dropna().astype(str).str.startswith('http').sum())
                        for col in chosen
                    )
                    st.info(f"Will classify **{total_urls}** images.  "
                            f"Heuristic is instant; uncertain ones go to Claude (~1-3 s each).")

                    if st.button("Run Image Classification", key="run_classify", type="primary"):
                        results  = []
                        progress = st.progress(0)
                        status   = st.empty()
                        done     = 0

                        import requests as _req

                        for col in chosen:
                            urls = full_df[col].dropna().astype(str)
                            urls = urls[urls.str.startswith('http')]

                            # find paired filename col
                            paired = None
                            for u in url_cols:
                                if u['col'] == col and u['paired']:
                                    paired = u['paired']; break

                            for idx, url in urls.items():
                                url = url.strip()
                                status.text(f"Classifying {done+1}/{total_urls} …  ({col})")

                                res = ic.classify_from_url(url)

                                orig_fname = ""
                                if paired and paired in full_df.columns:
                                    v = full_df.at[idx, paired]
                                    if pd.notna(v): orig_fname = str(v).strip()

                                results.append(dict(
                                    url=url, source_col=col,
                                    paired_filename=orig_fname,
                                    label=res.label, confidence=res.confidence,
                                    stage=res.stage, details=res.details,
                                    row_idx=int(idx),
                                ))
                                done += 1
                                progress.progress(done / total_urls if total_urls else 1)

                        progress.empty()
                        status.empty()
                        st.session_state.classify_results = results
            else:
                st.caption("No URL columns with downloadable images found in this sheet.")

        except Exception as e:
            st.error(str(e))
            st.code(traceback.format_exc())

    # ── display classification results ─────────────────────────────────
    if st.session_state.classify_results:
        results = st.session_state.classify_results
        st.markdown("---")
        st.markdown("### Classification Results")

        labels  = [r['label'] for r in results]
        counts  = Counter(labels)
        heur_n  = sum(1 for r in results if r['stage'] == 'heuristic')
        claude_n= sum(1 for r in results if r['stage'] == 'claude_api')
        err_n   = sum(1 for r in results if r['stage'] == 'error')

        # summary row
        metric_cols = st.columns(min(len(counts) + 3, 7))
        for i, (lbl, cnt) in enumerate(counts.most_common()):
            if i < len(metric_cols) - 3:
                with metric_cols[i]: st.metric(lbl, cnt)
        with metric_cols[-3]: st.metric("Heuristic",  heur_n)
        with metric_cols[-2]: st.metric("Claude API", claude_n)
        with metric_cols[-1]: st.metric("Errors",     err_n)

        # results table
        st.markdown("#### Results Table")
        table = []
        for r in results:
            table.append({
                'Filename':   r['paired_filename'] or "—",
                'Label':      r['label'],
                'Confidence': f"{r['confidence']}%",
                'Stage':      r['stage'],
                'Source Col': r['source_col'],
            })
        st.dataframe(pd.DataFrame(table), use_container_width=True)

        # image gallery  (first 12)
        st.markdown("#### Image Preview Gallery")
        gallery = [r for r in results if r['stage'] != 'error'][:12]
        if gallery:
            import requests as _req
            from PIL import Image as _Img
            gcols = st.columns(4)
            for i, r in enumerate(gallery):
                with gcols[i % 4]:
                    try:
                        resp = _req.get(r['url'], timeout=8)
                        resp.raise_for_status()
                        img  = _Img.open(io.BytesIO(resp.content))
                        st.image(img, caption=f"{r['label']} ({r['confidence']}%)  {r['paired_filename'] or ''}")
                    except Exception:
                        st.caption(f"[load failed]  {r['label']}")

        # download log
        st.markdown("---")
        log_rows = [{"filename": r['paired_filename'], "label": r['label'],
                     "confidence": r['confidence'], "stage": r['stage'],
                     "source_column": r['source_col'], "url": r['url'],
                     "row_index": r['row_idx']} for r in results]
        buf = io.BytesIO()
        pd.DataFrame(log_rows).to_csv(buf, index=False)
        buf.seek(0)
        st.download_button("Download Classification Log (CSV)", data=buf,
                           file_name="classification_log.csv", mime="text/csv")

    # ── 8  STATUS ──────────────────────────────────────────────────────
    st.markdown("---")
    c1,c2,c3,c4,c5 = st.columns(5)
    with c1: (st.success if (vendor_name and mfg_prefix and brand_folder) else st.warning)("Config")
    with c2: (st.success if vendor_file   else st.warning)("File")
    with c3: (st.success if selected_sheet else st.warning)("Sheet")
    with c4: (st.success if sku_col        else st.warning)("SKU Col")
    with c5: (st.success if (final_image_cols or final_pdf_cols or final_video_cols) else st.warning)("Columns")

    # ── 9  GENERATE ────────────────────────────────────────────────────
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
                st.info(f"Read {len(df)} rows | sheet={selected_sheet} | header=row {header_row+1}")

                output_df, log_text = _process(
                    df, mfg_prefix, brand_folder, sku_col,
                    final_image_cols, final_pdf_cols, final_video_cols, col_mediatype)

                if output_df is None or len(output_df) == 0:
                    st.error("No assets generated.")
                    st.text(log_text)
                else:
                    st.success(f"Generated {len(output_df)} asset rows")
                    c1,c2,c3,c4 = st.columns(4)
                    with c1: st.metric("Total",          len(output_df))
                    with c2: st.metric("Main Images",    int((output_df['assetFamilyIdentifier']=='main_product_image').sum()))
                    with c3: st.metric("Media + Videos", int((output_df['assetFamilyIdentifier']=='media').sum()))
                    with c4: st.metric("PDFs",           int(output_df['assetFamilyIdentifier'].isin(['spec_sheet','install_sheet']).sum()))

                    with st.expander("Preview (first 25 rows)"):
                        st.dataframe(output_df.head(25), use_container_width=True)

                    st.markdown("---")
                    c1,c2 = st.columns(2)
                    with c1:
                        buf = io.BytesIO()
                        with pd.ExcelWriter(buf, engine="openpyxl") as w:
                            output_df.to_excel(w, sheet_name="Sheet1", index=False)
                        buf.seek(0)
                        st.download_button("Download Asset Template", data=buf,
                                           file_name=f"{vendor_name}_Asset_Template.xlsx",
                                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                           use_container_width=True, type="primary")
                    with c2:
                        st.download_button("Download Processing Log", data=log_text,
                                           file_name=f"{vendor_name}_log.txt", mime="text/plain",
                                           use_container_width=True)
            except Exception as e:
                st.error(str(e))
                st.code(traceback.format_exc())
