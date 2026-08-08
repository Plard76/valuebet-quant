import streamlit as st
import requests
import re
import math

st.set_page_config(page_title="ValueBet Quant", page_icon="⚽", layout="centered")

st.title("⚽ ValueBet Quant - Calculateur Auto")
st.caption("Modèle Poisson & Dixon-Coles alimenté par URL ou saisie")

# Zone de saisie / scraping
url = st.text_input("🔗 Colle le lien du match FootyStats (facultatif) :", placeholder="https://footystats.org/fr/...")

xg_dom_m, xg_dom_c = 2.22, 0.87
xg_ext_m, xg_ext_c = 1.00, 1.20

if url:
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            decimals = re.findall(r'\b\d+[\.,]\d+\b', res.text)
            if len(decimals) >= 4:
                xg_dom_m = float(decimals[0].replace(',', '.'))
                xg_dom_c = float(decimals[1].replace(',', '.'))
                xg_ext_m = float(decimals[2].replace(',', '.'))
                xg_ext_c = float(decimals[3].replace(',', '.'))
                st.success("✅ Données extraites du lien avec succès !")
    except Exception as e:
        st.warning("Saisis directement les xG ci-dessous.")

st.divider()

# Formulaire d'entrée des xG
col1, col2 = st.columns(2)
with col1:
    st.subheader("🏠 Domicile")
    xgA_m = st.number_input("xG Marqués (Dom)", value=xg_dom_m, step=0.01)
    xgA_c = st.number_input("xG Concédés (Dom)", value=xg_dom_c, step=0.01)

with col2:
    st.subheader("✈️ Extérieur")
    xgB_m = st.number_input("xG Marqués (Ext)", value=xg_ext_m, step=0.01)
    xgB_c = st.number_input("xG Concédés (Ext)", value=xg_ext_c, step=0.01)

st.divider()

# Cotes Bookmaker
st.subheader("📊 Cotes Bookmaker")
c1, cN, c2 = st.columns(3)
with c1:
    bk_1 = st.number_input("Cote 1", value=2.10, step=0.05)
with cN:
    bk_N = st.number_input("Cote N", value=3.40, step=0.05)
with c2:
    bk_2 = st.number_input("Cote 2", value=3.80, step=0.05)

# Calculs Espérances
lambda_val = (xgA_m + xgB_c) / 2
mu_val = (xgB_m + xgA_c) / 2

def poisson(k, lmbda):
    return (math.pow(lmbda, k) * math.exp(-lmbda)) / math.factorial(k)

p_1, p_N, p_2 = 0.0, 0.0, 0.0
rho = -0.13

for x in range(7):
    for y in range(7):
        p = poisson(x, lambda_val) * poisson(y, mu_val)
        if x == 0 and y == 0: p *= (1 - lambda_val * mu_val * rho)
        elif x == 1 and y == 0: p *= (1 + mu * rho) if 'mu' in locals() else p
        elif x == 0 and y == 1: p *= (1 + lambda_val * rho)
        elif x == 1 and y == 1: p *= (1 - rho)

        if x > y: p_1 += p
        elif x == y: p_N += p
        else: p_2 += p

fair_1 = 1 / p_1 if p_1 > 0 else 0
fair_N = 1 / p_N if p_N > 0 else 0
fair_2 = 1 / p_2 if p_2 > 0 else 0

st.divider()
st.subheader("🎯 Bilan & ValueBets")

col_res1, col_res2, col_res3 = st.columns(3)
col_res1.metric("Victoire Dom (1)", f"Cote : {fair_1:.2f}", f"{((bk_1*p_1)-1)*100:.1f}% Value" if bk_1 > fair_1 else "No Value")
col_res2.metric("Match Nul (N)", f"Cote : {fair_N:.2f}", f"{((bk_N*p_N)-1)*100:.1f}% Value" if bk_N > fair_N else "No Value")
col_res3.metric("Victoire Ext (2)", f"Cote : {fair_2:.2f}", f"{((bk_2*p_2)-1)*100:.1f}% Value" if bk_2 > fair_2 else "No Value")
