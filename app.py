import streamlit as st
import math

st.set_page_config(page_title="DNB & BTTS", page_icon="⚽", layout="centered")

# CSS responsive pur
st.html("""
<style>
    .block-container { padding: 4px !important; max-width: 100vw !important; }
    header, footer, [data-testid="stHeader"] { display: none !important; }
    div[data-testid="stVerticalBlock"] > div { gap: 2px !important; }
    
    .stTextInput div div input {
        text-align: center !important;
        font-weight: bold !important;
        padding: 1px !important;
        font-size: 0.8rem !important;
        height: 28px !important;
    }
    .stTextInput label {
        font-size: 0.65rem !important;
        margin-bottom: 0px !important;
        color: #94a3b8 !important;
    }
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        width: 100% !important;
        gap: 2px !important;
    }
    div[data-testid="column"] {
        width: 50% !important;
        flex: 1 1 50% !important;
        min-width: 0 !important;
        padding: 0px 1px !important;
    }
</style>
""")

st.html("<div style='text-align:center; font-weight:bold; color:#f8fafc; font-size:0.9rem;'>⚽ CALCULATEUR DNB & BTTS</div>")

# ---------------------------------------------------------
# 1. SAISIE STATISTIQUES xG
# ---------------------------------------------------------
col_dom, col_ext = st.columns(2)
with col_dom:
    st.html("<div style='font-size:0.68rem; font-weight:bold; color:#38bdf8;'>🏠 DOMICILE</div>")
    xgA_m_str = st.text_input("Marqués", value="1.67", key="xgA_m")
    xgA_c_str = st.text_input("Concédés", value="0.83", key="xgA_c")

with col_ext:
    st.html("<div style='font-size:0.68rem; font-weight:bold; color:#fb7185;'>✈️ EXTÉRIEUR</div>")
    xgB_m_str = st.text_input("Marqués", value="1.00", key="xgB_m")
    xgB_c_str = st.text_input("Concédés", value="1.33", key="xgB_c")

# ---------------------------------------------------------
# 2. COTES BETCLIC
# ---------------------------------------------------------
st.html("<div style='font-size:0.68rem; font-weight:bold; color:#f59e0b;'>📊 COTES BETCLIC</div>")
col_c1, col_c2 = st.columns(2)
with col_c1:
    bk_dnb1_str = st.text_input("DNB 1", value="1.63", key="bk_dnb1")
    bk_btts_oui_str = st.text_input("BTTS Oui", value="1.49", key="bk_btts_oui")
with col_c2:
    bk_dnb2_str = st.text_input("DNB 2", value="1.90", key="bk_dnb2")
    bk_btts_non_str = st.text_input("BTTS Non", value="2.33", key="bk_btts_non")

# Conversions
try: xgA_m = float(xgA_m_str)
except: xgA_m = 0.0
try: xgA_c = float(xgA_c_str)
except: xgA_c = 0.0
try: xgB_m = float(xgB_m_str)
except: xgB_m = 0.0
try: xgB_c = float(xgB_c_str)
except: xgB_c = 0.0

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
# 4. CARTE DE RÉSULTAT
# ---------------------------------------------------------
def render_card(title, bk, prob):
    fair = 1 / prob if prob > 0 else 0
    prob_quant = prob * 100
    prob_book = (1 / bk * 100) if bk > 0 else 0
    is_val = bk > fair and bk > 0
    val_edge = (((bk * prob) - 1) * 100) if is_val else 0
    is_high_conf = is_val and prob_quant >= 75.0

    if is_high_conf:
        bg, bd = "#064e3b", "1px solid #f59e0b"
        badge = f'<div style="background:#10b981; color:#000; font-weight:900; font-size:0.6rem; padding:1px; border-radius:2px; margin-top:2px;">🔥 ULTRA (+{val_edge:.1f}%)</div>'
    elif is_val:
        bg, bd = "#1e4620", "1px solid #10b981"
        badge = f'<div style="color:#10b981; font-weight:bold; margin-top:2px; font-size:0.6rem;">+{val_edge:.1f}% VALUE</div>'
    else:
        bg, bd = "#1e293b", "1px solid #334155"
        badge = '<div style="color:#ef4444; font-weight:bold; margin-top:2px; font-size:0.6rem;">NO VALUE</div>'

    st.html(f"""
    <div style="background:{bg}; border:{bd}; color:#fff; padding:4px 2px; border-radius:4px; text-align:center;">
        <div style="font-size:0.65rem; font-weight:bold; color:#cbd5e1;">{title}</div>
        <div style="font-size:1.05rem; font-weight:900; color:#38bdf8; line-height:1;">{prob_quant:.1f}%</div>
        <div style="font-size:0.58rem; color:#94a3b8;">Book: <b>{bk:.2f}</b> ({prob_book:.0f}%)</div>
        <div style="font-size:0.58rem; color:#f59e0b; font-weight:bold;">Mini: ≥ {fair:.2f}</div>
        {badge}
    </div>
    """)

st.html(f"""
<div style="background:#0f172a; padding:2px 4px; border-radius:4px; text-align:center; border:1px solid #334155;">
    <span style="color:#94a3b8; font-size:0.62rem; font-weight:bold;">xG ATTENDUS : </span>
    <span style="color:#f8fafc; font-size:0.8rem; font-weight:900; font-family:monospace;">{lambda_val:.2f} — {mu_val:.2f}</span>
</div>
""")

st.html("<div style='font-size:0.65rem; font-weight:bold; color:#f1f5f9;'>🎯 DNB</div>")
c_d1, c_d2 = st.columns(2)
with c_d1: render_card("DNB 1", bk_dnb1, p_dnb1)
with c_d2: render_card("DNB 2", bk_dnb2, p_dnb2)

st.html("<div style='font-size:0.65rem; font-weight:bold; color:#f1f5f9;'>🎯 BTTS</div>")
c_b1, c_b2 = st.columns(2)
with c_b1: render_card("BTTS OUI", bk_btts_oui, p_btts_oui)
with c_b2: render_card("BTTS NON", bk_btts_non, p_btts_non)
