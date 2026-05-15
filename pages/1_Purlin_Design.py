"""
Page 1 — Purlin Design
IS 800:2007 + IS 875 (Part 1, 2, 3)
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import streamlit as st
import pandas as pd
from utils.sections import (
    COLD_FORMED_C,
    COLD_FORMED_Z,
    COMMON_PURLIN_SECTION_TYPES,
    HOLLOW_BOX,
    ISA,
    ISLB,
    ISMB,
    ISMC,
)
from utils.purlin_calc import run_purlin_design
from utils.auth import require_google_auth
from utils.pdf_report import generate_purlin_pdf

st.set_page_config(
    page_title="Purlin Design | IS 800:2007", page_icon="📐", layout="wide"
)

require_google_auth()

st.markdown(
    """
<style>
.step-header{background:#1A3557;color:white;padding:7px 14px;border-radius:5px;
             font-weight:700;margin:14px 0 6px 0;font-size:.97rem;}
.formula-box{background:#F0F4FA;border:1px solid #B8D0EA;border-radius:6px;
             padding:10px 14px;font-family:'Courier New',monospace;
             font-size:.87rem;color:#1A3557;margin:6px 0;white-space:pre-wrap;}
.result-safe{background:#E6F4ED;border-left:5px solid #1A7A4A;
             padding:10px 14px;border-radius:5px;margin:6px 0;}
.result-fail{background:#FDECEA;border-left:5px solid #E84040;
             padding:10px 14px;border-radius:5px;margin:6px 0;}
.ref-tag{color:#2E6DA4;font-size:.79rem;font-style:italic;}
section[data-testid="stSidebar"]{background:linear-gradient(160deg,#1A3557,#2E6DA4);}
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] li,
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] span{color:#FFF!important;}
section[data-testid="stSidebar"] input,
section[data-testid="stSidebar"] textarea{color:#17324D!important;background:#FFFFFF!important;}
section[data-testid="stSidebar"] input::placeholder{color:#51677D!important;opacity:1!important;}
.sidebar-badge{background:rgba(255,255,255,.14);border:1px solid rgba(255,255,255,.35);border-radius:14px;padding:14px 12px;text-align:center;margin-bottom:12px;}
.sidebar-badge .icon{font-size:2.4rem;line-height:1;margin-bottom:6px;}
.sidebar-badge .title{font-weight:800;color:white;font-size:1rem;}
.sidebar-badge .subtitle{color:#D6E8F7;font-size:.78rem;margin-top:2px;}
.design-note{background:#FFF8E6;border-left:4px solid #D99A00;color:#17324D;padding:8px 10px;border-radius:6px;margin-top:8px;font-size:.84rem;}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div style="background:linear-gradient(90deg,#1A3557,#2E6DA4);padding:22px 26px;border-radius:14px;margin-bottom:14px;color:white;">
  <h1 style="margin:0;color:white;">📐 Purlin Design — IS 800:2007 / IS 801:1975</h1>
  <p style="margin:6px 0 0;color:#D6E8F7;">Step-by-step roof purlin loading, biaxial bending, shear, deflection, and PDF report generation.</p>
</div>
""",
    unsafe_allow_html=True,
)
st.caption(
    "Loading: IS 875 Pt.1 (DL) + Pt.2 (LL) + Pt.3 (Wind)  |  "
    "Section check: IS 800:2007 or IS 801:1975 cold-formed mode  |  "
    "Sections: SP 6(1):1964 / IS 808:1989"
)

# ── Sidebar — Project info ─────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-badge">
          <div class="icon">📐</div>
          <div class="title">Purlin Design</div>
          <div class="subtitle">IS 800 · IS 875 · Section Database</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("**References**")
    st.markdown(
        "- IS 800:2007 Cl. 8.2.1\n- IS 800:2007 Cl. 9.3.1.1\n- IS 800:2007 Cl. 8.4.1\n- IS 875 Pt.1/2/3\n- SP 6(1):1964"
    )
    project_name = st.text_input(
        "Project Name", placeholder="Enter project name", value="My Project"
    )

# ── Input Columns ──────────────────────────────────────────────────────────
st.markdown("### 🔢 Design Inputs")
c1, c2, c3 = st.columns(3)

with c1:
    st.markdown("**Geometry**")
    span = st.number_input(
        "Span L (m)", 1.0, 20.0, 5.0, 0.25, help="Purlin span between supports (m)"
    )
    spacing = st.number_input(
        "Purlin Spacing (m)",
        0.5,
        5.0,
        1.5,
        0.25,
        help="Centre-to-centre spacing of purlins (m)",
    )
    slope = st.number_input(
        "Roof Slope θ (°)",
        0.0,
        45.0,
        10.0,
        0.5,
        help="Inclination of roof surface with horizontal",
    )

with c2:
    st.markdown("**Loading  (IS 875)**")
    dead_load = st.number_input(
        "Dead Load (kN/m²)",
        0.1,
        3.0,
        0.55,
        0.05,
        help="Roofing + insulation. Use the checkbox below to control purlin self-weight.",
    )
    dead_load_excludes_self_weight = st.checkbox(
        "Dead load excludes purlin self-weight",
        value=True,
        help="Keep checked to add selected-section self-weight separately. Uncheck if DL already includes purlin weight allowance.",
    )
    live_load = st.number_input(
        "Live Load (kN/m²)",
        0.0,
        2.0,
        0.75,
        0.05,
        help="IS 875 Pt.2: 0.75 kN/m² for slopes ≤ 10°",
    )
    wind_pres = st.number_input(
        "Design Wind Pressure qd (kN/m²)",
        0.1,
        3.0,
        0.70,
        0.05,
        help="Design wind pressure from IS 875 Pt.3 Cl.5.4",
    )
    Cpe = st.number_input(
        "Ext. Pressure Coeff Cpe",
        -2.0,
        2.0,
        -0.8,
        0.05,
        help="For roof: typically −0.8 (suction) on windward slope",
    )
    Cpi = st.number_input(
        "Int. Pressure Coeff Cpi",
        -0.5,
        0.5,
        0.2,
        0.05,
        help="Dominant openings: +0.2 or −0.2 per IS 875 Pt.3",
    )

with c3:
    st.markdown("**Material & Section**")
    fy = st.selectbox(
        "Steel Grade fy (MPa)",
        [250, 345, 410],
        index=0,
        help="IS 2062: E250=250 MPa, E350=345 MPa, E410=410 MPa",
    )
    gm0 = st.number_input(
        "γm0",
        1.00,
        1.25,
        1.10,
        0.01,
        help="IS 800 Cl.5.4.1 — Partial safety factor for resistance",
    )
    design_code = st.selectbox(
        "Purlin Design Code",
        ["IS 800:2007", "IS 801:1975"],
        index=0,
        help="Use IS 801:1975 for cold-formed lipped C/Z effective-width design. Other sections remain on IS 800:2007.",
    )

    all_sec_types = {
        "ISMB (I-Beam)": ISMB,
        "ISLB (Light Beam)": ISLB,
        "ISMC (Channel)": ISMC,
        "ISA (Angle)": ISA,
        "Cold-formed C (Lipped)": COLD_FORMED_C,
        "Cold-formed Z (Lipped)": COLD_FORMED_Z,
        "Hollow / Box (RHS/SHS)": HOLLOW_BOX,
    }
    sec_type_label = st.selectbox("Section Type", list(all_sec_types.keys()))
    sec_dict = all_sec_types[sec_type_label]
    sec_names = list(sec_dict.keys())
    sec_name = st.selectbox(
        "Section Designation", sec_names, index=min(4, len(sec_names) - 1)
    )
    sp = sec_dict[sec_name]
    cold_formed_selected = sp.get("section_family") in {
        "Cold-formed C-sections",
        "Cold-formed Z-sections",
    }
    if design_code == "IS 801:1975" and cold_formed_selected:
        st.info(
            "IS 801:1975 mode enabled: lipped C/Z checks will use effective-width cold-formed design."
        )
    elif design_code == "IS 801:1975":
        st.warning(
            "IS 801:1975 applies to cold-formed lipped C/Z sections only. This selected section will be checked as per IS 800:2007."
        )

    with st.expander("📋 Section Properties (auto-filled from section database)"):
        col_a, col_b = st.columns(2)
        col_a.metric("A (cm²)", sp.get("Area", 0))
        col_a.metric("Ixx (cm⁴)", sp.get("Ixx", 0))
        area = sp.get("Area", 0) or 0
        rxx_preview = (sp.get("Ixx", 0) / area) ** 0.5 if area else 0
        ryy_preview = (sp.get("Iyy", 0) / area) ** 0.5 if area else 0
        col_a.metric("rxx / ryy (cm)", f"{rxx_preview:.2f} / {ryy_preview:.2f}")
        col_a.metric("Zxx / Zyy (cm³)", f"{sp.get('Zxx', 0)} / {sp.get('Zyy', 0)}")
        col_b.metric("h × bf (mm)", f"{sp.get('h', 0)} × {sp.get('bf', 0)}")
        col_b.metric("tf / tw (mm)", f"{sp.get('tf', 0)} / {sp.get('tw', 0)}")
        col_b.metric("Weight (kg/m)", sp.get("weight", 0))
        if sp.get("ui_note") or sp.get("design_note"):
            st.markdown(
                f"<div class='design-note'>{sp.get('ui_note', sp['design_note'])}</div>",
                unsafe_allow_html=True,
            )

    with st.expander("🧷 Flange Restraint / Wind Uplift Assumptions", expanded=False):
        top_flange_restrained = st.checkbox(
            "Roof sheeting restrains top compression flange",
            value=True,
            help="Required for using full major-axis section capacity under gravity loading unless LTB is checked separately.",
        )
        bottom_flange_restrained = st.checkbox(
            "Bottom flange / uplift restraint provided",
            value=True,
            help="Required when wind suction reverses compression to the bottom flange.",
        )
        st.caption(
            "If either restraint is not provided, the report marks the explicit stability "
            "assumption check as not satisfied so an LTB/uplift bracing design can be added."
        )

    default_lap = max(0.10 * span, 0.60)
    lap_length = float(default_lap)
    lap_bolt_dia = 16
    lap_bolt_rows = 2
    lap_bolts_per_row = 2
    lap_bolt_grade = 400
    lap_plate_fu = 410.0
    with st.expander("🔩 Purlin Lap / Splice Design", expanded=False):
        if cold_formed_selected:
            st.info(
                "Lap/nested continuity is enabled only for cold-formed lipped C/Z purlins, "
                "which can physically nest over a support."
            )
            lap_length = st.number_input(
                "Provided Lap Length (m)",
                0.10,
                3.00,
                float(default_lap),
                0.05,
                help="Recommended minimum is max(10% of span, 600 mm).",
            )
            lap_bolt_dia = st.selectbox(
                "Lap Bolt Diameter (mm)", [12, 16, 20, 24], index=1
            )
            lap_bolt_rows = st.number_input("Bolt Rows", 1, 6, 2, 1)
            lap_bolts_per_row = st.number_input("Bolts per Row", 1, 8, 2, 1)
            lap_bolt_grade = st.selectbox("Bolt Grade fub (MPa)", [400, 800], index=0)
            lap_plate_fu = st.number_input(
                "Connected Steel fu (MPa)",
                360.0,
                550.0,
                410.0,
                10.0,
                help="Ultimate tensile strength used for bolt bearing capacity.",
            )
        else:
            st.warning(
                "Same-plane lapped/nested purlins are not applicable to hot-rolled or "
                "hollow sections such as ISMB, ISLB, ISMC, ISA, RHS, or SHS. Use a "
                "proper bolted splice/seat/cleat detail, or switch to a cold-formed "
                "lipped C/Z purlin if a lapped continuous system is required."
            )

st.markdown("### 📚 Common Purlin Section Types Used in IS-Based Design")
st.markdown(
    "The calculation module designs rolled **ISMB/ISLB/ISMC**, **ISA angle**, "
    "cold-formed **lipped C/Z**, and **RHS/SHS hollow-box** sections from the "
    "project database. The table below summarizes the supported purlin families, "
    "common shapes, example designations, and calculation scope."
)
st.dataframe(
    pd.DataFrame(COMMON_PURLIN_SECTION_TYPES).rename(
        columns={
            "type": "Section Type",
            "shape": "Common Shape",
            "designation": "Common IS / Trade Designation",
            "examples": "Examples",
            "typical_use": "Typical Use",
            "calculation_status": "Calculation Status",
        }
    ),
    hide_index=True,
    use_container_width=True,
    key="common_purlin_section_types_table",
)
st.info(
    "Cold-formed C/Z entries include effective-width, shear-buckling, web-crippling, "
    "distortional-geometry, and deflection checks. Angle entries remain gross-section "
    "checks and require connection eccentricity verification."
)


# ── Run Calculation ────────────────────────────────────────────────────────
current_input = {
    "span_m": span,
    "spacing_m": spacing,
    "roof_slope_deg": slope,
    "dead_load": dead_load,
    "live_load": live_load,
    "wind_pressure": wind_pres,
    "Cp_ext": Cpe,
    "Cp_int": Cpi,
    "fy": float(fy),
    "gm0": gm0,
    "section_name": sec_name,
    "section_props": sp,
    "design_code": design_code,
    "lap_length_m": lap_length,
    "lap_bolt_dia_mm": lap_bolt_dia,
    "lap_bolt_rows": lap_bolt_rows,
    "lap_bolts_per_row": lap_bolts_per_row,
    "lap_bolt_grade_fub": lap_bolt_grade,
    "lap_plate_fu": lap_plate_fu,
    "dead_load_excludes_self_weight": dead_load_excludes_self_weight,
    "top_flange_restrained": top_flange_restrained,
    "bottom_flange_restrained": bottom_flange_restrained,
    "candidate_sections": all_sec_types,
    "economy_max_recommendations": 5,
}


def _store_current_purlin_design(show_refresh_notice=False):
    st.session_state["purlin_result"] = run_purlin_design(current_input)
    st.session_state["purlin_input"] = dict(current_input)
    st.session_state["purlin_project"] = project_name
    st.session_state["purlin_section_name"] = sec_name
    if show_refresh_notice:
        st.info(
            "Inputs changed after the previous design/report. The purlin design "
            "and downloadable PDF have been recalculated using the latest inputs."
        )


if st.button("▶  Run Purlin Design", use_container_width=True, type="primary"):
    _store_current_purlin_design()
elif (
    "purlin_result" in st.session_state
    and st.session_state.get("purlin_input") != current_input
):
    _store_current_purlin_design(show_refresh_notice=True)

# ── Display Results ────────────────────────────────────────────────────────
if "purlin_result" in st.session_state:
    r = st.session_state["purlin_result"]
    cls = r.get("section_class", {})

    ok_all = r.get("overall_status") == "SAFE"
    status_icon = "✅" if ok_all else "❌"
    st.markdown(f"### {status_icon} Overall Status: **{r['overall_status']}**")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Governing Combo", r.get("governing_combo", "—").split(":", 1)[0])
    m2.metric("Biaxial Utilisation", f"{r['biaxial_ratio'] * 100:.1f}%")
    m3.metric("Shear Utilisation", f"{r.get('shear_ratio', 0) * 100:.1f}%")
    m4.metric("Deflection Utilisation", f"{r.get('defl_ratio', 0) * 100:.1f}%")

    if ok_all:
        st.success(
            f"Section **{r['section_name']}** is adequate for the selected design inputs."
        )
    else:
        st.error(
            f"Section **{r['section_name']}** is not adequate. Increase the section size or revise spacing/span/loading."
        )

    st.divider()

    # ── Step 1: Loads ──────────────────────────────────────────
    with st.expander("📌 Step 1 — Load Calculation  [IS 875]", expanded=True):
        st.markdown(
            '<div class="step-header">1.1  Self Weight & Distributed Loads</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
<div class="formula-box">
Self weight of purlin  =  {r["sw_kNm"]:.4f} kN/m  [SP 6(1):1964]

Total DL on purlin  =  {dead_load:.2f} × {spacing:.2f} + {r["sw_kNm"]:.4f}  =  {dead_load * spacing + r["sw_kNm"]:.4f} kN/m

Resolved perpendicular to slope (→ Mz):
  w_z,DL  =  w_DL × cos θ  =  {r["wz_DL"]:.4f} kN/m  [IS 875 Pt.1]
  w_z,LL  =  LL × s × cos θ  =  {r["wz_LL"]:.4f} kN/m  [IS 875 Pt.2]

Resolved along slope (→ My):
  w_y,DL  =  w_DL × sin θ  =  {r["wy_DL"]:.4f} kN/m
  w_y,LL  =  LL × s × sin θ  =  {r["wy_LL"]:.4f} kN/m

Wind load:
  w_wind  =  qd × (Cpe − Cpi) × s  =  {wind_pres:.2f} × ({Cpe:.2f} − {Cpi:.2f}) × {spacing:.2f}  =  {r["w_wind"]:.4f} kN/m  [IS 875 Pt.3]
</div>
""",
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="step-header">1.2  Load Combinations  [IS 800:2007 Table 4]</div>',
            unsafe_allow_html=True,
        )

        combo_df = pd.DataFrame(
            {
                "Load Combo": [
                    "LC1: 1.5(DL+LL)",
                    "LC2: 1.2(DL+LL+Wind)",
                    "LC3: 0.9DL+1.5Wind",
                ],
                "wz,d (kN/m)": [r.get("wz_1", 0), r.get("wz_2", 0), r.get("wz_3", 0)],
                "wy,d (kN/m)": [r.get("wy_1", 0), r.get("wy_2", 0), r.get("wy_3", 0)],
            }
        )
        st.dataframe(combo_df.set_index("Load Combo"), use_container_width=True)
        st.info(
            f"**Governing combo:** {r.get('governing_combo', '—')}  |  "
            f"design magnitudes: wz,d = {r['wz_d']:.4f} kN/m, wy,d = {r['wy_d']:.4f} kN/m"
        )

    # ── Step 2: Section Classification ────────────────────────
    with st.expander("📌 Step 2 — Section Classification  [IS 800:2007 Table 2]"):
        eps = cls.get("epsilon", (250 / float(fy)) ** 0.5)
        b_tf_val = cls.get("b_tf", 0.0)
        d_tw_val = cls.get("d_tw", 0.0)

        limits = cls.get("limits", {})
        f_lim = limits.get("flange", [0.0, 0.0, 0.0])
        w_lim = limits.get("web", [0.0, 0.0, 0.0])

        f_class = cls.get("flange_class", "Unknown")
        w_class = cls.get("web_class", "Unknown")
        overall_class = cls.get("overall", "Unknown")

        st.markdown(
            f"""
<div class="formula-box">
ε  =  √(250 / fy)  =  √(250 / {r.get("fy", 250):.0f})  =  {eps:.4f}

Outstand flange ratio:
  b/tf  =  ({sp.get("bf", 0)}/2 − {sp.get("tw", 0)}/2) / {sp.get("tf", 1)}  =  {b_tf_val:.2f}
  Plastic limit  9.4ε  =  {f_lim[0]:.2f}
  Compact  limit 13.6ε =  {f_lim[1]:.2f}
  Semi-compact  15.7ε  =  {f_lim[2]:.2f}
  → Flange: {f_class}

Web ratio:
  d/tw  =  ({sp.get("h", 0)} − 2×{sp.get("tf", 0)}) / {sp.get("tw", 1)}  =  {d_tw_val:.2f}
  Plastic limit  84ε   =  {w_lim[0]:.2f}
  Compact  limit 105ε  =  {w_lim[1]:.2f}
  Semi-compact  126ε   =  {w_lim[2]:.2f}
  → Web: {w_class}

Overall Classification:  {overall_class}
</div>
""",
            unsafe_allow_html=True,
        )

    # ── Step 3: BM & SF ────────────────────────────────────────
    with st.expander("📌 Step 3 — Design Bending Moments & Shear Force"):
        st.markdown(
            f"""
<div class="formula-box">
Simply supported purlin, UDL loading:

Mz  =  wz,d × L² / 8  =  {r["wz_d"]:.4f} × {span:.2f}² / 8  =  {r["Mz_kNm"]:.4f} kNm  (major axis)
My  =  wy,d × L² / 8  =  {r["wy_d"]:.4f} × {span:.2f}² / 8  =  {r["My_kNm"]:.4f} kNm  (minor axis)

Vz  =  wz,d × L / 2  =  {r["wz_d"]:.4f} × {span:.2f} / 2  =  {r["Vz_kN"]:.4f} kN
Vy  =  wy,d × L / 2  =  {r["wy_d"]:.4f} × {span:.2f} / 2  =  {r["Vy_kN"]:.4f} kN
</div>
""",
            unsafe_allow_html=True,
        )

    # ── Step 4: Moment Capacity ────────────────────────────────
    with st.expander("📌 Step 4 — Design Moment Capacity  [IS 800:2007 Cl. 8.2.1]"):
        if r.get("use_plastic_modulus"):
            st.markdown(
                f"""
<div class="formula-box">
{overall_class} section → use plastic section modulus

Mdz  =  βb × Zpx × fy / γm0  =  1.0 × {sp.get("Zpx", 0):.2f} cm³ × {r["fy"]:.0f} / ({r["gm0"]:.2f} × 1000)
     =  {r["Mdz_kNm"]:.4f} kNm  [IS 800 Cl. 8.2.1.2]

Mdy  =  βb × Zpy × fy / γm0  =  1.0 × {sp.get("Zpy", 0):.2f} cm³ × {r["fy"]:.0f} / ({r["gm0"]:.2f} × 1000)
     =  {r["Mdy_kNm"]:.4f} kNm
</div>
""",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
<div class="formula-box">
Semi-compact section → use elastic section modulus

Mdz  =  Zx,design × fy / γm0  =  {r.get("z_major_design", sp.get("Zxx", 0)):.2f} × {r["fy"]:.0f} / ({r["gm0"]:.2f} × 1000)  =  {r["Mdz_kNm"]:.4f} kNm
Mdy  =  Zy,design × fy / γm0  =  {r.get("z_minor_design", sp.get("Zyy", 0)):.2f} × {r["fy"]:.0f} / ({r["gm0"]:.2f} × 1000)  =  {r["Mdy_kNm"]:.4f} kNm
</div>
""",
                unsafe_allow_html=True,
            )

    # ── Step 5: Biaxial Check ──────────────────────────────────
    with st.expander(
        "📌 Step 5 — Biaxial Bending Check  [IS 800:2007 Cl. 9.3.1.1]", expanded=True
    ):
        st.markdown(
            f"""
<div class="formula-box">
My / Mdy  +  Mz / Mdz  ≤  1.0

{r["My_kNm"]:.4f} / {r["Mdy_kNm"]:.4f}  +  {r["Mz_kNm"]:.4f} / {r["Mdz_kNm"]:.4f}  =  {r["biaxial_ratio"]:.4f}
</div>
""",
            unsafe_allow_html=True,
        )
        if r.get("biaxial_ok"):
            st.markdown(
                f'<div class="result-safe">✓ PASS — Biaxial ratio = <b>{r["biaxial_ratio"]:.4f}</b> ≤ 1.0</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="result-fail">✗ FAIL — Biaxial ratio = <b>{r["biaxial_ratio"]:.4f}</b> > 1.0</div>',
                unsafe_allow_html=True,
            )

    # ── Step 6: Shear ──────────────────────────────────────────
    with st.expander("📌 Step 6 — Shear Capacity Check  [IS 800:2007 Cl. 8.4.1]"):
        cf = r.get("cold_formed_checks") or {}
        if cf:
            shear_capacity_text = (
                f"Vd = Av × τdesign / γm0 = {r['Av_mm2']:.0f} × "
                f"{cf['tau_design_MPa']:.2f} / ({r['gm0']:.2f} × 1000) = {r['Vd_kN']:.4f} kN"
            )
        else:
            shear_capacity_text = (
                f"Vd = Av × fy / (√3 × γm0) = {r['Av_mm2']:.0f} × {r['fy']:.0f} / "
                f"(√3 × {r['gm0']:.2f} × 1000) = {r['Vd_kN']:.4f} kN"
            )
        st.markdown(
            f"""
<div class="formula-box">
Shear area:  Av  =  h × tw  =  {sp.get("h", 0)} × {sp.get("tw", 0)}  =  {r["Av_mm2"]:.0f} mm²

{shear_capacity_text}

Vz (applied)  =  {r["Vz_kN"]:.4f} kN
</div>
""",
            unsafe_allow_html=True,
        )
        if r.get("shear_ok"):
            st.markdown(
                f'<div class="result-safe">✓ PASS — Vz = {r["Vz_kN"]:.4f} kN ≤ Vd = {r["Vd_kN"]:.4f} kN  '
                f"({r['Vz_kN'] / r['Vd_kN'] * 100:.1f}% utilisation)</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="result-fail">✗ FAIL — Vz = {r["Vz_kN"]:.4f} kN > Vd = {r["Vd_kN"]:.4f} kN</div>',
                unsafe_allow_html=True,
            )

    if r.get("cold_formed_checks"):
        cf = r["cold_formed_checks"]
        cf_checks = cf.get("checks", {})
        with st.expander("📌 Cold-formed C/Z — Effective-width & Stability Checks"):
            st.markdown(
                f"""
<div class="formula-box">
Method: {cf.get("method", "Cold-formed effective-width checks")}

Effective widths:
  Web:    ρ = {cf["web"]["rho"]:.3f}, be = {cf["web"]["effective_width"]:.1f} mm
  Flange: ρ = {cf["flange"]["rho"]:.3f}, be = {cf["flange"]["effective_width"]:.1f} mm
  Lip:    ρ = {cf["lip"]["rho"]:.3f}, be = {cf["lip"]["effective_width"]:.1f} mm

Effective section:
  Aeff / Ag = {cf["area_eff_ratio"]:.3f}
  Zeff,x = {cf["Zxx_eff"]:.2f} cm³, Zeff,y = {cf["Zyy_eff"]:.2f} cm³
  Ieff,x = {cf["Ixx_eff"]:.2f} cm⁴

Stability / bearing:
  τcr = {cf["tau_cr_MPa"]:.2f} MPa, τdesign = {cf["tau_design_MPa"]:.2f} MPa
  Web crippling capacity = {cf["web_crippling_capacity_kN"]:.3f} kN
  Lip/flange = {cf["lip_to_flange"]:.3f}
</div>
""",
                unsafe_allow_html=True,
            )
            cf_df = pd.DataFrame(
                {
                    "Check": [
                        "Local buckling / effective width",
                        "Distortional geometry",
                        "Effective-width bending",
                        "Shear buckling",
                        "Web crippling at support",
                        "Effective-I deflection",
                    ],
                    "Status": [
                        "✅ PASS" if cf_checks.get("local_buckling_ok") else "❌ FAIL",
                        "✅ PASS" if cf_checks.get("distortional_ok") else "❌ FAIL",
                        (
                            "✅ PASS"
                            if cf_checks.get("effective_width_bending_ok")
                            else "❌ FAIL"
                        ),
                        "✅ PASS" if cf_checks.get("shear_buckling_ok") else "❌ FAIL",
                        "✅ PASS" if cf_checks.get("web_crippling_ok") else "❌ FAIL",
                        "✅ PASS" if cf_checks.get("serviceability_ok") else "❌ FAIL",
                    ],
                }
            )
            st.dataframe(cf_df.set_index("Check"), use_container_width=True)
            if cf_checks.get("overall_ok"):
                st.markdown(
                    '<div class="result-safe">✓ PASS — cold-formed effective-width and stability checks are satisfied.</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    '<div class="result-fail">✗ FAIL — one or more cold-formed effective-width/stability checks are not satisfied.</div>',
                    unsafe_allow_html=True,
                )

    # ── Step 7: Deflection ─────────────────────────────────────
    with st.expander("📌 Step 7 — Deflection Check  [IS 800:2007 Table 6]"):
        st.markdown(
            f"""
<div class="formula-box">
Service load (unfactored):  wz,ser  =  {r["wz_DL"] + r["wz_LL"]:.4f} N/mm

δ_max  =  5 × wz,ser × L⁴ / (384 × E × Izz)
       =  5 × {r["wz_DL"] + r["wz_LL"]:.4f} × ({span * 1000:.0f})⁴ / (384 × 2×10⁵ × {r.get("Ixx_design_cm4", sp.get("Ixx", 0)):.1f}×10⁴)
       =  {r["delta_max_mm"]:.3f} mm

Permissible:  L / 180  =  {span * 1000:.0f} / 180  =  {r["delta_limit_mm"]:.3f} mm
</div>
""",
            unsafe_allow_html=True,
        )
        if r.get("defl_ok"):
            st.markdown(
                f'<div class="result-safe">✓ PASS — δ = {r["delta_max_mm"]:.3f} mm ≤ L/180 = {r["delta_limit_mm"]:.3f} mm</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="result-fail">✗ FAIL — δ = {r["delta_max_mm"]:.3f} mm > L/180 = {r["delta_limit_mm"]:.3f} mm</div>',
                unsafe_allow_html=True,
            )

    # ── Step 8: LTB / Wind Uplift Restraint ───────────────────
    stability = r.get("stability_checks") or {}
    with st.expander(
        "📌 Step 8 — Lateral Torsional Buckling & Wind Uplift Restraint",
        expanded=True,
    ):
        st.markdown(
            f"""
<div class="formula-box">
Full section bending capacity assumption:
  Top compression flange restrained = {"YES" if stability.get("top_flange_restrained") else "NO"}
  Bottom/uplift flange restraint provided = {"YES" if stability.get("bottom_flange_restrained") else "NO"}

Wind uplift check:
  Governing uplift combo = {stability.get("governing_uplift_combo", "None")}
  wz,uplift = {stability.get("governing_uplift_wz_kNm", 0):.4f} kN/m
  Mz,uplift = |wz,uplift| × L² / 8 = {stability.get("uplift_moment_kNm", 0):.4f} kNm
  Uplift bending ratio = Mz,uplift / Mdz = {stability.get("uplift_ratio", 0):.4f}

Note: {stability.get("note", "Compression flange restraint must be verified for LTB and uplift reversal.")}
</div>
""",
            unsafe_allow_html=True,
        )
        if stability.get("overall_ok"):
            st.markdown(
                '<div class="result-safe">✓ PASS — Compression-flange restraint assumptions and uplift bending check are satisfied.</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="result-fail">✗ FAIL — Provide explicit LTB/uplift restraint verification or reduce bending capacity.</div>',
                unsafe_allow_html=True,
            )

    # ── Step 9: Lap / Splice Design ───────────────────────────
    lap = r.get("lap_design") or {}
    with st.expander(
        "📌 Step 9 — Purlin Lap / Splice Design  [Cold-formed C/Z only]",
        expanded=True,
    ):
        if lap.get("applicable"):
            st.markdown(
                f"""
<div class="formula-box">
Method: {lap.get("method", "Cold-formed C/Z nested purlin lap bolt group check at support")}

Lap length:
  Provided lap = {lap.get("provided_lap_mm", 0):.0f} mm
  Recommended minimum = max(0.10 × L, 600) = max(0.10 × {r["span_m"] * 1000:.0f}, 600) = {lap.get("recommended_lap_mm", 0):.0f} mm

Bolt group:
  Bolts = {lap.get("bolt_rows", 0)} rows × {lap.get("bolts_per_row", 0)} per row = {lap.get("bolt_count", 0)} bolts
  Diameter = {lap.get("bolt_dia_mm", 0):.0f} mm, hole = {lap.get("hole_dia_mm", 0):.0f} mm, fub = {lap.get("bolt_grade_fub", 0):.0f} MPa

Resultant support reaction:
  R = √(Vz² + Vy²) = √({r["Vz_kN"]:.4f}² + {r["Vy_kN"]:.4f}²) = {lap.get("support_reaction_kN", 0):.4f} kN

Bolt capacity per bolt:
  Vdsb = fub × Anb / (√3 × γmb) = {lap.get("bolt_shear_capacity_kN", 0):.4f} kN
  Vdpb = 2.5 × kb × d × t × fu / γmb = {lap.get("bolt_bearing_capacity_kN", 0):.4f} kN
  Vbolt = min(Vdsb, Vdpb) = {lap.get("bolt_capacity_kN", 0):.4f} kN

Group capacity:
  Vgroup = n × Vbolt = {lap.get("bolt_count", 0)} × {lap.get("bolt_capacity_kN", 0):.4f} = {lap.get("group_capacity_kN", 0):.4f} kN
  Utilisation = R / Vgroup = {lap.get("bolt_utilisation", 0):.4f}
</div>
""",
                unsafe_allow_html=True,
            )
            lap_status = bool(lap.get("overall_ok"))
            status_class = "result-safe" if lap_status else "result-fail"
            status_text = "✓ PASS" if lap_status else "✗ FAIL"
            st.markdown(
                f'<div class="{status_class}">{status_text} — Cold-formed lap length, bolt capacity, and minimum detailing checks are {"satisfied" if lap_status else "not satisfied"}.</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="result-safe">N/A — Lap/nested continuity is not applied to this {lap.get("section_family", "selected")} section.</div>',
                unsafe_allow_html=True,
            )
        st.caption(
            lap.get(
                "note",
                "Final lap detailing should be reviewed with project-specific continuity and erection requirements.",
            )
        )

    # ── Summary Table ──────────────────────────────────────────
    st.divider()
    st.markdown("### 📊 Design Summary")

    summary_rows = [
        {
            "Check": "Biaxial Bending",
            "Applied": f"{r['biaxial_ratio']:.4f}",
            "Capacity": "1.000",
            "Utilisation (%)": f"{r['biaxial_ratio'] * 100:.1f}",
            "Status": "✅ PASS" if r.get("biaxial_ok") else "❌ FAIL",
        },
        {
            "Check": "Shear Capacity",
            "Applied": f"Vz = {r['Vz_kN']:.4f} kN",
            "Capacity": f"Vd = {r['Vd_kN']:.4f} kN",
            "Utilisation (%)": f"{r.get('shear_ratio', 0) * 100:.1f}",
            "Status": "✅ PASS" if r.get("shear_ok") else "❌ FAIL",
        },
        {
            "Check": "Deflection",
            "Applied": f"δ = {r['delta_max_mm']:.3f} mm",
            "Capacity": f"L/180 = {r['delta_limit_mm']:.3f} mm",
            "Utilisation (%)": f"{r.get('defl_ratio', 0) * 100:.1f}",
            "Status": "✅ PASS" if r.get("defl_ok") else "❌ FAIL",
        },
        {
            "Check": "LTB / Wind Uplift Restraint",
            "Applied": f"Mz,uplift = {r.get('stability_checks', {}).get('uplift_moment_kNm', 0):.4f} kNm",
            "Capacity": f"Mdz = {r.get('Mdz_kNm', 0):.4f} kNm",
            "Utilisation (%)": f"{r.get('stability_checks', {}).get('uplift_ratio', 0) * 100:.1f}",
            "Status": (
                "✅ PASS"
                if r.get("stability_checks", {}).get("overall_ok")
                else "❌ FAIL"
            ),
        },
        {
            "Check": "Purlin Lap / Splice",
            "Applied": (
                f"R = {r.get('lap_design', {}).get('support_reaction_kN', 0):.4f} kN"
                if r.get("lap_design", {}).get("applicable")
                else "Not applicable"
            ),
            "Capacity": (
                f"Vgroup = {r.get('lap_design', {}).get('group_capacity_kN', 0):.4f} kN"
                if r.get("lap_design", {}).get("applicable")
                else "Cold-formed C/Z only"
            ),
            "Utilisation (%)": (
                f"{r.get('lap_design', {}).get('bolt_utilisation', 0) * 100:.1f}"
                if r.get("lap_design", {}).get("applicable")
                else "—"
            ),
            "Status": (
                "✅ PASS"
                if r.get("lap_design", {}).get("applicable")
                and r.get("lap_design", {}).get("overall_ok")
                else ("❌ FAIL" if r.get("lap_design", {}).get("applicable") else "N/A")
            ),
        },
    ]
    if r.get("cold_formed_checks"):
        cf_ok = r["cold_formed_checks"].get("checks", {}).get("overall_ok", False)
        summary_rows.append(
            {
                "Check": "Cold-formed effective-width/stability",
                "Applied": f"Aeff/Ag = {r['cold_formed_checks']['area_eff_ratio']:.3f}",
                "Capacity": "All CFS checks pass",
                "Utilisation (%)": "—",
                "Status": "✅ PASS" if cf_ok else "❌ FAIL",
            }
        )
    summary = pd.DataFrame(summary_rows)
    st.dataframe(summary.set_index("Check"), use_container_width=True)

    # ── AI Economy Predictor ───────────────────────────────────
    st.divider()
    st.markdown("### 🤖 Economy Predictor — Safe & Economical Section")
    economy = r.get("economy_prediction", {})
    if economy.get("recommendations"):
        if economy.get("current_economical"):
            st.success(economy.get("verdict", "Current section is economical."))
        else:
            st.warning(
                economy.get("verdict", "A lighter safe option may be available.")
            )

        best = economy.get("best_section") or {}
        ai_cols = st.columns(4)
        ai_cols[0].metric("Best Safe Section", best.get("section_name", "—"))
        ai_cols[1].metric("Best Weight", f"{best.get('weight_kg_m', 0):.1f} kg/m")
        ai_cols[2].metric(
            "Current Weight", f"{economy.get('current_weight_kg_m', 0):.1f} kg/m"
        )
        ai_cols[3].metric("Safe Candidates", economy.get("safe_candidate_count", 0))

        rec_df = pd.DataFrame(economy.get("recommendations", []))
        rec_df = rec_df.rename(
            columns={
                "section_name": "Section",
                "section_family": "Family",
                "weight_kg_m": "Weight (kg/m)",
                "governing_utilisation": "Governing Util.",
                "biaxial_ratio": "Biaxial",
                "shear_ratio": "Shear",
                "defl_ratio": "Deflection",
                "weight_saving_percent": "Weight Saving vs Current (%)",
            }
        )
        show_cols = [
            "Section",
            "Family",
            "Weight (kg/m)",
            "Governing Util.",
            "Biaxial",
            "Shear",
            "Deflection",
            "Weight Saving vs Current (%)",
        ]
        st.dataframe(
            rec_df[show_cols].style.format(
                {
                    "Weight (kg/m)": "{:.1f}",
                    "Governing Util.": "{:.3f}",
                    "Biaxial": "{:.3f}",
                    "Shear": "{:.3f}",
                    "Deflection": "{:.3f}",
                    "Weight Saving vs Current (%)": "{:.1f}",
                }
            ),
            hide_index=True,
            use_container_width=True,
        )
        st.caption(f"{economy.get('method', '')} {economy.get('note', '')}")
    else:
        st.info(
            "No safe economical alternative was found in the available section database "
            "for the current loading, restraint, and design-code assumptions."
        )

    # ── PDF Download ───────────────────────────────────────────
    st.divider()
    st.markdown("### 📄 Download Design Report (PDF)")
    pdf_bytes = generate_purlin_pdf(r, project=project_name)
    download_name = sec_name or r.get("section_name", "Purlin")
    st.download_button(
        label="⬇️  Download PDF Report",
        data=pdf_bytes,
        file_name=f"Purlin_Design_{download_name.replace(' ', '_')}.pdf",
        mime="application/pdf",
        use_container_width=True,
        type="primary",
    )
    st.caption(
        "The PDF contains step-by-step calculations with all formulae, references, "
        "load combinations, and section classification per IS 800:2007."
    )
