import requests
from requests import RequestException
from typing import Optional, Dict, Any
from datetime import datetime

import streamlit as st


API_BASE = "http://127.0.0.1:8000"


def _auth_headers() -> Dict[str, str]:
    token = st.session_state.get("auth_token")
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}


def check_user_auth() -> bool:
    return bool(st.session_state.get("auth_token") and st.session_state.get("user_id"))


def login_user(sidebar: bool = True):
    container = st.sidebar if sidebar else st
    with container.expander("Account", expanded=True):
        if check_user_auth():
            container.success(f"Logged in as {st.session_state.get('username')}")
            if container.button("Log out"):
                for k in ["auth_token", "user_id", "username"]:
                    st.session_state.pop(k, None)
                container.info("Logged out.")
            return

        container.subheader("Login")
        with container.form("login_form", clear_on_submit=False):
            username = container.text_input("Username", key="login_username")
            password = container.text_input("Password", type="password", key="login_password")
            user_id_input = container.text_input("User ID", key="login_user_id")
            submitted = container.form_submit_button("Sign in")

        if submitted:
            if not username or not password or not user_id_input:
                container.error("Please enter username, password, and user ID.")
                return
            try:
                user_id = int(user_id_input)
            except ValueError:
                container.error("User ID must be a number.")
                return

            try:
                resp = requests.post(
                    f"{API_BASE}/token",
                    data={"username": username, "password": password},
                    timeout=10,
                )
                if resp.status_code != 200:
                    container.error("Invalid credentials.")
                    return
                token = resp.json().get("access_token")
                if not token:
                    container.error("Login failed: no token returned.")
                    return

                # Validate access to provided user_id
                chk = requests.get(
                    f"{API_BASE}/user/{user_id}/streaks",
                    headers={**_auth_headers(), "Authorization": f"Bearer {token}"},
                    timeout=10,
                )
                if chk.status_code == 403:
                    container.error("Access denied for this user ID. Please verify.")
                    return
                if chk.status_code == 404:
                    container.error("User not found. Check the user ID.")
                    return
                if chk.status_code != 200:
                    container.error("Unable to verify account access.")
                    return

                st.session_state["auth_token"] = token
                st.session_state["user_id"] = user_id
                st.session_state["username"] = username
                container.success("Signed in successfully.")
            except RequestException:
                container.error("Network error while logging in. Is the API running?")


def save_fact_for_user(content: str, category: Optional[str] = None, source_url: Optional[str] = None, button_label: str = "✅ I learned this fact!"):
    disabled = not check_user_auth()
    if st.button(button_label, disabled=disabled, use_container_width=True):
        if not check_user_auth():
            st.warning("Please log in to save facts.")
            return
        payload = {"content": content, "category": category, "source_url": source_url}
        try:
            resp = requests.post(
                f"{API_BASE}/user/{st.session_state['user_id']}/facts",
                json=payload,
                headers=_auth_headers(),
                timeout=10,
            )
            if resp.status_code == 200:
                st.success("Saved! Keep your streak going! 🎉")
                st.balloons()
            elif resp.status_code == 401:
                st.error("Session expired. Please log in again.")
            elif resp.status_code == 403:
                st.error("Access denied for this account.")
            elif resp.status_code == 404:
                st.error("User not found. Check your account.")
            else:
                st.error("Failed to save fact. Please try again.")
        except RequestException:
            st.error("Network error while saving the fact.")


def show_user_stats(sidebar: bool = True):
    container = st.sidebar if sidebar else st
    with container.expander("Your Streak", expanded=True):
        if not check_user_auth():
            container.info("Log in to see your streak stats.")
            return
        try:
            resp = requests.get(
                f"{API_BASE}/user/{st.session_state['user_id']}/streaks",
                headers=_auth_headers(),
                timeout=10,
            )
        except RequestException:
            container.error("Network error loading stats.")
            return

        if resp.status_code != 200:
            if resp.status_code == 401:
                container.error("Session expired. Please log in again.")
            elif resp.status_code == 403:
                container.error("Access denied for this account.")
            else:
                container.error("Failed to load stats.")
            return

        data = resp.json()
        current = data.get("current_streak", 0)
        longest = data.get("longest_streak", 0)
        total = data.get("total_facts_count", 0)
        week = data.get("facts_this_week", 0)

        col1, col2, col3 = container.columns(3)
        col1.metric("Current Streak", current)
        col2.metric("Longest", longest)
        col3.metric("Total Facts", total)

        target = max(1, min(7, longest or 7))
        progress = min(1.0, float(current) / float(target)) if target else 0.0
        container.progress(progress, text=f"{current} day streak")

        if current >= 2:
            container.success("Awesome! Keep your streak going! 🔥")
        else:
            container.info("Start your learning streak today!")

        container.caption(f"Facts learned this week: {week}")


def show_recent_facts(limit: int = 10, category: Optional[str] = None):
    st.subheader("Recent Learned Facts")
    if not check_user_auth():
        st.info("Log in to see your saved facts.")
        return
    params: Dict[str, Any] = {"limit": limit}
    if category:
        params["category"] = category
    try:
        resp = requests.get(
            f"{API_BASE}/user/{st.session_state['user_id']}/facts",
            params=params,
            headers=_auth_headers(),
            timeout=10,
        )
    except RequestException:
        st.error("Network error loading recent facts.")
        return

    if resp.status_code != 200:
        st.error("Failed to load recent facts.")
        return

    data = resp.json()
    items = data.get("items", [])
    if not items:
        st.write("No facts saved yet. Save your first one and start a streak!")
        return

    for fact in items:
        content = fact.get("content", "")
        category = fact.get("category") or "general"
        learned_at = fact.get("learned_at")
        try:
            # Handle ISO strings with/without microseconds and Z suffix
            ts = learned_at
            if ts and isinstance(ts, str):
                ts = ts.rstrip("Z")
                fmt = "%Y-%m-%dT%H:%M:%S.%f" if "." in ts else "%Y-%m-%dT%H:%M:%S"
                dt = datetime.strptime(ts, fmt)
                nice = dt.strftime("%b %d, %Y %H:%M UTC")
            else:
                nice = ""
        except Exception:
            nice = learned_at or ""

        with st.container(border=True):
            st.markdown(f"**{content}**")
            st.caption(f"Category: {category}  •  Learned: {nice}")


