import streamlit as st
import requests
import math

st.set_page_config(page_title="ValueBet Quant", page_icon="⚽", layout="centered")

st.title("⚽ ValueBet Quant - Modèle vs Betclic")

API_KEY = "f38ee008fcce89b9c2f13d577cbd1745"

# ---------------------------------------------------------
# 1. SAISIE DES xG
# ---------------------------------------------------------
st.subheader("📝 1. Statistiques xG")

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
# 2. CHARGEMENT API OU SAISIE MANUELLE DES COTES
# ---------------------------------------------------------
st.subheader("📊 2. Cotes Bookmaker (Betclic)")

leagues = {
    "Ligue 1 (France)": "soccer_france_ligue_one",
    "Ligue 2 (France)": "soccer_france_ligue_two",
    "Bundesliga 2 (Allemagne)": "soccer_germany_bundesliga2",
    "Eliteserien (Norvège)": "soccer_norway_eliteserien",
    "Liga I (Roumanie)": "soccer_romania_liga_1",
    "Premiership (Écosse)": "soccer_spl",
    "Premier Division (Irlande)": "soccer_eircom_league",
    "Bundesliga (Autriche)": "soccer_austria_bundesliga",
    "Liga Profesional (Argentine)": "soccer_argentina_primera_division",
    "Liga MX (Mexique)": "soccer_mexico_ligamx",
    "MLS (USA)": "soccer_usa_mls",
    "Premier League (Angleterre)": "soccer_epl",
    "La Liga (Espagne)": "soccer_spain_la_liga",
    "Serie A (Italie)": "soccer_italy_serie_a",
    "Bundesliga (Allemagne)": "soccer_germany_bundesliga",
    "Ligue des Champions": "soccer_uefa_champs_league"
}

selected_league = st.selectbox("Sélectionne la compétition :", list(leagues.keys()))

bk_1_val, bk_N_val, bk_2_val = 2.28, 3.30, 2.77
bk_o25_val, bk_u25_val, bk_btts_val = 1.70, 1.95, 1.59

league_key = leagues[selected_league]
odds_url = f"https://api.the-odds-api.com/v4/sports/{league_key}/odds/?apiKey={API_KEY}&regions=eu&markets=h2h"

try:
    r = requests.get(odds_url, timeout=4)
    if r.status_code == 200:
        data = r.json()
        if isinstance(data, list) and len(data) > 0:
            matches_dict = {f"{m['home_team']} vs {m['away_team']}": m for m in data}
            selected_match = st.selectbox("Charger les cotes d'un match (Optionnel) :", ["-- Manuel / Choisir un match --"] + list(matches_dict.keys()))
            
            if selected_match != "-- Manuel / Choisir un match --":
                m_data = matches_dict[selected_match]
                h_name, a_name = m_data['home_team'], m_data['away_team']
                bookmakers = m_data.get('bookmakers', [])
                bm = next((b for b in bookmakers if b['key'] == 'betclic'), bookmakers[0] if bookmakers else None)
                if bm:
                    for market in bm.get('markets', []):
                        if market['key'] == 'h2h':
                            for o in market['outcomes']:
                                if o['name'] == h_name: bk_1_val = float(o['price'])
                                elif o['name'] == a_name: bk_2_val = float(o['price'])
                                else: bk_N_val = float(o['price'])
except Exception:
    pass

st.markdown("**Saisie / Ajustement rapide des cotes Betclic :**")
c1, cN, c2 = st.columns(3)
bk_1 = c1.number_input("Cote 1", value=bk_1_val, step=0.01)
bk_N = cN.number_input("Cote N", value=bk_N_val, step=0.01)
bk_2 = c2.number_input("Cote 2", value=bk_2_val, step=0.01)

cd1, cd2 = st.columns(2)
bk_dnb1 = cd1.number_input("DNB 1", value=1.63, step=0.01)
bk_dnb2 = cd2.number_input("DNB 2", value=1.90, step=0.01)

co25, cu25, cbtts = st.columns(3)
bk_o25 = co25.number_input("Over 2.5", value=bk_o25_val, step=0.01)
bk_u25 = cu25.number_input("Under 2.5", value=bk_u25_val, step=0.01)
bk_btts = cbtts.number_input("BTTS Oui", value=bk_btts_val, step=0.01)

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
        if x == 0 and y == 0: p *= (1 - lambda_val * mu_val * rho)
        elif x == 1 and y == 0: p *= (1 + mu_val * rho)
        elif x == 0 and y == 1: p *= (1 + lambda_val * rho)
        elif x == 1 and y == 1: p *= (1 - rho)

        if x > y: p_1 += p
        elif x == y: p_N += p
        else: p_2 += p

        if x + y > 2.5: p_o25 += p
        if x > 0 and y > 0: p_btts += p

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
    
    if is_val:
        badge = f'<span style="color: #10b981; font-weight: bold; font-size: 1.1rem;">+{val_edge:.1f}% VALUE</span>'
    else:
        badge = '<span style="color: #ef4444; font-weight: bold; font-size: 1.1rem;">NO VALUE</span>'
        
    st.markdown(
        f"""
        <div style="background-color: #1e293b; padding: 14px; border-radius: 10px; margin-bottom: 12px; border: 1px solid #334155;">
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

with m2:
    display_card("Match Nul (N)", bk_N, p_N)
    display_card("Under 2.5", bk_u25, p_u25)

with m3:
    display_card("Victoire Ext (2)", bk_2, p_2)
    display_card("DNB 2", bk_dnb2, p_dnb2)
    display_card("BTTS Oui", bk_btts, p_btts)
