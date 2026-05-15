"""
IS Steel Design Suite — Main Application
Streamlit multi-page app for IS 800:2007 structural steel member design.

Pages:
  1. Purlin Design
  2. Girt Design
  3. Column Design
"""

import streamlit as st

from utils.auth import require_google_auth

st.set_page_config(
    page_title="IS Steel Design Suite",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

require_google_auth()

# ── Custom CSS ─────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
/* Sidebar branding */
section[data-testid="stSidebar"] {
    background: linear-gradient(160deg, #1A3557 0%, #2E6DA4 100%);
}
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] li,
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] span { color: #FFFFFF !important; }
section[data-testid="stSidebar"] input,
section[data-testid="stSidebar"] textarea { color: #17324D !important; background: #FFFFFF !important; }
section[data-testid="stSidebar"] input::placeholder { color: #51677D !important; opacity: 1 !important; }
section[data-testid="stSidebar"] .stSelectbox label { color: #D6E8F7 !important; }

/* Main header bar */
.main-title {
    background: linear-gradient(90deg, #1A3557, #2E6DA4);
    padding: 22px 28px 14px 28px;
    border-radius: 10px;
    margin-bottom: 24px;
    color: white;
}
.main-title h1 { color: white !important; margin: 0; font-size: 2rem; }
.main-title p  { color: #D6E8F7; margin: 4px 0 0 0; font-size: 0.95rem; }

/* Code / IS reference badges */
.is-badge {
    display: inline-block;
    background: #E6F0FA;
    color: #1A3557;
    border: 1px solid #2E6DA4;
    border-radius: 12px;
    padding: 2px 10px;
    font-size: 0.8rem;
    font-weight: 600;
    margin: 2px;
}

/* Result cards */
.result-safe {
    background: #E6F4ED; border-left: 5px solid #1A7A4A;
    padding: 12px 16px; border-radius: 5px; margin: 8px 0;
}
.result-fail {
    background: #FDECEA; border-left: 5px solid #E84040;
    padding: 12px 16px; border-radius: 5px; margin: 8px 0;
}
.result-neutral {
    background: #F4F4F4; border-left: 5px solid #2E6DA4;
    padding: 10px 14px; border-radius: 5px; margin: 6px 0;
    font-family: 'Courier New', monospace; font-size: 0.88rem;
}
.formula-box {
    background: #F0F4FA; border: 1px solid #B8D0EA;
    border-radius: 6px; padding: 10px 14px;
    font-family: 'Courier New', monospace;
    font-size: 0.88rem; color: #1A3557; margin: 6px 0;
}
.step-header {
    background: #1A3557; color: white;
    padding: 7px 14px; border-radius: 5px;
    font-weight: 700; margin: 14px 0 6px 0;
    font-size: 0.97rem;
}
</style>
""",
    unsafe_allow_html=True,
)

# ── Landing Page ───────────────────────────────────────────────────────────
st.markdown(
    """
<div class="main-title">
  <h1>🏗️ IS Steel Design Suite</h1>
  <p>Structural Steel Member Design as per <strong>IS 800:2007</strong> | 
     IS 875 Parts 1–3 | SP 6(1):1964</p>
</div>
""",
    unsafe_allow_html=True,
)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 📐 Purlin Design")
    st.markdown(
        """
    Design of **roof purlins** subjected to dead load, live load, and wind uplift.
    - Biaxial bending check (IS 800 Cl. 9.3.1.1)
    - Load combinations per IS 875 / IS 800 Table 4
    - Shear and deflection checks
    - ISMB/ISLB/ISMC, ISA, lipped C/Z, and RHS/SHS section options
    - PDF report with step-by-step calculations
    
    <span class='is-badge'>IS 800:2007</span>
    <span class='is-badge'>IS 875 Pt.1,2,3</span>
    """,
        unsafe_allow_html=True,
    )
    if st.button("Open Purlin Design →", use_container_width=True, type="primary"):
        st.switch_page("pages/1_Purlin_Design.py")

with col2:
    st.markdown("### 🧱 Girt Design")
    st.markdown(
        """
    Design of **wall girts** supporting cladding under wind and self-weight.
    - Wind pressure / suction per IS 875 Part 3
    - Biaxial bending (wind horizontal + DL vertical)
    - Shear and serviceability checks
    - Professional PDF design report
    
    <span class='is-badge'>IS 800:2007</span>
    <span class='is-badge'>IS 875 Pt.3</span>
    """,
        unsafe_allow_html=True,
    )
    if st.button("Open Girt Design →", use_container_width=True, type="primary"):
        st.switch_page("pages/2_Girt_Design.py")

with col3:
    st.markdown("### 🏛️ Column Design")
    st.markdown(
        """
    Design of **axially loaded / beam-column** members under compression.
    - Non-dimensional slenderness and buckling curves a–d
    - Stress reduction factor χ per IS 800 Cl. 7.1.2
    - Combined axial + biaxial bending (Cl. 9.3.2.2)
    - Complete PDF with all intermediate steps
    
    <span class='is-badge'>IS 800:2007</span>
    <span class='is-badge'>Cl.7 & Cl.9</span>
    """,
        unsafe_allow_html=True,
    )
    if st.button("Open Column Design →", use_container_width=True, type="primary"):
        st.switch_page("pages/3_Column_Design.py")

st.divider()
st.markdown(
    """
<div style='text-align:center; color:#888; font-size:0.82rem; padding:8px'>
IS Steel Design Suite &nbsp;|&nbsp; D. Mandal &nbsp;|&nbsp;
Designed for educational & professional reference use as per BIS codes
</div>
""",
    unsafe_allow_html=True,
)
