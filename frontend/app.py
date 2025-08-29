import streamlit as st
from styles.theme import initialize_theme, get_theme_colors
from styles.components import generate_dynamic_css
from components.header import render_header
from pages.landing import render_landing
from pages.auth import render_auth
from pages.dashboard import render_dashboard
from pages.categories import render_categories
from pages.quiz import render_quiz
from pages.progress import render_progress
from pages.admin import render_admin
from utils.state import initialize_session_state, get_current_page
from streamlit_helpers.user_integration import login_user, show_user_stats

# Page configuration
st.set_page_config(
    page_title="HealthFactAI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize session state and theme
initialize_session_state()
initialize_theme()

# Get current theme colors and generate CSS
colors = get_theme_colors()
css = generate_dynamic_css(colors)

# Apply CSS
st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

# Render header
render_header()

# Sidebar: auth + user stats
login_user(sidebar=True)
show_user_stats(sidebar=True)

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
