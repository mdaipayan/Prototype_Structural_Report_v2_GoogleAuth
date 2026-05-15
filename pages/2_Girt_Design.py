"""Placeholder page for the upcoming girt design workflow."""

import streamlit as st

from utils.auth import require_google_auth

st.set_page_config(
    page_title="Girt Design | Coming Soon", page_icon="🧱", layout="wide"
)

require_google_auth()

st.markdown(
    """
<div style="background:linear-gradient(90deg,#1A3557,#2E6DA4);padding:22px 26px;border-radius:14px;margin-bottom:14px;color:white;">
  <h1 style="margin:0;color:white;">🧱 Girt Design</h1>
  <p style="margin:6px 0 0;color:#D6E8F7;">This module is being prepared for the same calculation/report workflow used by purlins.</p>
</div>
""",
    unsafe_allow_html=True,
)

st.info(
    "Girt design is not yet implemented in this prototype. Use **Purlin Design** for the completed "
    "calculation and PDF report workflow."
)

if st.button("← Back to Home", use_container_width=True):
    st.switch_page("app.py")
