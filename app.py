import streamlit as st

st.set_page_config(
    page_title="Belami Tools",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ultra-simple CSS - iOS compatible
st.markdown("""
<style>
* {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}

.main {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 1.5rem 1rem;
}

.block-container {
    background: white;
    border-radius: 20px;
    padding: 2rem;
    max-width: 1400px;
}

.title {
    font-size: 2.5rem;
    font-weight: 700;
    color: #667eea;
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
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    font-weight: 600;
    padding: 1rem;
    border-radius: 10px;
    border: none;
    width: 100%;
}

.stDownloadButton>button {
    background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
    padding: 1rem;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
}

section[data-testid="stSidebar"] label {
    color: white;
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
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
