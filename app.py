import streamlit as st
import math

st.set_page_config(page_title="ValueBet Quant", page_icon="⚽", layout="centered")

st.title("⚽ ValueBet Quant - Modèle Dixon-Coles")

# =========================================================
# 1. PARTIE xG : GRILLE 2x2 (DOMICILE À GAUCHE / EXTÉRIEUR À DROITE)
# =========================================================
st.subheader("📝 1. Statistiques xG")

col_dom, col_ext = st.columns(2)

with col_dom:
    st.markdown("### 🏠 Domicile")
    xgA_m = st.number_input("xG Marqués (Dom)", value=1.80, step=0.01, key="xgA_m")
    xgA_c = st.number_input("xG Concédés (Dom)", value=0.90, step=0.01, key="xgA_c")

with col_ext:
    st.markdown("### ✈️ Extérieur")
    xgB_m = st.number_input("xG Marqués (Ext)", value=1.00, step=0.01, key="xgB_m")
    xgB_c = st.number_input("xG Concédés (Ext)", value=1.20, step=0.01, key="xgB_c")

st.divider()

# =========================================================
# 2. RÉSULTAT DU CALCUL DE POISSON
# =========================================================
lambda_val = (xgA_m + xgB_c) / 2
mu_val = (xgB_m + xgA_c) / 2

st.subheader("📊 2. Résultat du calcul de Poisson (Espérance de buts)")

col_p1, col_p2 = st.columns(2)
with col_p1:
    st.info(f"⚽ **Espérance Buts Domicile (λ) :** `{lambda_val:.2f}`")
with col_p2:
    st.info(f"⚽ **Espérance Buts Extérieur (μ) :** `{mu_val:.2f}`")

st.divider()

# =========================================================
# 3. SAISIE DES COTES BETCLIC (DISPOSÉES COMME SUR BETCLIC)
# =========================================================
st.subheader("📊 3. Cotes Betclic")

# 1N2
st.markdown("**Résultat du match (1N2)**")
c1, cN, c2 = st.columns(3)
bk_1 = c1.number_input("1 (Dom)", value=2.28, step=0.01, key="bk_1")
bk_N = cN.number_input("N (Nul)", value=3.30, step=0.01, key="bk_N")
bk_2 = c2.number_input("2 (Ext)", value=2.77, step=0.01, key="bk_2")

# DNB
st.markdown("**Remboursé si match nul (DNB)**")
cd1, cd2 = st.columns(2)
bk_dnb1 = cd1.number_input("DNB 1", value=1.63, step=0.01, key="bk_dnb1")
bk_dnb2 = cd2.number_input("DNB 2", value=1.90, step=0.01, key="bk_dnb2")

# Over / Under 2.5
st.markdown("**Nombre total de buts (2.5)**")
co25, cu25 = st.columns(2)
bk_o25 = co25.number_input("+ de 2.5", value=1.70, step=0.01, key="bk_o25")
bk_u25 = cu25.number_input("- de 2.5", value=1.95, step=0.01, key="bk_u25")

# BTTS (Oui à gauche, Non à droite)
st.markdown("**Les 2 équipes marquent (BTTS)**")
cbtts_oui, cbtts_non = st.columns(2)
bk_btts_oui = cbtts_oui.number_input("Oui", value=1.59, step=0.01, key="bk_btts_oui")
bk_btts_non = cbtts_non.number_input("Non", value=2.13, step=0.01, key="bk_btts_non")

# =========================================================
# 4. CALCULS DU MODÈLE DIXON-COLES
# =========================================================
def poisson(k, lmbda):
    return (math.pow(lmbda, k) * math.exp(-lmbda)) / math.factorial(k)

p_1, p_N, p_2 = 0.0, 0.0, 0.0
p_o25, p_btts_oui = 0.0, 0.0
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

        if x + y > 2.5: p_o25 += p
        if x > 0 and y > 0: p_btts_oui += p

p_u25 = 1.0 - p_o25
p_btts_non = 1.0 - p_btts_oui
p_dnb1 = p_1 / (p_1 + p_2) if (p_1 + p_2) > 0 else 0
p_dnb2 = p_2 / (p_1 + p_2) if (p_1 + p_2) > 0 else 0

st.divider()

# =========================================================
# 5. BILAN & DÉTECTION VALUEBETS
# =========================================================
st.subheader("🎯 4. Bilan & Comparatif Probas")

def display_card(title, bk, prob):
    fair = 1 / prob if prob > 0 else 0
    prob_quant = prob * 100
    prob_book = (1 / bk * 100) if bk > 0 else 0
    
    is_val = bk > fair and bk > 0
    val_edge = (((bk * prob) - 1) * 100) if is_val else 0
    
    is_high_conf = is_val and prob_quant >= 75.0
    
    if is_high_conf:
        card_bg = "background-color: #064e3b; border: 2px solid #f59e0b;"
        badge = f"""
        <div style="background-color: #10b981; color: #000000; font-weight: 900; font-size: 1.1rem; padding: 6px; border-radius: 6px; text-align: center; margin-top: 6px; box-shadow: 0 0 10px #10b981;">
            🔥 ULTRA VALUE (+{val_edge:.1f}%) [PROBA > 75%]
        </div>
        """
    elif is_val:
        card_bg = "background-color: #1e293b; border: 1px solid #334155;"
        badge = f'<span style="color: #10b981; font-weight: bold; font-size: 1.1rem;">+{val_edge:.1f}% VALUE</span>'
    else:
        card_bg = "background-color: #1e293b; border: 1px solid #334155;"
        badge = '<span style="color: #ef4444; font-weight: bold; font-size: 1.1rem;">NO VALUE</span>'
        
    st.markdown(
        f"""
        <div style="{card_bg} padding: 14px; border-radius: 10px; margin-bottom: 12px;">
            <div style="font-size: 1rem; color: #f1f5f9; font-weight: bold; margin-bottom: 6px;">{title}</div>
            <div style="font-size: 1.1rem; color: #cbd5e1; margin-bottom: 8px;">
                Cote Est. : <b style="color: #ffffff;">{fair:.2f}</b> | Book : <b style="color: #f59e0b;">{bk:.2f}</b>
            </div>
            <div style="background-color: #0f172a; padding: 8px; border-radius: 6px; margin-bottom: 8px;">
                <div style="font-size: 1.05rem; color: #38bdf8; font-weight: bold;">📊 Proba Modèle : {prob_quant:.1f}%</div>
                <div style="font-size: 1.05rem; color: #fb7185; font-weight: bold;">🏢 Proba Betclic : {prob_book:.1f}%</div>
            </div>
            <div>{badge}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

m1, m2, m3 = st.columns(3)
with m1:
    display_card("Victoire Dom (1)", bk_1, p_1)
    display_card("DNB 1", bk_dnb1, p_dnb1)
    display_card("Over 2.5", bk_o25, p_o25)
    display_card("BTTS Oui", bk_btts_oui, p_btts_oui)

with m2:
    display_card("Match Nul (N)", bk_N, p_N)
    display_card("Under 2.5", bk_u25, p_u25)
    display_card("BTTS Non", bk_btts_non, p_btts_non)

with m3:
    display_card("Victoire Ext (2)", bk_2, p_2)
    display_card("DNB 2", bk_dnb2, p_dnb2)
