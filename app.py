import streamlit as st
import requests
import math
from datetime import datetime, timedelta, timezone

st.set_page_config(page_title="ValueBet Quant", page_icon="⚽", layout="centered")

st.title("⚽ ValueBet Quant - Auto Cotes (48h Betclic)")

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
# 2. SELECTION MATCHS BETCLIC PROCHAINES 48H
# ---------------------------------------------------------
st.subheader("⚡ 2. Matchs Betclic (48h Prochaines)")

bk_1_val, bk_N_val, bk_2_val = 2.10, 3.40, 3.80
bk_o25_val, bk_u25_val, bk_btts_val = 1.95, 1.85, 1.80

sports_keys = [
    "soccer_france_ligue_one", "soccer_france_ligue_two", "soccer_epl", 
    "soccer_spain_la_liga", "soccer_italy_serie_a", "soccer_germany_bundesliga", 
    "soccer_uefa_champs_league", "soccer_usa_mls"
]

@st.cache_data(ttl=180)
def fetch_betclic_48h_matches():
    matches_dict = {}
    now = datetime.now(timezone.utc)
    limit_48h = now + timedelta(hours=48)
    
    for s_key in sports_keys:
        # On demande uniquement Betclic à l'API pour charger très vite
        odds_url = f"https://api.the-odds-api.com/v4/sports/{s_key}/odds/?apiKey={API_KEY}&regions=eu&markets=h2h,totals,btts&bookmakers=betclic"
        try:
            r = requests.get(odds_url, timeout=4)
            data = r.json()
            if isinstance(data, list):
                for match in data:
                    # Verification du filtre 48h
                    commence_time = datetime.fromisoformat(match['commence_time'].replace('Z', '+00:00'))
                    if now <= commence_time <= limit_48h:
                        # Uniquement si Betclic est bien présent
                        if any(bm['key'] == 'betclic' for bm in match.get('bookmakers', [])):
                            label = f"{match['home_team']} vs {match['away_team']}"
                            matches_dict[label] = match
        except Exception:
            pass
    return matches_dict

all_matches = fetch_betclic_48h_matches()

if all_matches:
    selected_label = st.selectbox("📌 Choisis ton match Betclic (prochaines 48h) :", ["-- Sélectionne un match --"] + list(all_matches.keys()))
    
    if selected_label != "-- Sélectionne un match --":
        match = all_matches[selected_label]
        h_name = match['home_team']
        a_name = match['away_team']
        
        # On extrait les cotes Betclic
        for bm in match.get('bookmakers', []):
            if bm['key'] == 'betclic':
                for market in bm.get('markets', []):
                    if market['key'] == 'h2h':
                        for o in market['outcomes']:
                            if o['name'] == h_name: bk_1_val = float(o['price'])
                            elif o['name'] == a_name: bk_2_val = float(o['price'])
                            else: bk_N_val = float(o['price'])
                    elif market['key'] == 'totals':
                        for o in market['outcomes']:
                            if o.get('point') == 2.5:
                                if o['name'] == 'Over': bk_o25_val = float(o['price'])
                                elif o['name'] == 'Under': bk_u25_val = float(o['price'])
                    elif market['key'] == 'btts':
                        for o in market['outcomes']:
                            if o['name'] == 'Yes': bk_btts_val = float(o['price'])

        st.success(f"🎯 Cotes Betclic chargées en direct !")
else:
    st.info("Aucun match Betclic trouvé dans les 48h pour ces ligues (ou rechargement en cours).")

bk_dnb1_val = round(bk_1_val * (1 - (1 / bk_N_val)), 2) if bk_N_val > 0 else 1.50
bk_dnb2_val = round(bk_2_val * (1 - (1 / bk_N_val)), 2) if bk_N_val > 0 else 2.60

st.caption(f"Cotes chargées : 1N2 ({bk_1_val} / {bk_N_val} / {bk_2_val}) | O/U 2.5 ({bk_o25_val} / {bk_u25_val}) | BTTS ({bk_btts_val})")

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
