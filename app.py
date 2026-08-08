"""
ValueBet Quant - Modèle vs Betclic (v3 - simplifiée)
======================================================

CE QUI A CHANGÉ PAR RAPPORT AUX VERSIONS PRÉCÉDENTES :

1. PLUS D'API DE COTES DU TOUT. Les cotes se saisissent à la main, dans le
   même ordre que sur l'app Betclic (1N2 -> DNB -> Buts Over/Under par ligne
   -> BTTS), pour que tu puisses juste recopier en lisant l'écran Betclic
   de haut en bas.

2. xG AUTOMATIQUE VIA FOOTYSTATS, SANS CLÉ API. Les pages xG de
   footystats.org sont publiques (pas besoin de compte ni d'abonnement).
   Le split Domicile / Extérieur existe uniquement sur la page de CHAQUE
   ÉQUIPE (onglet "Shots, xG & Offsides"), pas sur la page globale du
   championnat -> ce script va chercher la liste des équipes du championnat
   choisi, puis va lire la page de chacune des 2 équipes sélectionnées.

3. Tu choisis les 2 équipes dans une liste déroulante (peuplée automatiquement
   depuis FootyStats), donc plus de souci de "quel nom correspond à quelle
   équipe" : les 2 équipes viennent directement de la même source.

ATTENTION : ce script utilise du web scraping (lecture directe des pages HTML
publiques), pas une API officielle. Concrètement :
   - C'est gratuit et sans clé.
   - C'est plus fragile qu'une API : si FootyStats change la mise en page
     de son site, le scraping peut casser du jour au lendemain. Si ça arrive,
     regarde la fonction debug_team_page() pour voir ce qui a changé.
   - Fais des requêtes raisonnables (le cache ci-dessous limite à 1 requête
     par équipe toutes les 12h) pour rester correct vis-à-vis du site.

Non testé contre le vrai site depuis cet environnement (pas d'accès réseau
ici) : la structure HTML a été vérifiée manuellement sur 2 pages (championnat
MLS + page Houston Dynamo) au moment d'écrire ce script, mais teste chez toi
et dis-moi ce qui ne marche pas.
"""

import re
import difflib

import requests
import pandas as pd
import streamlit as st
from bs4 import BeautifulSoup

st.set_page_config(page_title="ValueBet Quant", page_icon="⚽", layout="centered")
st.title("⚽ ValueBet Quant - Modèle vs Betclic")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.google.com/",
    "Connection": "keep-alive",
}

# ---------------------------------------------------------
# 1. LIGUES — slug FootyStats (vérifiés : usa/mls et argentina/primera-division ;
#    les autres sont le format standard FootyStats "pays/nom-ligue", à vérifier
#    toi-même en une seconde sur footystats.org/leagues si jamais ça ne marche pas)
# ---------------------------------------------------------
LEAGUES = {
    "Ligue 1 (France)":              "france/ligue-1",
    "Ligue 2 (France)":              "france/ligue-2",
    "Bundesliga 2 (Allemagne)":      "germany/bundesliga-2",
    "Eliteserien (Norvège)":         "norway/eliteserien",
    "Liga I (Roumanie)":             "romania/liga-i",
    "Premiership (Écosse)":          "scotland/premiership",
    "Bundesliga (Autriche)":         "austria/bundesliga",
    "Liga Profesional (Argentine)":  "argentina/primera-division",  # vérifié
    "Liga MX (Mexique)":             "mexico/liga-mx",
    "MLS (USA)":                     "usa/mls",  # vérifié
    "Premier League (Angleterre)":   "england/premier-league",
    "La Liga (Espagne)":             "spain/la-liga",
    "Serie A (Italie)":              "italy/serie-a",
    "Bundesliga (Allemagne)":        "germany/bundesliga",
    "Ligue des Champions":           "europe/champions-league",
}

FUZZY_MATCH_THRESHOLD = 0.55


# ---------------------------------------------------------
# 2. SCRAPING FOOTYSTATS — liste des équipes d'un championnat
# ---------------------------------------------------------
@st.cache_data(ttl=86400, show_spinner="Chargement de la liste des équipes...")
def fetch_league_teams(league_slug: str) -> dict:
    """
    Retourne {nom_equipe: url_complete_page_equipe} pour un championnat,
    en lisant les liens vers /clubs/... présents sur la page du championnat.
    """
    url = f"https://footystats.org/{league_slug}"
    r = requests.get(url, headers=HEADERS, timeout=10)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    teams = {}
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/clubs/" in href:
            name = a.get_text(strip=True)
            if name and len(name) > 1:
                full_url = href if href.startswith("http") else f"https://footystats.org{href}"
                teams[name] = full_url
    return teams


