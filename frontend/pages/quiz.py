import streamlit as st
from utils.api import check_health_claim, fetch_quiz_questions
from streamlit_helpers.user_integration import save_fact_for_user, show_recent_facts

def render_quiz() -> None:
    """Render the quiz page with health claim checker and quiz mode"""
    
    # Health Claim Checker
    with st.expander("Check a Health Claim"):
        claim = st.text_area("Enter a health claim:")
        if st.button("Check Claim") and claim.strip():
            result = check_health_claim(claim)
            if result:
                st.success(f"Result: {result['result']}")
                st.write(f"Explanation: {result['explanation']}")
                st.markdown(f"[Trusted Source]({result['source']})")
                # Offer to save verified claim to user's profile
                save_fact_for_user(
                    content=claim,
                    category="claim-check",
                    source_url=result.get("source"),
                    button_label="✅ I learned this fact!",
                )
            else:
                st.error("Error connecting to backend or invalid claim.")

    # Quiz Mode
    with st.expander("Quiz Mode", expanded=st.session_state.get("start_quiz", False)):
        start_clicked = st.button("Start Quiz") or st.session_state.get("start_quiz", False)
        
        if start_clicked:
            questions = fetch_quiz_questions()
            
            if questions:
                for q in questions:
                    st.write(q.get("question", ""))
                    answer = st.radio("Your answer:", q.get("options", []), key=q.get("id", "q"))
                    
                    if st.button(f"Submit {q.get('id', '')}"):
                        if answer == q.get("answer"):
                            st.write("✅ Correct!")
                        else:
                            st.write("❌ Wrong")
            else:
                st.error("Could not fetch quiz questions. Backend may be unavailable.")

            # Reset quiz flag after rendering
            if st.session_state.get("start_quiz"):
                st.session_state["start_quiz"] = False

    # Recent facts after interactions
    show_recent_facts(limit=6)
