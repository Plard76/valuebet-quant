import streamlit as st
import math

st.set_page_config(page_title="Calculateur DNB & BTTS", page_icon="⚽", layout="centered")

st.title("⚽ CALCULATEUR QUANT - DNB & BTTS")

# ---------------------------------------------------------
# 1. ÉTAPE 1 · ÉQUIPES (xG)
# ---------------------------------------------------------
st.markdown("### ÉTAPE 1 · STATISTIQUES xG")

col_dom, col_ext = st.columns(2)

with col_dom:
    st.markdown("**🏠 DOMICILE**")
    xgA_m = st.number_input("BUTS MARQUÉS / MATCH", value=1.67, step=0.01, key="xgA_m")
    xgA_c = st.number_input("BUTS ENCAISSÉS / MATCH", value=0.83, step=0.01, key="xgA_c")

with col_ext:
    st.markdown("**✈️ EXTÉRIEUR**")
    xgB_m = st.number_input("BUTS MARQUÉS / MATCH", value=1.00, step=0.01, key="xgB_m")
    xgB_c = st.number_input("BUTS ENCAISSÉS / MATCH", value=1.33, step=0.01, key="xgB_c")

st.write("")

# ---------------------------------------------------------
# 2. ÉTAPE 2 · COTES BETCLIC (DNB & BTTS UNIQUEMENT)
# ---------------------------------------------------------
st.markdown("### ÉTAPE 2 · COTES BETCLIC")

st.markdown("**MARCHÉ DRAW NO BET (DNB)**")
cd1, cd2 = st.columns(2)
bk_dnb1 = cd1.number_input("COTE DNB 1", value=1.63, step=0.01)
bk_dnb2 = cd2.number_input("COTE DNB 2", value=1.90, step=0.01)

st.markdown("**MARCHÉ LES 2 ÉQUIPES MARQUENT (BTTS)**")
cb1, cb2 = st.columns(2)
bk_btts_oui = cb1.number_input("COTE BTTS OUI", value=1.49, step=0.01)
bk_btts_non = cb2.number_input("COTE BTTS NON", value=2.33, step=0.01)

st.write("")

# ---------------------------------------------------------
# 3. CALCULS DU MODÈLE (DIXON-COLES / POISSON)
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

st.divider()

# ---------------------------------------------------------
# 4. RÉSULTATS & DÉTECTION VALUEBETS
# ---------------------------------------------------------
st.markdown(
    f"""
    <div style="background-color: #111827; padding: 12px; border-radius: 6px; text-align: center; margin-bottom: 20px; border: 1px solid #374151;">
        <div style="color: #9ca3af; font-size: 0.85rem; font-weight: bold; letter-spacing: 1px; margin-bottom: 4px;">BUTS ATTENDUS (λ - μ)</div>
        <div style="color: #ffffff; font-size: 2rem; font-weight: 900; font-family: monospace;">{lambda_val:.2f} — {mu_val:.2f}</div>
    </div>
    """,
    unsafe_allow_html=True
)

def render_pair_cards(title_left, bk_left, prob_left, title_right, bk_right, prob_right):
    def make_card_html(title, bk, prob):
        fair = 1 / prob if prob > 0 else 0
        prob_quant = prob * 100
        prob_book = (1 / bk * 100) if bk > 0 else 0
        is_val = bk > fair and bk > 0
        val_edge = (((bk * prob) - 1) * 100) if is_val else 0
        is_high_conf = is_val and prob_quant >= 75.0
        
        if is_high_conf:
            bg_color = "#064e3b"
            border = "2px solid #f59e0b"
            badge = f"""
            <div style="background-color: #10b981; color: #000000; font-weight: 900; font-size: 0.95rem; padding: 4px; border-radius: 4px; text-align: center; margin-top: 6px;">
                🔥 ULTRA VALUE (+{val_edge:.1f}%) [> 75%]
            </div>
            """
        elif is_val:
            bg_color = "#1e4620"
            border = "1px solid #10b981"
            badge = f'<div style="color: #10b981; font-weight: bold; margin-top: 6px;">+{val_edge:.1f}% VALUE</div>'
        else:
            bg_color = "#1f2937"
            border = "1px solid #374151"
            badge = '<div style="color: #ef4444; font-weight: bold; margin-top: 6px;">NO VALUE</div>'
            
        return f"""
        <div style="background-color: {bg_color}; border: {border}; color: #ffffff; padding: 14px; border-radius: 8px; text-align: center; margin-bottom: 10px;">
            <div style="font-size: 0.9rem; font-weight: bold; letter-spacing: 1px; margin-bottom: 6px;">{title}</div>
            <div style="font-size: 2rem; font-weight: 900; margin-bottom: 6px; color: #38bdf8;">{prob_quant:.1f}%</div>
            <div style="font-size: 0.85rem; color: #d1d5db;">Cote Betclic : <b>{bk:.2f}</b> ({prob_book:.1f}%)</div>
            <div style="font-size: 0.85rem; color: #f59e0b; font-weight: bold; margin-top: 4px;">Cote juste mini : ≥ {fair:.2f}</div>
            {badge}
        </div>
        """

    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown(make_card_html(title_left, bk_left, prob_left), unsafe_allow_html=True)
    with col_r:
        st.markdown(make_card_html(title_right, bk_right, prob_right), unsafe_allow_html=True)

st.markdown("#### 🎯 BILAN DRAW NO BET (DNB)")
render_pair_cards("DNB 1", bk_dnb1, p_dnb1, "DNB 2", bk_dnb2, p_dnb2)

st.markdown("#### 🎯 BILAN LES 2 ÉQUIPES MARQUENT (BTTS)")
render_pair_cards("BTTS OUI", bk_btts_oui, p_btts_oui, "BTTS NON", bk_btts_non, p_btts_non)