# ---------------------------------------------------------
# 3. SCRAPING FOOTYSTATS — xG Domicile/Extérieur d'une équipe
# ---------------------------------------------------------
@st.cache_data(ttl=43200, show_spinner=False)
def fetch_team_xg_home_away(team_url: str) -> dict | None:
    """
    Va chercher, sur la page d'une équipe, le tableau 'Expected Goals'
    (section Shots, xG & Offsides) avec les colonnes Overall / At Home / At Away.
    Retourne {"home_for":..., "home_against":..., "away_for":..., "away_against":...}
    ou None si le tableau n'a pas été trouvé (mise en page différente / page premium).
    """
    r = requests.get(team_url, headers=HEADERS, timeout=10)
    r.raise_for_status()

    try:
        tables = pd.read_html(r.text)
    except ValueError:
        return None

    for table in tables:
        # On cherche la table qui contient une ligne "xG For" et une ligne "xG Against"
        first_col = table.iloc[:, 0].astype(str).str.strip()
        if first_col.str.contains("xG For", case=False, na=False).any() and \
           first_col.str.contains("xG Against", case=False, na=False).any():

            row_for = table[first_col.str.contains("xG For", case=False, na=False)]
            row_against = table[first_col.str.contains("xG Against", case=False, na=False)]

            # Colonnes attendues dans l'ordre : [label, Overall, At Home, At Away]
            if table.shape[1] >= 4:
                try:
                    return {
                        "home_for": float(row_for.iloc[0, 2]),
                        "away_for": float(row_for.iloc[0, 3]),
                        "home_against": float(row_against.iloc[0, 2]),
                        "away_against": float(row_against.iloc[0, 3]),
                    }
                except (ValueError, IndexError):
                    continue
    return None


def debug_team_page(team_url: str):
    """À lancer à la main si le scraping casse, pour voir toutes les tables
    trouvées sur la page et repérer laquelle contient les xG."""
    r = requests.get(team_url, headers=HEADERS, timeout=10)
    tables = pd.read_html(r.text)
    for i, t in enumerate(tables):
        st.write(f"Table {i}:")
        st.dataframe(t)


def match_team(query: str, teams: dict) -> str | None:
    """Rapprochement flou si jamais le nom tapé ne correspond pas exactement."""
    names = list(teams.keys())
    best = difflib.get_close_matches(query, names, n=1, cutoff=FUZZY_MATCH_THRESHOLD)
    return best[0] if best else None


# ---------------------------------------------------------
# 4. SÉLECTION DU CHAMPIONNAT ET DES 2 ÉQUIPES
# ---------------------------------------------------------
st.subheader("🔎 1. Choisir les 2 équipes")

selected_league_name = st.selectbox("Compétition :", list(LEAGUES.keys()))
league_slug = LEAGUES[selected_league_name]

teams_error = None
teams = {}
try:
    teams = fetch_league_teams(league_slug)
except requests.HTTPError as e:
    teams_error = f"Erreur ({e.response.status_code}) en chargeant la liste des équipes."
except requests.RequestException as e:
    teams_error = f"Erreur réseau : {e}"

if teams_error:
    st.error(teams_error)
elif not teams:
    st.warning(
        "Aucune équipe trouvée pour ce championnat (page peut-être différente de ce qui "
        "était prévu). Vérifie le slug dans LEAGUES ou saisis les xG à la main plus bas."
    )

team_names = sorted(teams.keys())
col_home, col_away = st.columns(2)
home_team_name = col_home.selectbox("Équipe domicile", ["--"] + team_names, key="home_team_select")
away_team_name = col_away.selectbox("Équipe extérieure", ["--"] + team_names, key="away_team_select")

load_clicked = st.button("📥 Charger les xG (Domicile/Extérieur) depuis FootyStats")


def load_xg():
    if home_team_name == "--" or away_team_name == "--":
        st.session_state["_xg_msg"] = "⚠️ Choisis les 2 équipes d'abord."
        return

    msgs = []
    home_data = fetch_team_xg_home_away(teams[home_team_name])
    if home_data:
        st.session_state["xgA_m"] = round(home_data["home_for"], 2)
        st.session_state["xgA_c"] = round(home_data["home_against"], 2)
        msgs.append(f"✅ {home_team_name} (Domicile) : xG {home_data['home_for']} / xGA {home_data['home_against']}")
    else:
        msgs.append(f"⚠️ xG Domicile introuvables pour {home_team_name} (page premium ou mise en page différente).")

    away_data = fetch_team_xg_home_away(teams[away_team_name])
    if away_data:
        st.session_state["xgB_m"] = round(away_data["away_for"], 2)
        st.session_state["xgB_c"] = round(away_data["away_against"], 2)
        msgs.append(f"✅ {away_team_name} (Extérieur) : xG {away_data['away_for']} / xGA {away_data['away_against']}")
    else:
        msgs.append(f"⚠️ xG Extérieur introuvables pour {away_team_name} (page premium ou mise en page différente).")

    st.session_state["_xg_msg"] = " | ".join(msgs)


