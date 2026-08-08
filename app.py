"""
ValueBet Quant - Modèle vs Betclic (v4 - 100% manuel)
========================================================

Plus aucune automatisation (ni cotes, ni xG) : le scraping FootyStats
renvoyait une erreur 403 depuis Streamlit Cloud (blocage probable des IP
datacenter), donc on repart sur une saisie 100% manuelle, mais organisée
pour aller vite : la disposition des cotes suit exactement l'ordre affiché
sur l'app Betclic, ligne par ligne :

  1) Résultat du match : 1 / N / 2
  2) Résultat du match (remboursé si nul) : DNB Domicile / DNB Extérieur
  3) Nombre total de buts : + de 2.5 / - de 2.5
  4) Les 2 équipes marquent : BTTS Oui / BTTS Non

Il suffit de descendre l'écran Betclic et de recopier dans le même ordre,
sans avoir à chercher où va quoi.
"""

import math
import streamlit as st

st.set_page_config(page_title="ValueBet Quant", page_icon="⚽", layout="centered")
st.title("⚽ ValueBet Quant - Modèle vs Betclic")

# ---------------------------------------------------------
# 1. STATISTIQUES xG
# ---------------------------------------------------------
st.subheader("📝 1. Statistiques xG")
st.caption("xG Domicile = stats de l'équipe qui reçoit, xG Extérieur = stats de l'équipe qui se déplace.")

col1, col2 = st.columns(2)
with col1:
    st.markdown("**🏠 Domicile**")
    xgA_m = st.number_input("xG Marqués (Dom)", value=1.80, step=0.01, key="xgA_m")
    xgA_c = st.number_input("xG Concédés (Dom)", value=0.90, step=0.01, key="xgA_c")
with col2:
    st.markdown("**✈️ Extérieur**")
    xgB_m = st.number_input("xG Marqués (Ext)", value=1.00, step=0.01, key="xgB_m")
    xgB_c = st.number_input("xG Concédés (Ext)", value=1.20, step=0.01, key="xgB_c")

st.divider()

# ---------------------------------------------------------
# 2. COTES BETCLIC — même ordre, même regroupement que dans l'app
# ---------------------------------------------------------
st.subheader("📊 2. Cotes Betclic")

st.markdown("**Résultat du match**")
c1, cN, c2 = st.columns(3)
bk_1 = c1.number_input("1", value=2.28, step=0.01, key="bk_1")
bk_N = cN.number_input("N", value=3.30, step=0.01, key="bk_N")
bk_2 = c2.number_input("2", value=2.77, step=0.01, key="bk_2")

st.markdown("**Résultat du match (remboursé si match nul)**")
cd1, cd2 = st.columns(2)
bk_dnb1 = cd1.number_input("DNB Domicile", value=1.63, step=0.01, key="bk_dnb1")
bk_dnb2 = cd2.number_input("DNB Extérieur", value=1.90, step=0.01, key="bk_dnb2")

st.markdown("**Nombre total de buts**")
co25, cu25 = st.columns(2)
bk_o25 = co25.number_input("+ de 2.5", value=1.70, step=0.01, key="bk_o25")
bk_u25 = cu25.number_input("- de 2.5", value=1.95, step=0.01, key="bk_u25")

st.markdown("**Les 2 équipes marquent**")
cbtts1, cbtts2 = st.columns(2)
bk_btts_yes = cbtts1.number_input("BTTS Oui", value=1.59, step=0.01, key="bk_btts_yes")
bk_btts_no = cbtts2.number_input("BTTS Non", value=2.13, step=0.01, key="bk_btts_no")

# ---------------------------------------------------------
# 3. CALCULS MODÈLE DIXON-COLES
# ---------------------------------------------------------
lambda_val = (xgA_m + xgB_c) / 2
mu_val = (xgB_m + xgA_c) / 2


def poisson(k, lmbda):
    return (math.pow(lmbda, k) * math.exp(-lmbda)) / math.factorial(k)


p_1, p_N, p_2 = 0.0, 0.0, 0.0
p_o25, p_btts = 0.0, 0.0
rho = -0.13

for x in range(7):
    for y in range(7):
        p = poisson(x, lambda_val) * poisson(y, mu_val)
        if x == 0 and y == 0:
            p *= (1 - lambda_val * mu_val * rho)
        elif x == 1 and y == 0:
            p *= (1 + mu_val * rho)
        elif x == 0 and y == 1:
            p *= (1 + lambda_val * rho)
        elif x == 1 and y == 1:
            p *= (1 - rho)

        if x > y:
            p_1 += p
        elif x == y:
            p_N += p
        else:
            p_2 += p

        if x + y > 2.5:
            p_o25 += p
        if x > 0 and y > 0:
            p_btts += p

p_u25 = 1 - p_o25
p_dnb1 = p_1 / (p_1 + p_2) if (p_1 + p_2) > 0 else 0
p_dnb2 = p_2 / (p_1 + p_2) if (p_1 + p_2) > 0 else 0

st.divider()
st.subheader("🎯 Bilan & Comparatif Probas")


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
        <div style="background-color: #10b981; color: #000000; font-weight: 900; font-size: 1.15rem; padding: 6px; border-radius: 6px; text-align: center; margin-top: 6px; box-shadow: 0 0 10px #10b981;">
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
        unsafe_allow_html=True,
    )


m1, m2, m3 = st.columns(3)
with m1:
    display_card("Victoire Dom (1)", bk_1, p_1)
    display_card("DNB Domicile", bk_dnb1, p_dnb1)
    display_card("+ de 2.5 buts", bk_o25, p_o25)
with m2:
    display_card("Match Nul (N)", bk_N, p_N)
    display_card("- de 2.5 buts", bk_u25, p_u25)
with m3:
    display_card("Victoire Ext (2)", bk_2, p_2)
    display_card("DNB Extérieur", bk_dnb2, p_dnb2)
    display_card("BTTS Oui", bk_btts_yes, p_btts)
