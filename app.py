 import streamlit as st
import math

st.set_page_config(page_title="Calculateur DNB & BTTS", page_icon="⚽", layout="centered")

# CSS injecté pour aligner les 2 colonnes à 50% / 50% sur l'écran du téléphone
st.markdown("""
<style>
    /* 1. Supprimer les marges Streamlit pour utiliser toute la largeur */
    .block-container {
        padding-left: 0.2rem !important;
        padding-right: 0.2rem !important;
        padding-top: 0.5rem !important;
        padding-bottom: 0.5rem !important;
        max-width: 100% !important;
    }
    header, footer { display: none !important; }

    /* 2. Forcer les 2 colonnes à faire 50% de l'écran exactement (au trait rouge) */
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        width: 100% !important;
        gap: 4px !important;
    }
    div[data-testid="column"] {
        width: 50% !important;
        flex: 1 1 50% !important;
        min-width: 0 !important;
    }

    /* 3. Réduire la taille des inputs pour qu'ils rentrent dans leur moitié */
    .stNumberInput div div input {
        text-align: center !important;
        font-weight: bold !important;
        padding: 0px !important;
        font-size: 0.85rem !important;
        height: 32px !important;
    }
    .stNumberInput label {
        font-size: 0.7rem !important;
        margin-bottom: 2px !important;
        white-space: nowrap !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<h4 style='text-align: center; margin-bottom: 8px;'>⚽ CALCULATEUR DNB & BTTS</h4>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 1. xG (DOMICILE À GAUCHE / EXTÉRIEUR À DROITE)
# ---------------------------------------------------------
st.markdown("##### 📝 1. STATISTIQUES xG")
col_dom, col_ext = st.columns(2)

with col_dom:
    st.markdown("<div style='font-size: 0.75rem; font-weight: bold; color: #38bdf8;'>🏠 DOMICILE</div>", unsafe_allow_html=True)
    xgA_m = st.number_input("Marqués", value=1.67, step=0.01, key="xgA_m")
    xgA_c = st.number_input("Concédés", value=0.83, step=0.01, key="xgA_c")

with col_ext:
    st.markdown("<div style='font-size: 0.75rem; font-weight: bold; color: #fb7185;'>✈️ EXTÉRIEUR</div>", unsafe_allow_html=True)
    xgB_m = st.number_input("Marqués", value=1.00, step=0.01, key="xgB_m")
    xgB_c = st.number_input("Concédés", value=1.33, step=0.01, key="xgB_c")

# ---------------------------------------------------------
# 2. COTES BETCLIC (DNB & BTTS SÉPARÉS 50/50)
# ---------------------------------------------------------
st.markdown("##### 📊 2. COTES BETCLIC")
col_c1, col_c2 = st.columns(2)

with col_c1:
    bk_dnb1 = st.number_input("DNB 1", value=1.63, step=0.01, key="bk_dnb1")
    bk_btts_oui = st.number_input("BTTS Oui", value=1.49, step=0.01, key="bk_btts_oui")

with col_c2:
    bk_dnb2 = st.number_input("DNB 2", value=1.90, step=0.01, key="bk_dnb2")
    bk_btts_non = st.number_input("BTTS Non", value=2.33, step=0.01, key="bk_btts_non")

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
# 4. AFFICHAGE DES RÉSULTATS (Taille divisée par 2)
# ---------------------------------------------------------
st.markdown(
    f"""
    <div style="background-color: #0f172a; padding: 4px; border-radius: 4px; text-align: center; margin: 6px 0px; border: 1px solid #334155;">
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
        badge_html = f'<div style="background-color: #10b981; color: #000000; font-weight: 900; font-size: 0.65rem; padding: 2px; border-radius: 2px; text-align: center; margin-top: 2px;">🔥 ULTRA (+{val_edge:.1f}%)</div>'
    elif is_val:
        bg_color = "#1e4620"
        border = "1px solid #10b981"
        badge_html = f'<div style="color: #10b981; font-weight: bold; margin-top: 2px; font-size: 0.65rem;">+{val_edge:.1f}% VALUE</div>'
    else:
        bg_color = "#1e293b"
        border = "1px solid #334155"
        badge_html = '<div style="color: #ef4444; font-weight: bold; margin-top: 2px; font-size: 0.65rem;">NO VALUE</div>'
        
    return f'''<div style="background-color: {bg_color}; border: {border}; color: #ffffff; padding: 6px; border-radius: 6px; text-align: center;">
        <div style="font-size: 0.72rem; font-weight: bold; color: #cbd5e1;">{title}</div>
        <div style="font-size: 1.25rem; font-weight: 900; color: #38bdf8; line-height: 1.1;">{prob_quant:.1f}%</div>
        <div style="font-size: 0.65rem; color: #94a3b8;">Book: <b>{bk:.2f}</b> ({prob_book:.0f}%)</div>
        <div style="font-size: 0.65rem; color: #f59e0b; font-weight: bold;">Mini: ≥ {fair:.2f}</div>
        {badge_html}
    </div>'''

# MARCHÉ DNB
st.markdown("<div style='font-size: 0.75rem; font-weight: bold; margin-bottom: 2px;'>🎯 DNB</div>", unsafe_allow_html=True)
col_dnb1, col_dnb2 = st.columns(2)
with col_dnb1: st.markdown(build_card_html("DNB 1", bk_dnb1, p_dnb1), unsafe_allow_html=True)
with col_dnb2: st.markdown(build_card_html("DNB 2", bk_dnb2, p_dnb2), unsafe_allow_html=True)

# MARCHÉ BTTS
st.markdown("<div style='font-size: 0.75rem; font-weight: bold; margin-top: 4px; margin-bottom: 2px;'>🎯 BTTS</div>", unsafe_allow_html=True)
col_btts1, col_btts2 = st.columns(2)
with col_btts1: st.markdown(build_card_html("BTTS OUI", bk_btts_oui, p_btts_oui), unsafe_allow_html=True)
with col_btts2: st.markdown(build_card_html("BTTS NON", bk_btts_non, p_btts_non), unsafe_allow_html=True)
