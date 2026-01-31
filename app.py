import streamlit as st

st.set_page_config(
    page_title="Belami Tools",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional CSS - No emojis, clean corporate look
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

/* Sidebar styling */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
}

[data-testid="stSidebar"] .css-1d391kg {
    color: white;
}

[data-testid="stSidebar"] .stMarkdown {
    color: white;
}

/* Radio buttons in sidebar */
[data-testid="stSidebar"] .stRadio > label {
    color: white;
    font-weight: 600;
    font-size: 1.1rem;
}

[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label {
    background: rgba(255, 255, 255, 0.1);
    padding: 0.75rem 1rem;
    border-radius: 10px;
    margin-bottom: 0.5rem;
    cursor: pointer;
    transition: all 0.3s;
}

[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:hover {
    background: rgba(255, 255, 255, 0.2);
    transform: translateX(5px);
}

[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label div {
    color: white !important;
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

/* Hide Streamlit branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
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
