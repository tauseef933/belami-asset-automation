import streamlit as st

st.set_page_config(
    page_title="Belami Tools",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"about": "Belami Asset Automation Tools"}
)

# iOS & Android Compatible - Fixed Header Overlap Issue
st.markdown("""
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, viewport-fit=cover, user-scalable=no">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="format-detection" content="telephone=no">

<style>
html, body, #root {
    width: 100vw;
    height: 100vh;
    margin: 0;
    padding: 0;
    overflow-x: hidden !important;
    -webkit-user-select: none;
    -webkit-touch-callout: none;
}

* {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
    box-sizing: border-box;
    -webkit-tap-highlight-color: transparent;
}

body {
    font-size: 16px;
    -webkit-font-smoothing: antialiased;
    -webkit-text-size-adjust: 100%;
}

/* CRITICAL FIX: Hide Streamlit default header completely */
header[data-testid="stHeader"] {
    display: none !important;
    height: 0 !important;
    position: fixed !important;
    top: -100px !important;
}

/* Hide toolbar that causes overlap */
.stDeployButton {
    display: none !important;
}

/* Hide share/GitHub/settings menu */
#MainMenu {
    visibility: hidden !important;
    display: none !important;
}

footer {
    visibility: hidden !important;
    display: none !important;
}

/* Fix app container to start from top */
.appview-container {
    padding-top: 0 !important;
    margin-top: 0 !important;
}

.main {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 0.75rem;
    min-height: 100vh;
    padding-top: 0.75rem !important;
    margin-top: 0 !important;
}

.block-container {
    background: white;
    border-radius: 12px;
    padding: 1.5rem 1rem;
    max-width: 100%;
    width: 100%;
    margin: 0;
    padding-top: 1.5rem !important;
}

/* Ensure no content is hidden behind header */
.element-container:first-child {
    margin-top: 0 !important;
    padding-top: 0 !important;
}

.title {
    font-size: clamp(1.5rem, 5vw, 2.2rem);
    font-weight: 700;
    color: #667eea;
    text-align: center;
    margin-bottom: 0.5rem;
    margin-top: 0;
    padding-top: 0;
    letter-spacing: -0.5px;
    line-height: 1.2;
}

.subtitle {
    text-align: center;
    color: #6b7280;
    margin-bottom: 1.5rem;
    font-size: clamp(0.85rem, 3vw, 0.95rem);
    margin-top: 0;
    line-height: 1.4;
}

.stButton > button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    color: white !important;
    font-weight: 600 !important;
    padding: 0.75rem 1.2rem !important;
    border-radius: 10px !important;
    border: none !important;
    width: 100% !important;
    transition: all 0.3s ease !important;
    font-size: 1rem !important;
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3) !important;
    cursor: pointer !important;
    min-height: 48px !important;
}

.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4) !important;
}

.stButton > button:active {
    opacity: 0.9 !important;
    transform: translateY(0) scale(0.98) !important;
}

.stDownloadButton > button {
    background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%) !important;
    padding: 0.75rem 1.2rem !important;
    color: white !important;
    border-radius: 10px !important;
    font-size: 1rem !important;
    box-shadow: 0 4px 12px rgba(17, 153, 142, 0.3) !important;
    border: none !important;
    width: 100% !important;
    font-weight: 600 !important;
    min-height: 48px !important;
    transition: all 0.3s ease !important;
}

.stDownloadButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 16px rgba(17, 153, 142, 0.4) !important;
}

.stSelectbox, .stTextInput, .stFileUploader {
    width: 100% !important;
}

.stSelectbox > div > div > select,
.stTextInput > div > div > input {
    border-radius: 10px !important;
    border: 2px solid #e5e7eb !important;
    padding: 0.7rem 0.9rem !important;
    font-size: 1rem !important;
    transition: border-color 0.2s ease !important;
}

.stSelectbox > div > div > select:focus,
.stTextInput > div > div > input:focus {
    border-color: #667eea !important;
    outline: none !important;
}

/* Sidebar styling */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #667eea 0%, #764ba2 100%) !important;
    padding-top: 1rem !important;
}

section[data-testid="stSidebar"] > div {
    padding-top: 1rem !important;
}

section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stRadio > label {
    color: white !important;
    font-size: 1rem !important;
    font-weight: 600 !important;
}

section[data-testid="stSidebar"] .stRadio > div {
    background: rgba(255, 255, 255, 0.1) !important;
    border-radius: 10px !important;
    padding: 0.5rem !important;
}

section[data-testid="stSidebar"] .stRadio label {
    color: white !important;
    padding: 0.6rem 1rem !important;
    border-radius: 8px !important;
    transition: background 0.2s ease !important;
}

section[data-testid="stSidebar"] .stRadio label:hover {
    background: rgba(255, 255, 255, 0.15) !important;
}

/* Professional alert styling */
.stAlert {
    border-radius: 10px !important;
    padding: 1rem !important;
    font-size: 0.95rem !important;
    border: none !important;
}

.stSuccess {
    background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%) !important;
    color: #065f46 !important;
}

.stError {
    background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%) !important;
    color: #991b1b !important;
}

.stInfo {
    background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%) !important;
    color: #1e40af !important;
}

.stWarning {
    background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%) !important;
    color: #92400e !important;
}

/* File uploader styling */
.stFileUploader {
    border: 2px dashed #d1d5db !important;
    border-radius: 12px !important;
    padding: 1.5rem !important;
    background: #f9fafb !important;
    transition: all 0.3s ease !important;
}

.stFileUploader:hover {
    border-color: #667eea !important;
    background: #f3f4f6 !important;
}

/* Mobile-first responsive */
@media (max-width: 480px) {
    .block-container {
        padding: 1rem 0.75rem !important;
        border-radius: 10px !important;
    }
    
    .main {
        padding: 0.5rem !important;
    }
    
    .stColumns {
        gap: 0.5rem !important;
    }
    
    .title {
        font-size: 1.5rem !important;
    }
    
    .subtitle {
        font-size: 0.85rem !important;
    }
}

/* Tablet optimization */
@media (max-width: 768px) {
    .block-container {
        padding: 1.25rem 1rem !important;
    }
    
    .main {
        padding: 0.75rem !important;
    }
}

/* Prevent zoom on input focus - Critical for iPhone */
input[type="text"],
input[type="number"],
input[type="email"],
input[type="tel"],
input[type="date"],
input[type="file"],
select,
textarea {
    font-size: 16px !important;
    -webkit-user-select: text;
}

/* Better touch targets - Apple HIG compliance */
.stButton > button,
.stDownloadButton > button,
.stRadio label {
    min-height: 44px !important;
    min-width: 44px !important;
}

/* Fix iOS file picker */
input[type="file"] {
    padding: 12px !important;
    border-radius: 10px !important;
}

/* Better spacing on mobile */
@media (max-width: 640px) {
    .block-container {
        padding: 1rem 0.75rem !important;
    }
    
    .stButton > button,
    .stDownloadButton > button {
        min-height: 50px !important;
        font-size: 16px !important;
        padding: 0.85rem 1.2rem !important;
    }
    
    .stSelectbox,
    .stTextInput {
        margin-bottom: 0.75rem !important;
    }
}

/* Smooth scrolling */
html {
    scroll-behavior: smooth;
}

/* Loading spinner */
.stSpinner > div {
    border-top-color: #667eea !important;
}

/* Better focus states for accessibility */
button:focus,
input:focus,
select:focus {
    outline: 2px solid #667eea !important;
    outline-offset: 2px !important;
}

/* Hide browser default focus on mobile */
@media (max-width: 768px) {
    button:focus,
    input:focus,
    select:focus {
        outline: none !important;
    }
}

/* Prevent content shift */
.main .block-container {
    position: relative;
}

/* Fix for columns on mobile */
@media (max-width: 768px) {
    [data-testid="column"] {
        width: 100% !important;
        flex: 1 1 100% !important;
    }
}

/* Ensure proper spacing for all elements */
.element-container {
    margin-bottom: 0.5rem;
}

/* Better markdown rendering */
.stMarkdown {
    line-height: 1.6;
}

.stMarkdown h1, 
.stMarkdown h2, 
.stMarkdown h3 {
    margin-top: 0;
    padding-top: 0;
}

/* Radio button improvements */
.stRadio > div {
    gap: 0.5rem !important;
}

.stRadio > div > label {
    cursor: pointer !important;
    user-select: none !important;
}
</style>
""", unsafe_allow_html=True)

# Sidebar navigation
with st.sidebar:
    st.markdown("### Navigation")
    page = st.radio(
        "",
        ["Asset Template Generator", "Image Resizer"],
        label_visibility="collapsed"
    )

# Route to appropriate page
if page == "Asset Template Generator":
    import asset_generator
    asset_generator.show()
elif page == "Image Resizer":
    import image_resizer
    image_resizer.show()
