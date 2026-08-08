import streamlit as st
import requests
import math

st.set_page_config(page_title="ValueBet Quant", page_icon="⚽", layout="centered")

st.title("⚽ ValueBet Quant - Saisie xG & Cotes Betclic Auto")

API_KEY = "f38ee008fcce89b9c2f13d577cbd1745"

# ---------------------------------------------------------
# 1. SAISIE RAPIDE DES 4 xG
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
# 2. CHARGEMENT AUTOMATIQUE DE TOUTES LES COTES BETCLIC
# ---------------------------------------------------------
st.subheader("⚡ 2. Cotes Betclic Automatiques")

search_query = st.text_input("🔍 Tape le nom d'une équipe :", placeholder="ex: Guingamp, Metz, PSG, Real...")

bk_1_val, bk_N_val, bk_2_val = 2.10, 3.40, 3.80
bk_o25_val, bk_u25_val, bk_btts_val = 1.95, 1.85, 1.80
bk_dnb1_val, bk_dnb2_val = 1.50, 2.60

if search_query:
    sports_keys = [
        "soccer_france_ligue_one", "soccer_france_ligue_two", "soccer_epl", 
        "soccer_spain_la_liga", "soccer_italy_serie_a", "soccer_germany_bundesliga", 
        "soccer_uefa_champs_league", "soccer_usa_mls"
    ]
    found = False
    
    for s_key in sports_keys:
        if found: break
        # Appel API pour le 1N2, Over/Under et BTTS
        odds_url = f"https://api.the-odds-api.com/v4/sports/{s_key}/odds/?apiKey={API_KEY}&regions=eu&markets=h2h,totals,btts&bookmakers=betclic"
        try:
            r = requests.get(odds_url)
            data = r.json()
            for match in data:
                h_name = match['home_team']
                a_name = match['away_team']
                
                if search_query.lower() in h_name.lower() or search_query.lower() in a_name.lower():
                    for bm in match.get('bookmakers', []):
                        if bm['key'] == 'betclic':
                            for market in bm.get('markets', []):
                                # Extraction 1N2
                                if market['key'] == 'h2h':
                                    for o in market['outcomes']:
                                        if o['name'] == h_name: bk_1_val = float(o['price'])
                                        elif o['name'] == a_name: bk_2_val = float(o['price'])
                                        else: bk_N_val = float(o['price'])
                                # Extraction Over / Under 2.5
                                elif market['key'] == 'totals':
                                    for o in market['outcomes']:
                                        if o.get('point') == 2.5:
                                            if o['name'] == 'Over': bk_o25_val = float(o['price'])
                                            elif o['name'] == 'Under': bk_u25_val = float(o['price'])
                                # Extraction BTTS
                                elif market['key'] == 'btts':
                                    for o in market['outcomes']:
                                        if o['name'] == 'Yes': bk_btts_val = float(o['price'])

                            # Estimation automatique des DNB si non fournis par l'API
                            bk_dnb1_val = round(bk_1_val * (1 - (1 / bk_N_val)), 2)
                            bk_dnb2_val = round(bk_2_val * (1 - (1 / bk_N_val)), 2)

                            st.success(f"🎯 Toutes les cotes Betclic ont été chargées pour **{h_name} vs {a_name}** !")
                            found = True
                            break
        except Exception:
            pass
            
    if not found:
        st.warning("Match non trouvé sur Betclic. Vérifie l'orthographe de l'équipe.")

# Affichage informatif des cotes Betclic récupérées
st.caption(f"Cotes Betclic chargées : 1N2 ({bk_1_val} / {bk_N_val} / {bk_2_val}) | O/U 2.5 ({bk_o25_val} / {bk_u25_val}) | BTTS ({bk_btts_val})")

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
