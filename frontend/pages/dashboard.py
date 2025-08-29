import streamlit as st
from components.search import render_search
from components.cards import render_fact_card
from components.sidebar import render_sidebar
from utils.api import fetch_featured_fact
from utils.state import is_authenticated, set_page
from streamlit_helpers.user_integration import save_fact_for_user, show_recent_facts

def render_dashboard() -> None:
    """Render the main dashboard/home page"""
    # Check if user is authenticated
    if not is_authenticated():
        set_page("Landing")
        st.rerun()
        return
    
    # Search functionality
    query = render_search()
    
    # Main content layout
    left, right = st.columns([2.5, 1])
    
    with left:
        # Fetch and display featured fact
        fact = fetch_featured_fact(query)
        render_fact_card(fact)
        # Save fact button (integrated with FastAPI)
        save_fact_for_user(
            content=fact.get("title", ""),
            category=fact.get("category", "general"),
            source_url=(fact.get("sources") or [{}])[0].get("url"),
        )
    
    with right:
        # Right sidebar
        render_sidebar()
        # Recent facts list below sidebar widgets
        show_recent_facts(limit=8)
