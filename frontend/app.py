import streamlit as st

# Import our modular components
from config import PAGE_TITLE, PAGE_ICON, LAYOUT
from styles.theme import initialize_theme
from styles.components import generate_dynamic_css
from utils.state import initialize_session_state, get_current_page, is_authenticated
from components.header import render_header
from pages.landing import render_landing
from pages.auth import render_auth
from pages.dashboard import render_dashboard
from pages.categories import render_categories
from pages.quiz import render_quiz
from pages.progress import render_progress
from pages.admin import render_admin

# Page configuration
st.set_page_config(
    page_title=PAGE_TITLE, 
    page_icon=PAGE_ICON, 
    layout=LAYOUT
)

# Initialize session state and theme
initialize_session_state()
initialize_theme()

# Apply CSS with current theme colors
from styles.theme import get_theme_colors
colors = get_theme_colors()
st.markdown(generate_dynamic_css(colors), unsafe_allow_html=True)

# Render header
render_header()

# Main page routing
current_page = get_current_page()

if current_page == "Landing":
    render_landing()
elif current_page == "Auth":
    render_auth()
elif current_page == "Home":
    render_dashboard()
elif current_page == "Categories":
    render_categories()
elif current_page == "Quiz":
    render_quiz()
elif current_page == "Progress":
    render_progress()
elif current_page == "Admin":
    render_admin()
else:
    # Default to landing page
    render_landing()
