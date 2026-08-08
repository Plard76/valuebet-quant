import streamlit as st
import requests
import math

st.set_page_config(page_title="ValueBet Quant", page_icon="⚽", layout="centered")

st.title("⚽ ValueBet Quant - Cotes Betclic & FR")

API_KEY = "f38ee008fcce89b9c2f13d577cbd1745"

# ---------------------------------------------------------
# 1. SAISIE DES xG
# ---------------------------------------------------------
st.subheader("📝 1. Entre les 4 xG")

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
# 2. CHARGEMENT AUTOMATIQUE DES COTES VIA L'API
# ---------------------------------------------------------
st.subheader("⚡ 2. Cotes Automatiques")

leagues = {
    "Ligue 1": "soccer_france_ligue_one",
    "Premier League": "soccer_epl",
    "La Liga": "soccer_spain_la_liga",
    "Serie A": "soccer_italy_serie_a",
    "Bundesliga": "soccer_germany_bundesliga",
    "Ligue des Champions": "soccer_uefa_champs_league",
    "MLS (USA)": "soccer_usa_mls"
}

selected_league = st.selectbox("Sélectionne la compétition :", list(leagues.keys()))

bk_1_val, bk_N_val, bk_2_val = 2.10, 3.40, 3.80
bk_o25_val, bk_u25_val, bk_btts_val = 1.95, 1.85, 1.80

league_key = leagues[selected_league]

# Requête ciblant en priorité Betclic, Unibet et Winamax
odds_url = f"https://api.the-odds-api.com/v4/sports/{league_key}/odds/?apiKey={API_KEY}&regions=eu&markets=h2h&bookmakers=betclic,unibet_eu,winamax"

try:
    r = requests.get(odds_url, timeout=5)
    if r.status_code == 200:
        data = r.json()
        if isinstance(data, list) and len(data) > 0:
            matches_dict = {f"{m['home_team']} vs {m['away_team']}": m for m in data}
            selected_match = st.selectbox("Choisis le match :", ["-- Sélectionner --"] + list(matches_dict.keys()))
            
            if selected_match != "-- Sélectionner --":
                m_data = matches_dict[selected_match]
                h_name = m_data['home_team']
                a_name = m_data['away_team']
                
                bookmakers = m_data.get('bookmakers', [])
                
                # Ordre de préférence : Betclic > Unibet > Winamax > Autre
                selected_bm = None
                for target_bm in ['betclic', 'unibet_eu', 'winamax']:
                    selected_bm = next((b for b in bookmakers if b['key'] == target_bm), None)
                    if selected_bm:
                        break
                if not selected_bm and len(bookmakers) > 0:
                    selected_bm = bookmakers[0]
                
                if selected_bm:
                    for market in selected_bm.get('markets', []):
                        if market['key'] == 'h2h':
                            for o in market['outcomes']:
                                if o['name'] == h_name: bk_1_val = float(o['price'])
                                elif o['name'] == a_name: bk_2_val = float(o['price'])
                                else: bk_N_val = float(o['price'])
                    st.success(f"🎯 Cotes réelles chargées depuis **{selected_bm['title']}** !")
        else:
            st.info("Aucun match à venir coté sur Betclic/Unibet pour ce championnat.")
    else:
        st.warning(f"⚠️ Code réponse API : {r.status_code}")
except Exception as e:
    st.error(f"Erreur de connexion : {e}")

bk_dnb1_val = round(bk_1_val * (1 - (1 / bk_N_val)), 2) if bk_N_val > 0 else 1.50
bk_dnb2_val = round(bk_2_val * (1 - (1 / bk_N_val)), 2) if bk_N_val > 0 else 2.60

st.divider()

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

st.subheader("🎯 Bilan & Détection ValueBets")

def display_card(title, bk, prob):
    fair = 1 / prob if prob > 0 else 0
    prob_pct = prob * 100
    is_val = bk > fair and bk > 0
    val_edge = (((bk * prob) - 1) * 100) if is_val else 0
    
    if is_val:
        badge = f'<span style="color: #10b981; font-weight: bold;">+{val_edge:.1f}% VALUE</span>'
    else:
        badge = '<span style="color: #ef4444; font-weight: bold;">NO VALUE</span>'
        
    st.markdown(
        f"""
        <div style="background-color: #1e293b; padding: 12px; border-radius: 8px; margin-bottom: 12px; border: 1px solid #334155;">
            <div style="font-size: 0.85rem; color: #94a3b8; font-weight: bold; margin-bottom: 4px;">{title}</div>
            <div style="font-size: 0.95rem; color: #f8fafc;">Cote Est. : <b>{fair:.2f}</b> | Book : <b>{bk:.2f}</b></div>
            <div style="font-size: 0.8rem; color: #3b82f6; font-weight: bold; margin-top: 2px;">Proba estimée : {prob_pct:.1f}%</div>
            <div style="font-size: 0.9rem; margin-top: 4px;">{badge}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

m1, m2, m3 = st.columns(3)
with m1:
    display_card("Victoire Dom (1)", bk_1_val, p_1)
    display_card("DNB 1", bk_dnb1_val, p_dnb1)
    display_card("Over 2.5", bk_o25_val, p_o25)

with m2:
    display_card("Match Nul (N)", bk_N_val, p_N)
    display_card("Under 2.5", bk_u25_val, p_u25)

with m3:
    display_card("Victoire Ext (2)", bk_2_val, p_2)
    display_card("DNB 2", bk_dnb2_val, p_dnb2)
    display_card("BTTS Oui", bk_btts_val, p_btts)
