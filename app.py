import streamlit as st

st.set_page_config(
    page_title="Belami Tools",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"about": "Belami Asset Automation Tools"}
)

# iOS & Android Compatible - iPhone 7 Plus Optimized
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

.main {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 0.75rem;
    min-height: 100vh;
}

.block-container {
    background: white;
    border-radius: 12px;
    padding: 1rem 0.75rem;
    max-width: 100%;
    width: 100%;
    margin: 0;
}

.title {
    font-size: clamp(1.5rem, 5vw, 2.2rem);
    font-weight: 700;
    color: #667eea;
    text-align: center;
    margin-bottom: 0.5rem;
    margin-top: 0;
    letter-spacing: -0.5px;
}

.subtitle {
    text-align: center;
    color: #6b7280;
    margin-bottom: 1.5rem;
    font-size: clamp(0.85rem, 3vw, 0.95rem);
    margin-top: 0;
}

.stButton > button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    color: white !important;
    font-weight: 600 !important;
    padding: 0.65rem 1rem !important;
    border-radius: 8px !important;
    border: none !important;
    width: 100% !important;
    transition: all 0.2s ease !important;
    font-size: 0.95rem !important;
}

.stButton > button:active {
    opacity: 0.9 !important;
    transform: scale(0.98) !important;
}

.stDownloadButton > button {
    background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%) !important;
    padding: 0.65rem 1rem !important;
    color: white !important;
    border-radius: 8px !important;
    font-size: 0.95rem !important;
}

.stSelectbox, .stTextInput, .stFileUploader {
    width: 100% !important;
}

.stSelectbox > div > div > select,
.stTextInput > div > div > input {
    border-radius: 8px !important;
    border: 1px solid #d1d5db !important;
    padding: 0.6rem 0.75rem !important;
    font-size: 0.95rem !important;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #667eea 0%, #764ba2 100%) !important;
}

section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stRadio > label {
    color: white !important;
    font-size: 0.95rem !important;
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

/* Professional alert styling */
.stAlert {
    border-radius: 8px !important;
    padding: 1rem !important;
    font-size: 0.9rem !important;
}

/* Mobile-first responsive */
@media (max-width: 480px) {
    .block-container {
        padding: 0.75rem 0.5rem !important;
        border-radius: 10px !important;
    }
    
    .main {
        padding: 0.5rem !important;
    }
    
    .stColumns {
        gap: 0.25rem !important;
    }
}

/* Tablet optimization */
@media (max-width: 768px) {
    .block-container {
        padding: 1rem 0.75rem !important;
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

/* Better touch targets */
.stButton > button,
.stDownloadButton > button {
    min-height: 44px !important;
    min-width: 44px !important;
}

/* Fix iOS file picker */
input[type="file"] {
    padding: 10px !important;
    border-radius: 8px !important;
}

/* Better spacing on mobile */
@media (max-width: 640px) {
    .block-container {
        padding: 0.5rem 0.5rem !important;
    }
    
    .stButton > button,
    .stDownloadButton > button {
        min-height: 48px !important;
        font-size: 16px !important;
        padding: 0.75rem 1rem !important;
    }
    
    .stSelectbox,
    .stTextInput {
        margin-bottom: 0.5rem !important;
    }
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
