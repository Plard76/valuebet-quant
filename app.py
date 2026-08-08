import streamlit as st
import math

st.set_page_config(page_title="Calculateur DNB & BTTS", page_icon="⚽", layout="centered")

# CSS personnalisé ultra-compact pour écran mobile
st.markdown("""
<style>
    /* Réduction globale des marges Streamlit */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
    }
    header, footer { visibility: hidden !important; }
    
    /* Inputs très compacts */
    .stNumberInput div div input {
        text-align: center !important;
        font-weight: bold !important;
        padding: 2px 4px !important;
        font-size: 0.85rem !important;
        height: 32px !important;
    }
    .stNumberInput label {
        font-size: 0.72rem !important;
        margin-bottom: 0px !important;
        white-space: nowrap !important;
    }
    
    /* Disposition côte à côte sur mobile (48% par colonne) */
    div[data-testid="column"] {
        width: 48% !important;
        flex: 1 1 48% !important;
        min-width: 48% !important;
        padding: 0px 2px !important;
    }
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 4px !important;
    }
    h5, h4 {
        margin-top: 4px !important;
        margin-bottom: 4px !important;
        font-size: 0.85rem !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<h3 style='text-align: center; margin-bottom: 6px; font-size: 1.1rem;'>⚽ CALCULATEUR DNB & BTTS</h3>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 1. COMPACT : STATISTIQUES xG
# ---------------------------------------------------------
st.markdown("##### 📝 1. STATISTIQUES xG")
c_xg1, c_xg2, c_xg3, c_xg4 = st.columns(4)
with c_xg1: xgA_m = st.number_input("Dom. Marq.", value=1.67, step=0.01, key="xgA_m")
with c_xg2: xgA_c = st.number_input("Dom. Conc.", value=0.83, step=0.01, key="xgA_c")
with c_xg3: xgB_m = st.number_input("Ext. Marq.", value=1.00, step=0.01, key="xgB_m")
with c_xg4: xgB_c = st.number_input("Ext. Conc.", value=1.33, step=0.01, key="xgB_c")

# ---------------------------------------------------------
# 2. COMPACT : COTES BETCLIC
# ---------------------------------------------------------
st.markdown("##### 📊 2. COTES BETCLIC")
c_bk1, c_bk2, c_bk3, c_bk4 = st.columns(4)
with c_bk1: bk_dnb1 = c_bk1.number_input("DNB 1", value=1.63, step=0.01, key="bk_dnb1")
with c_bk2: bk_dnb2 = c_bk2.number_input("DNB 2", value=1.90, step=0.01, key="bk_dnb2")
with c_bk3: bk_btts_oui = c_bk3.number_input("BTTS Oui", value=1.49, step=0.01, key="bk_btts_oui")
with c_bk4: bk_btts_non = c_bk4.number_input("BTTS Non", value=2.33, step=0.01, key="bk_btts_non")

# ---------------------------------------------------------
# 3. CALCULS DU MODÈLE DIXON-COLES
# ---------------------------------------------------------
lambda_val = (xgA_m + xgB_c) / 2
mu_val = (xgB_m + xgA_c) / 2

def poisson(k, lmbda):
    return (math.pow(lmbda, k) * math.exp(-lmbda)) / math.factorial(k)

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
# 4. RÉSULTATS CONDENSÉS
# ---------------------------------------------------------
st.markdown(
    f"""
    <div style="background-color: #0f172a; padding: 4px; border-radius: 4px; text-align: center; margin-top: 6px; margin-bottom: 6px; border: 1px solid #334155;">
        <span style="color: #94a3b8; font-size: 0.75rem; font-weight: bold;">BUTS ATTENDUS (λ - μ) : </span>
        <span style="color: #f8fafc; font-size: 1.1rem; font-weight: 900; font-family: monospace;">{lambda_val:.2f} — {mu_val:.2f}</span>
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
        border = "2px solid #f59e0b"
        badge_html = f'<div style="background-color: #10b981; color: #000000; font-weight: 900; font-size: 0.75rem; padding: 3px; border-radius: 3px; text-align: center; margin-top: 4px;">🔥 ULTRA (+{val_edge:.1f}%)</div>'
    elif is_val:
        bg_color = "#1e4620"
        border = "1px solid #10b981"
        badge_html = f'<div style="color: #10b981; font-weight: bold; margin-top: 4px; font-size: 0.75rem;">+{val_edge:.1f}% VALUE</div>'
    else:
        bg_color = "#1e293b"
        border = "1px solid #334155"
        badge_html = '<div style="color: #ef4444; font-weight: bold; margin-top: 4px; font-size: 0.75rem;">NO VALUE</div>'
        
    return f'''<div style="background-color: {bg_color}; border: {border}; color: #ffffff; padding: 6px; border-radius: 6px; text-align: center;">
        <div style="font-size: 0.75rem; font-weight: bold; color: #cbd5e1;">{title}</div>
        <div style="font-size: 1.4rem; font-weight: 900; color: #38bdf8; line-height: 1.1;">{prob_quant:.1f}%</div>
        <div style="font-size: 0.72rem; color: #94a3b8;">Book : <b>{bk:.2f}</b> ({prob_book:.0f}%)</div>
        <div style="font-size: 0.72rem; color: #f59e0b; font-weight: bold;">Mini : ≥ {fair:.2f}</div>
        {badge_html}
    </div>'''

# MARCHÉ DNB
st.markdown("<div style='font-size: 0.8rem; font-weight: bold; margin-bottom: 2px;'>🎯 DRAW NO BET (DNB)</div>", unsafe_allow_html=True)
col_dnb1, col_dnb2 = st.columns(2)
with col_dnb1: st.markdown(build_card_html("DNB 1", bk_dnb1, p_dnb1), unsafe_allow_html=True)
with col_dnb2: st.markdown(build_card_html("DNB 2", bk_dnb2, p_dnb2), unsafe_allow_html=True)

# MARCHÉ BTTS
st.markdown("<div style='font-size: 0.8rem; font-weight: bold; margin-top: 4px; margin-bottom: 2px;'>🎯 BTTS</div>", unsafe_allow_html=True)
col_btts1, col_btts2 = st.columns(2)
with col_btts1: st.markdown(build_card_html("BTTS OUI", bk_btts_oui, p_btts_oui), unsafe_allow_html=True)
with col_btts2: st.markdown(build_card_html("BTTS NON", bk_btts_non, p_btts_non), unsafe_allow_html=True)
