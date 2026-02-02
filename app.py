import streamlit as st

st.set_page_config(
    page_title="Belami Tools",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"about": "Belami Asset Automation Tools"}
)

# iOS & Android Compatible CSS with Meta Tags
st.markdown("""
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover, user-scalable=yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">

<style>
html, body {
    width: 100%;
    height: 100%;
    margin: 0;
    padding: 0;
    overflow-x: hidden;
}

* {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
    box-sizing: border-box;
}

.main {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 1rem;
}

.block-container {
    background: white;
    border-radius: 15px;
    padding: 1.5rem 1rem;
    max-width: 100%;
    margin: 0 auto;
}

.title {
    font-size: clamp(1.5rem, 5vw, 2.5rem);
    font-weight: 700;
    color: #667eea;
    text-align: center;
    margin-bottom: 0.5rem;
}

.subtitle {
    text-align: center;
    color: #6b7280;
    margin-bottom: 2rem;
    font-size: clamp(0.9rem, 4vw, 1.1rem);
}

.stButton > button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    color: white !important;
    font-weight: 600 !important;
    padding: 0.75rem 1.5rem !important;
    border-radius: 10px !important;
    border: none !important;
    width: 100% !important;
    transition: all 0.3s ease !important;
}

.stButton > button:hover {
    box-shadow: 0 10px 25px rgba(102, 126, 234, 0.4) !important;
    transform: translateY(-2px) !important;
}

.stDownloadButton > button {
    background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%) !important;
    padding: 0.75rem 1.5rem !important;
    color: white !important;
    border-radius: 10px !important;
}

.stDownloadButton > button:hover {
    box-shadow: 0 10px 25px rgba(17, 153, 142, 0.4) !important;
}

.stSelectbox, .stTextInput, .stFileUploader {
    width: 100% !important;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #667eea 0%, #764ba2 100%) !important;
}

section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stRadio {
    color: white !important;
}

section[data-testid="stSidebar"] .stRadio > label {
    color: white !important;
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

/* Mobile optimizations */
@media (max-width: 768px) {
    .block-container {
        padding: 1rem 0.75rem;
        border-radius: 12px;
    }
    
    .main {
        padding: 0.75rem;
    }
    
    .stColumns {
        gap: 0.5rem;
    }
}

/* Input field styling */
.stTextInput > div > div > input,
.stSelectbox > div > div > select {
    border-radius: 8px !important;
    border: 2px solid #e5e7eb !important;
    padding: 0.5rem 1rem !important;
    font-size: 1rem !important;
}

.stTextInput > div > div > input:focus,
.stSelectbox > div > div > select:focus {
    border-color: #667eea !important;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
}

/* Alert boxes */
.stAlert {
    border-radius: 10px !important;
    border-left: 4px solid;
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
