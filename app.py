import streamlit as st

st.set_page_config(
    page_title="Belami Tools",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Simplified CSS - iOS compatible, no complex regex patterns
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

* {
    font-family: 'Inter', sans-serif;
}

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
    font-size: 1.1rem;
}

.stButton>button {
    width: 100%;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    font-weight: 600;
    padding: 0.75rem;
    border-radius: 10px;
    border: none;
}

.stDownloadButton>button {
    background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
}

/* Sidebar styling */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
}

section[data-testid="stSidebar"] .stMarkdown {
    color: white;
}

section[data-testid="stSidebar"] label {
    color: white;
    font-weight: 600;
}

/* Hide branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Mobile responsive */
@media (max-width: 768px) {
    .title {
        font-size: 1.8rem;
    }
    .block-container {
        padding: 1rem;
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
