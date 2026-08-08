import streamlit as st
import math

st.set_page_config(page_title="DNB & BTTS", page_icon="⚽", layout="centered")

# CSS agressif pour réduire la taille globale et tout faire tenir sans scroll
st.markdown("""
<style>
    .block-container {
        padding: 0.5rem 0.2rem !important;
    }
    header, footer { display: none !important; }
    
    /* Suppression des espaces vides */
    div[data-testid="stVerticalBlock"] > div {
        gap: 0.2rem !important;
    }
    
    /* Inputs ultra-compacts sans boutons -/+ */
    .stTextInput div div input {
        text-align: center !important;
        font-weight: bold !important;
        padding: 1px 2px !important;
        font-size: 0.8rem !important;
        height: 28px !important;
        min-height: 28px !important;
    }
    .stTextInput label {
        font-size: 0.65rem !important;
        margin-bottom: 0px !important;
        white-space: nowrap !important;
        color: #94a3b8 !important;
    }
    
    /* Forcer 2 colonnes strictes sur mobile */
    div[data-testid="column"] {
        width: 49% !important;
        flex: 1 1 49% !important;
        min-width: 49% !important;
        padding: 0px 1px !important;
    }
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 2px !important;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 1. ÉTAPE 1 : xG EN 2 COLONNES (DOMICILE / EXTÉRIEUR)
# ---------------------------------------------------------
c_dom, c_ext = st.columns(2)
with c_dom:
    st.markdown("<div style='font-size:0.75rem; font-weight:bold; color:#38bdf8;'>🏠 DOMICILE (xG)</div>", unsafe_allow_html=True)
    xgA_m_str = st.text_input("Marqués", value="1.67", key="xgA_m")
    xgA_c_str = st.text_input("Concédés", value="0.83", key="xgA_c")

with c_ext:
    st.markdown("<div style='font-size:0.75rem; font-weight:bold; color:#fb7185;'>✈️ EXTÉRIEUR (xG)</div>", unsafe_allow_html=True)
    xgB_m_str = st.text_input("Marqués", value="1.00", key="xgB_m")
    xgB_c_str = st.text_input("Concédés", value="1.33", key="xgB_c")

# Conversion sécurisée des inputs
try: xgA_m = float(xgA_m_str)
except: xgA_m = 0.0
try: xgA_c = float(xgA_c_str)
except: xgA_c = 0.0
try: xgB_m = float(xgB_m_str)
except: xgB_m = 0.0
try: xgB_c = float(xgB_c_str)
except: xgB_c = 0.0

# ---------------------------------------------------------
# 2. ÉTAPE 2 : COTES BETCLIC EN 2 COLONNES
# ---------------------------------------------------------
st.markdown("<div style='font-size:0.75rem; font-weight:bold; color:#f59e0b; margin-top:4px;'>📊 COTES BETCLIC</div>", unsafe_allow_html=True)
c_c1, c_c2 = st.columns(2)
with c_c1:
    bk_dnb1_str = st.text_input("DNB 1", value="1.63", key="bk_dnb1")
    bk_btts_oui_str = st.text_input("BTTS Oui", value="1.49", key="bk_btts_oui")
with c_c2:
    bk_dnb2_str = st.text_input("DNB 2", value="1.90", key="bk_dnb2")
    bk_btts_non_str = st.text_input("BTTS Non", value="2.33", key="bk_btts_non")

try: bk_dnb1 = float(bk_dnb1_str)
except: bk_dnb1 = 1.0
try: bk_dnb2 = float(bk_dnb2_str)
except: bk_dnb2 = 1.0
try: bk_btts_oui = float(bk_btts_oui_str)
except: bk_btts_oui = 1.0
try: bk_btts_non = float(bk_btts_non_str)
except: bk_btts_non = 1.0

# ---------------------------------------------------------
# 3. CALCULS DU MODÈLE DIXON-COLES
# ---------------------------------------------------------
lambda_val = (xgA_m + xgB_c) / 2
mu_val = (xgB_m + xgA_c) / 2

def poisson(k, lmbda):
    return (math.pow(lmbda, k) * math.exp(-lmbda)) / math.factorial(k) if lmbda > 0 else 0

p_1, p_N, p_2 = 0.0, 0.0, 0.0
p_btts_oui = 0.0
rho = -0.13

for x in range(7):
    for y in range(7):
        p = poisson(x, lambda_val) * poisson(y, mu_val)
        if x == 0 and y == 0: p *= (1 - lambda_val * mu_val * rho)
        elif x == 1 and y == 0: p *= (1 + mu_val * rho)
        elif x == 0 and y == 1: p *= (1 + lambda_val * rho)
        elif x == 1 and y == 1: p *= (1 - rho)

        if x > y: p_1 += p
        elif x == y: p_N += p
        else: p_2 += p

        if x > 0 and y > 0: p_btts_oui += p

p_btts_non = 1.0 - p_btts_oui
p_dnb1 = p_1 / (p_1 + p_2) if (p_1 + p_2) > 0 else 0
p_dnb2 = p_2 / (p_1 + p_2) if (p_1 + p_2) > 0 else 0

# ---------------------------------------------------------
# 4. CARTE CONDENSÉE ULTRA-FIT
# ---------------------------------------------------------
st.markdown(
    f"""
    <div style="background-color: #0f172a; padding: 2px 6px; border-radius: 4px; text-align: center; margin: 4px 0px; border: 1px solid #334155;">
        <span style="color: #94a3b8; font-size: 0.7rem; font-weight: bold;">xG ATTENDUS : </span>
        <span style="color: #f8fafc; font-size: 0.95rem; font-weight: 900; font-family: monospace;">{lambda_val:.2f} — {mu_val:.2f}</span>
    </div>
    """,
    unsafe_allow_html=True
)

def build_card_html(title, bk, prob):
    fair = 1 / prob if prob > 0 else 0
    prob_quant = prob * 100
    prob_book = (1 / bk * 100) if bk > 0 else 0
    
    is_val = bk > fair and bk > 0
    val_edge = (((bk * prob) - 1) * 100) if is_val else 0
    is_high_conf = is_val and prob_quant >= 75.0
    
    if is_high_conf:
        bg_color = "#064e3b"
        border = "1px solid #f59e0b"
        badge_html = f'<div style="background-color: #10b981; color: #000; font-weight: 900; font-size: 0.68rem; padding: 1px; border-radius: 2px; text-align: center; margin-top: 2px;">🔥 ULTRA (+{val_edge:.1f}%)</div>'
    elif is_val:
        bg_color = "#1e4620"
        border = "1px solid #10b981"
        badge_html = f'<div style="color: #10b981; font-weight: bold; margin-top: 2px; font-size: 0.68rem;">+{val_edge:.1f}% VALUE</div>'
    else:
        bg_color = "#1e293b"
        border = "1px solid #334155"
        badge_html = '<div style="color: #ef4444; font-weight: bold; margin-top: 2px; font-size: 0.68rem;">NO VALUE</div>'
        
    return f'''<div style="background-color: {bg_color}; border: {border}; color: #ffffff; padding: 4px; border-radius: 4px; text-align: center;">
        <div style="font-size: 0.7rem; font-weight: bold; color: #cbd5e1;">{title}</div>
        <div style="font-size: 1.2rem; font-weight: 900; color: #38bdf8; line-height: 1;">{prob_quant:.1f}%</div>
        <div style="font-size: 0.65rem; color: #94a3b8;">Book: <b>{bk:.2f}</b> ({prob_book:.0f}%)</div>
        <div style="font-size: 0.65rem; color: #f59e0b; font-weight: bold;">Mini: ≥ {fair:.2f}</div>
        {badge_html}
    </div>'''

# MARCHÉ DNB
st.markdown("<div style='font-size: 0.72rem; font-weight: bold; margin-bottom: 2px;'>🎯 DNB</div>", unsafe_allow_html=True)
col_dnb1, col_dnb2 = st.columns(2)
with col_dnb1: st.markdown(build_card_html("DNB 1", bk_dnb1, p_dnb1), unsafe_allow_html=True)
with col_dnb2: st.markdown(build_card_html("DNB 2", bk_dnb2, p_dnb2), unsafe_allow_html=True)

# MARCHÉ BTTS
st.markdown("<div style='font-size: 0.72rem; font-weight: bold; margin-top: 2px; margin-bottom: 2px;'>🎯 BTTS</div>", unsafe_allow_html=True)
col_btts1, col_btts2 = st.columns(2)
with col_btts1: st.markdown(build_card_html("BTTS OUI", bk_btts_oui, p_btts_oui), unsafe_allow_html=True)
with col_btts2: st.markdown(build_card_html("BTTS NON", bk_btts_non, p_btts_non), unsafe_allow_html=True)