if load_clicked:
    load_xg()

if st.session_state.get("_xg_msg"):
    st.caption(st.session_state["_xg_msg"])

st.divider()

# ---------------------------------------------------------
# 5. SAISIE DES xG (pré-remplis si le scraping a marché, toujours modifiables)
# ---------------------------------------------------------
st.subheader("📝 2. Statistiques xG (Domicile pour l'équipe qui reçoit, Extérieur pour l'autre)")

for k, v in {"xgA_m": 1.80, "xgA_c": 0.90, "xgB_m": 1.00, "xgB_c": 1.20}.items():
    if k not in st.session_state:
        st.session_state[k] = v

col1, col2 = st.columns(2)
with col1:
    st.markdown("**🏠 Domicile**")
    xgA_m = st.number_input("xG Marqués (Dom, à domicile)", step=0.01, key="xgA_m")
    xgA_c = st.number_input("xG Concédés (Dom, à domicile)", step=0.01, key="xgA_c")
with col2:
    st.markdown("**✈️ Extérieur**")
    xgB_m = st.number_input("xG Marqués (Ext, à l'extérieur)", step=0.01, key="xgB_m")
    xgB_c = st.number_input("xG Concédés (Ext, à l'extérieur)", step=0.01, key="xgB_c")

st.divider()

# ---------------------------------------------------------
# 6. COTES — 100% manuelles, regroupées comme sur l'app Betclic
# ---------------------------------------------------------
st.subheader("📊 3. Cotes Betclic (saisie manuelle)")

st.markdown("**Résultat du match**")
c1, cN, c2 = st.columns(3)
bk_1 = c1.number_input("1", step=0.01, value=2.28, key="bk_1")
bk_N = cN.number_input("N", step=0.01, value=3.30, key="bk_N")
bk_2 = c2.number_input("2", step=0.01, value=2.77, key="bk_2")

st.markdown("**Résultat du match (remboursé si nul)**")
cd1, cd2 = st.columns(2)
bk_dnb1 = cd1.number_input("DNB Domicile", step=0.01, value=1.63, key="bk_dnb1")
bk_dnb2 = cd2.number_input("DNB Extérieur", step=0.01, value=1.90, key="bk_dnb2")

st.markdown("**Nombre total de buts**")
lignes_ou = [0.5, 1.5, 2.5, 3.5]
ou_odds = {}
for ligne in lignes_ou:
    co, cu = st.columns(2)
    ou_odds[ligne] = {
        "over": co.number_input(f"+ de {ligne}", step=0.01, key=f"bk_o{ligne}"),
        "under": cu.number_input(f"- de {ligne}", step=0.01, key=f"bk_u{ligne}"),
    }

st.markdown("**Les 2 équipes marquent**")
cbtts1, cbtts2 = st.columns(2)
bk_btts_yes = cbtts1.number_input("BTTS Oui", step=0.01, value=1.59, key="bk_btts_yes")
bk_btts_no = cbtts2.number_input("BTTS Non", step=0.01, value=2.13, key="bk_btts_no")

# La ligne 2.5 reste la référence pour le calcul Over/Under principal ci-dessous
bk_o25 = ou_odds[2.5]["over"]
bk_u25 = ou_odds[2.5]["under"]

# ---------------------------------------------------------
# 7. CALCULS MODÈLE DIXON-COLES
# ---------------------------------------------------------
lambda_val = (st.session_state["xgA_m"] + st.session_state["xgB_c"]) / 2
mu_val = (st.session_state["xgB_m"] + st.session_state["xgA_c"]) / 2


def poisson(k, lmbda):
    import math
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
    prob_book = (1 / bk * 100) if bk and bk > 0 else 0

    is_val = bool(bk) and bk > 0 and bk > fair
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
    display_card("DNB 1", bk_dnb1, p_dnb1)
    display_card("Over 2.5", bk_o25, p_o25)
with m2:
    display_card("Match Nul (N)", bk_N, p_N)
    display_card("Under 2.5", bk_u25, p_u25)
with m3:
    display_card("Victoire Ext (2)", bk_2, p_2)
    display_card("DNB 2", bk_dnb2, p_dnb2)
    display_card("BTTS Oui", bk_btts_yes, p_btts)
