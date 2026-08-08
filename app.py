import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import math

st.set_page_config(page_title="ValueBet Quant", page_icon="⚽", layout="centered")

st.title("⚽ ValueBet Quant - Match Direct & Cotes Betclic")

API_KEY = "f38ee008fcce89b9c2f13d577cbd1745"

# ---------------------------------------------------------
# 1. SCRAPING xG ET RECHERCHE AUTOMATIQUE DES ÉQUIPES
# ---------------------------------------------------------
url = st.text_input("🔗 Colle le lien du match FootyStats :", key="url_input")

xg_dom_m, xg_dom_c = 1.80, 0.90
xg_ext_m, xg_ext_c = 1.00, 1.20
home_team_found = ""
away_team_found = ""

bk_1_val, bk_N_val, bk_2_val = 2.10, 3.40, 3.80

if url:
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': 'https://footystats.org/'
        }
        res = requests.get(url, headers=headers, timeout=8)
        
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            text = soup.get_text()
            
            # Extraction des xG
            xg_matches = re.findall(r'(\d+[\.,]\d+)', text)
            valid_xg = [float(x.replace(',', '.')) for x in xg_matches if 0.20 <= float(x.replace(',', '.')) <= 4.50]
            
            if len(valid_xg) >= 4:
                xg_dom_m, xg_dom_c = valid_xg[0], valid_xg[1]
                xg_ext_m, xg_ext_c = valid_xg[2], valid_xg[3]
                st.success(f"✅ xG extraits : Dom ({xg_dom_m} / {xg_dom_c}) | Ext ({xg_ext_m} / {xg_ext_c})")
            
            # Extraction des noms d'équipes depuis le titre de la page
            title = soup.title.string if soup.title else ""
            if " vs " in title or " v " in title or " - " in title:
                # Tente de trouver les équipes dans le titre
                clean_title = title.split("Pronostics")[0].split("Stats")[0]
                st.info(f"📌 Match détecté : {clean_title.strip()}")
                
        else:
            st.error(f"❌ Blocage FootyStats (Code {res.status_code}).")
    except Exception as e:
        st.error(f"❌ Erreur de lecture du lien : {e}")

st.divider()

# Formulaire xG
col1, col2 = st.columns(2)
with col1:
    st.subheader("🏠 Domicile")
    xgA_m = st.number_input("xG Marqués (Dom)", value=xg_dom_m, step=0.01, key="xgA_m")
    xgA_c = st.number_input("xG Concédés (Dom)", value=xg_dom_c, step=0.01, key="xgA_c")

with col2:
    st.subheader("✈️ Extérieur")
    xgB_m = st.number_input("xG Marqués (Ext)", value=xg_ext_m, step=0.01, key="xgB_m")
    xgB_c = st.number_input("xG Concédés (Ext)", value=xg_ext_c, step=0.01, key="xgB_c")

st.divider()

# ---------------------------------------------------------
# 2. RECHERCHE EN DIRECT DES COTES BETCLIC POUR CE MATCH
# ---------------------------------------------------------
st.subheader("📊 Cotes Betclic en Direct")

search_query = st.text_input("🔍 Recherche le nom d'une des équipes sur Betclic :", placeholder="ex: PSG, Real Madrid, Arsenal...")

if search_query:
    # On parcourt les compétitions principales pour trouver le match
    sports_keys = ["soccer_france_ligue_one", "soccer_epl", "soccer_spain_la_liga", "soccer_italy_serie_a", "soccer_germany_bundesliga", "soccer_uefa_champs_league"]
    found = False
    
    for s_key in sports_keys:
        if found: break
        odds_url = f"https://api.the-odds-api.com/v4/sports/{s_key}/odds/?apiKey={API_KEY}&regions=eu&markets=h2h&bookmakers=betclic"
        try:
            r = requests.get(odds_url)
            data = r.json()
            for match in data:
                h_name = match['home_team']
                a_name = match['away_team']
                
                # Vérifie si le nom cherché est dans le match
                if search_query.lower() in h_name.lower() or search_query.lower() in a_name.lower():
                    for bm in match.get('bookmakers', []):
                        if bm['key'] == 'betclic':
                            outcomes = bm['markets'][0]['outcomes']
                            for o in outcomes:
                                if o['name'] == h_name: bk_1_val = float(o['price'])
                                elif o['name'] == a_name: bk_2_val = float(o['price'])
                                else: bk_N_val = float(o['price'])
                            st.success(f"🎯 Cotes Betclic trouvées en direct pour {h_name} vs {a_name} !")
                            found = True
                            break
        except Exception:
            pass
            
    if not found:
        st.warning("Aucun match correspondant trouvé en direct chez Betclic. Ajuste les cotes ci-dessous.")

st.markdown("**Marché 1N2**")
c1, cN, c2 = st.columns(3)
bk_1 = c1.number_input("Cote 1", value=bk_1_val, step=0.05)
bk_N = cN.number_input("Cote N", value=bk_N_val, step=0.05)
bk_2 = c2.number_input("Cote 2", value=bk_2_val, step=0.05)

st.markdown("**Marché DNB (Draw No Bet)**")
cd1, cd2 = st.columns(2)
bk_dnb1 = cd1.number_input("DNB 1", value=1.50, step=0.05)
bk_dnb2 = cd2.number_input("DNB 2", value=2.60, step=0.05)

st.markdown("**Marché Buts & BTTS**")
co25, cu25, cbtts = st.columns(3)
bk_o25 = co25.number_input("Over 2.5", value=1.95, step=0.05)
bk_u25 = cu25.number_input("Under 2.5", value=1.85, step=0.05)
bk_btts = cbtts.number_input("BTTS Oui", value=1.80, step=0.05)

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
