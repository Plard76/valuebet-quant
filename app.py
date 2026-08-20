import streamlit as st
import math
import os

# Tentative d'importation de pandas
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

st.set_page_config(page_title="Calculateur Quant xG", page_icon="⚽", layout="centered")

st.title("⚽ CALCULATEUR QUANT - OVER/UNDER & BTTS")

# ---------------------------------------------------------
# 1. IMPORTATION ET TÉLÉCHARGEMENT CSV
# ---------------------------------------------------------
st.subheader("📁 1. Matchs du Jour (CSV / Excel)")

default_values = {"xgA_m": 1.67, "xgA_c": 0.83, "xgB_m": 1.00, "xgB_c": 1.33}

# Modèle CSV prêt à être téléchargé sur le téléphone
template_csv = "match,xga_m,xga_c,xgb_m,xgb_c\nGirona vs Rayo Vallecano,1.85,1.20,1.30,1.55\nHammarby vs Kalmar,2.10,1.10,1.60,1.70\n"

st.download_button(
    label="📥 1. Télécharger le modèle CSV exemple",
    data=template_csv,
    file_name="matchs_exemple.csv",
    mime="text/csv"
)

st.caption("Télécharge le fichier modèle ci-dessus, modifie les chiffres, puis redépose-le ci-dessous.")

uploaded_file = st.file_uploader("📤 2. Dépose ton fichier CSV/Excel rempli", type=["csv", "xlsx"])

df = None

# Lecture du fichier déposé ou d'un fichier 'matchs.csv' présent sur GitHub
if uploaded_file is not None and HAS_PANDAS:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"Erreur de lecture du fichier importé : {e}")
elif os.path.exists("matchs.csv") and HAS_PANDAS:
    try:
        df = pd.read_csv("matchs.csv")
        st.info("ℹ️ Fichier 'matchs.csv' détecté depuis GitHub.")
    except Exception as e:
        pass

if df is not None:
    try:
        df.columns = [c.strip().lower() for c in df.columns]
        
        if 'match' in df.columns:
            match_list = df['match'].tolist()
        elif 'domicile' in df.columns and 'exterieur' in df.columns:
            df['match'] = df['domicile'] + " vs " + df['exterieur']
            match_list = df['match'].tolist()
        else:
            match_list = [f"Match #{i+1}" for i in range(len(df))]
            df['match'] = match_list

        selected_match = st.selectbox("🎯 Sélectionne le match à analyser :", match_list)
        
        match_row = df[df['match'] == selected_match].iloc[0]
        
        default_values["xgA_m"] = float(match_row.get('xga_m', default_values["xgA_m"]))
        default_values["xgA_c"] = float(match_row.get('xga_c', default_values["xgA_c"]))
        default_values["xgB_m"] = float(match_row.get('xgb_m', default_values["xgB_m"]))
        default_values["xgB_c"] = float(match_row.get('xgb_c', default_values["xgB_c"]))
        
        st.success(f"✅ xG chargés automatiquement pour : **{selected_match}**")
    except Exception as e:
        st.error(f"Erreur d'extraction des données du match : {e}")

st.divider()

# ---------------------------------------------------------
# 2. STATISTIQUES xG
# ---------------------------------------------------------
st.subheader("📝 2. Statistiques xG")

col_dom, col_ext = st.columns(2)

with col_dom:
    st.markdown("### 🏠 Domicile")
    xgA_m = st.number_input("xG Marqués (Dom)", value=default_values["xgA_m"], step=0.01, key="xgA_m")
    xgA_c = st.number_input("xG Concédés (Dom)", value=default_values["xgA_c"], step=0.01, key="xgA_c")

with col_ext:
    st.markdown("### ✈️ Extérieur")
    xgB_m = st.number_input("xG Marqués (Ext)", value=default_values["xgB_m"], step=0.01, key="xgB_m")
    xgB_c = st.number_input("xG Concédés (Ext)", value=default_values["xgB_c"], step=0.01, key="xgB_c")

XG_SAFETY_COEFFICIENT = 0.85

st.divider()

# ---------------------------------------------------------
# 3. COTES BETCLIC
# ---------------------------------------------------------
st.subheader("📊 3. Cotes Betclic")

SHOW_OVER_UNDER = False
SHOW_BTTS25 = False

st.markdown("**Les 2 équipes marquent (BTTS)**")
cb1, cb2 = st.columns(2)
bk_btts_oui = cb1.number_input("BTTS Oui", value=1.49, step=0.01, key="bk_btts_oui")
bk_btts_non = cb2.number_input("BTTS Non", value=2.33, step=0.01, key="bk_btts_non")

st.markdown("**Les 2 équipes marquent OU + de 2.5 buts (gardé en mémoire)**")
if SHOW_BTTS25:
    cbo1, cbo2 = st.columns(2)
    bk_btts25_oui = cbo1.number_input("BTTS+2.5 Oui", value=1.55, step=0.01, key="bk_btts25_oui")
    bk_btts25_non = cbo2.number_input("BTTS+2.5 Non", value=2.20, step=0.01, key="bk_btts25_non")
else:
    st.caption("Masqué — passe SHOW_BTTS25 à True en haut du fichier pour le revoir.")

st.markdown("**Évolution de la cote depuis ta première consultation**")
st.caption("Cote qui baisse = le marché se resserre vers ce résultat. Cote qui monte = le marché s'en éloigne.")
cm1, cm2 = st.columns(2)
MOVEMENT_OPTIONS = ["➡️ Stable / pas suivi", "↗️ En hausse", "↘️ En baisse"]
mvt_btts_oui = cm1.selectbox("Évolution BTTS Oui", MOVEMENT_OPTIONS, key="mvt_btts_oui")
mvt_btts_non = cm2.selectbox("Évolution BTTS Non", MOVEMENT_OPTIONS, key="mvt_btts_non")

if SHOW_BTTS25:
    cm3, cm4 = st.columns(2)
    mvt_btts25_oui = cm3.selectbox("Évolution BTTS+2.5 Oui", MOVEMENT_OPTIONS, key="mvt_btts25_oui")
    mvt_btts25_non = cm4.selectbox("Évolution BTTS+2.5 Non", MOVEMENT_OPTIONS, key="mvt_btts25_non")

st.markdown("**Cotes Over / Under (gardées en mémoire)**")
if SHOW_OVER_UNDER:
    co1, co2, co3 = st.columns(3)
    bk_o15 = co1.number_input("Over 1.5", value=1.25, step=0.01, key="bk_o15")
    bk_o25 = co2.number_input("Over 2.5", value=1.80, step=0.01, key="bk_o25")
    bk_u25 = co3.number_input("Under 2.5", value=1.95, step=0.01, key="bk_u25")
else:
    st.caption("Masquées — passe SHOW_OVER_UNDER à True en haut du fichier pour les revoir.")

# ---------------------------------------------------------
# 4. CALCULS DU MODÈLE DIXON-COLES & POISSON
# ---------------------------------------------------------
lambda_val = (xgA_m + xgB_c) / 2
mu_val = (xgB_m + xgA_c) / 2


def poisson(k, lmbda):
    return (math.pow(lmbda, k) * math.exp(-lmbda)) / math.factorial(k) if lmbda > 0 else 0


p_1, p_N, p_2 = 0.0, 0.0, 0.0
p_btts_oui = 0.0
p_over_15 = 0.0
p_over_25 = 0.0
p_over_35 = 0.0
p_btts_and_over25 = 0.0
rho = -0.13

for x in range(10):
    for y in range(10):
        p = poisson(x, lambda_val) * poisson(y, mu_val)

        # Correction Dixon-Coles
        if x == 0 and y == 0: p *= (1 - lambda_val * mu_val * rho)
        elif x == 1 and y == 0: p *= (1 + mu_val * rho)
        elif x == 0 and y == 1: p *= (1 + lambda_val * rho)
        elif x == 1 and y == 1: p *= (1 - rho)

        # BTTS
        btts_ici = x > 0 and y > 0
        if btts_ici: p_btts_oui += p

        # OVER / UNDER
        total_goals = x + y
        if total_goals > 1.5: p_over_15 += p
        if total_goals > 2.5: p_over_25 += p
        if total_goals > 3.5: p_over_35 += p

        # Intersection BTTS et Over 2.5
        if btts_ici and total_goals > 2.5: p_btts_and_over25 += p

p_btts_non = 1.0 - p_btts_oui
p_under_25 = 1.0 - p_over_25
xg_total = lambda_val + mu_val
xg_total_prudent = xg_total * XG_SAFETY_COEFFICIENT

p_btts_ou_25 = p_btts_oui + p_over_25 - p_btts_and_over25
p_btts_ou_25_non = 1.0 - p_btts_ou_25

st.divider()

# ---------------------------------------------------------
# 5. RÉSULTATS & VALUEBETS
# ---------------------------------------------------------
st.subheader("🎯 4. Résultats & ValueBets")

st.markdown(
    f"""
    <div style="background-color: #0f172a; padding: 12px; border-radius: 6px; margin-bottom: 16px; border: 1px solid #334155;">
        <div style="display:flex; justify-content:space-around; text-align:center;">
            <div>
                <div style="color: #94a3b8; font-size: 0.8rem; font-weight: bold; letter-spacing: 1px;">xG CALCULÉ (λ + μ)</div>
                <div style="color: #f8fafc; font-size: 1.6rem; font-weight: 900; font-family: monospace;">{xg_total:.2f}</div>
                <div style="color: #64748b; font-size: 0.75rem;">({lambda_val:.2f} - {mu_val:.2f})</div>
            </div>
            <div>
                <div style="color: #94a3b8; font-size: 0.8rem; font-weight: bold; letter-spacing: 1px;">xG AVEC COEFFICIENT (×{XG_SAFETY_COEFFICIENT})</div>
                <div style="color: #f8fafc; font-size: 1.6rem; font-weight: 900; font-family: monospace;">{xg_total_prudent:.2f}</div>
                <div style="color: #64748b; font-size: 0.75rem;">version prudente</div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)


def display_card(title, bk, prob, movement=None):
    prob_quant = prob * 100

    EDGE_MARGE = 0.03
    implied_prob = (1 / bk) if bk > 0 else 0
    edge_points = (prob - implied_prob) * 100
    fair = 1 / (prob - EDGE_MARGE) if prob > EDGE_MARGE else 0

    roi = ((bk * prob) - 1) * 100 if bk > 0 else 0

    EDGE_THRESHOLD_ULTRA = 3.0
    is_val = edge_points > 0 and bk > 0
    is_ultra = is_val and edge_points > EDGE_THRESHOLD_ULTRA and prob_quant >= 75.0

    movement_confirms = movement == "↘️ En baisse"
    on_joue = is_val and movement_confirms

    if on_joue and is_ultra:
        card_bg = "background-color: #064e3b; border: 3px solid #10b981;"
        badge = f"""
        <div style="background-color: #10b981; color: #000000; font-weight: 900; font-size: 1.15rem; padding: 8px; border-radius: 6px; text-align: center; margin-top: 6px;">
            🔥 ULTRA VALUE (+{edge_points:.1f} pts) [PROBA ≥ 75%]
        </div>
        """
    elif on_joue:
        card_bg = "background-color: #14532d; border: 3px solid #10b981;"
        badge = f'<div style="color: #10b981; font-weight: 900; font-size: 1.15rem; margin-top: 6px;">+{edge_points:.1f} pts VALUE</div>'
    elif is_val:
        card_bg = "background-color: #1e293b; border: 1px solid #f59e0b;"
        badge = f'<div style="color: #f59e0b; font-weight: bold; font-size: 1rem; margin-top: 6px;">+{edge_points:.1f} pts d\'edge, mais non confirmé par le marché</div>'
    else:
        card_bg = "background-color: #1e293b; border: 1px solid #334155;"
        badge = f'<div style="color: #ef4444; font-weight: bold; font-size: 1rem; margin-top: 6px;">NO VALUE ({edge_points:+.1f} pts)</div>'

    movement_html = ""
    if movement and movement != "➡️ Stable / pas suivi":
        if movement == "↘️ En baisse":
            mvt_note = "le marché se resserre vers ce résultat (confirmation) → signal favorable pour jouer."
            mvt_color = "#10b981"
        else:
            mvt_note = "le marché s'éloigne de ce résultat (doute) → signal défavorable, mieux vaut ne pas jouer même si l'edge semble bon."
            mvt_color = "#ef4444"
        movement_html = f'<div style="font-size: 0.8rem; color: {mvt_color}; margin-top: 4px; margin-bottom: 4px;">{movement} — {mvt_note}</div>'

    if on_joue:
        verdict_html = '<div style="background-color:#10b981; color:#000000; font-weight:900; font-size:1.3rem; text-align:center; padding:8px; border-radius:6px; margin-top:8px;">✅ ON JOUE</div>'
    else:
        verdict_html = '<div style="background-color:#3d1a1a; color:#ff8080; font-weight:900; font-size:1.3rem; text-align:center; padding:8px; border-radius:6px; margin-top:8px;">❌ ON NE JOUE PAS</div>'

    st.markdown(
        f"""
        <div style="{card_bg} padding: 14px; border-radius: 10px; margin-bottom: 12px;">
            <div style="font-size: 1rem; color: #f1f5f9; font-weight: bold; margin-bottom: 6px;">{title}</div>
            <div style="font-size: 1.8rem; color: #38bdf8; font-weight: 900; margin-bottom: 6px;">{prob_quant:.1f}%</div>
            <div style="font-size: 0.95rem; color: #cbd5e1; margin-bottom: 4px;">
                Cote Betclic : <b style="color: #ffffff;">{bk:.2f}</b> | Cote juste mini : <b style="color: #f59e0b;">≥ {fair:.2f}</b>
            </div>
            <div style="font-size: 0.85rem; color: #94a3b8; margin-bottom: 4px;">
                ROI attendu : <b style="color: {'#10b981' if roi > 0 else '#ef4444'};">{roi:+.1f}%</b>
            </div>
            {movement_html}
            {badge}
            {verdict_html}
        </div>
        """,
        unsafe_allow_html=True
    )

if SHOW_OVER_UNDER:
    st.markdown("#### ⚽ OVER / UNDER")
    display_card("OVER 1.5 BUTS", bk_o15, p_over_15)
    display_card("OVER 2.5 BUTS", bk_o25, p_over_25)
    display_card("UNDER 2.5 BUTS", bk_u25, p_under_25)

st.markdown("#### 🎯 MARCHÉ LES 2 ÉQUIPES MARQUENT (BTTS)")
display_card("BTTS OUI", bk_btts_oui, p_btts_oui, movement=mvt_btts_oui)
display_card("BTTS NON", bk_btts_non, p_btts_non, movement=mvt_btts_non)

if SHOW_BTTS25:
    st.markdown("#### 🎯 BTTS OU + DE 2.5 BUTS")
    display_card("BTTS+2.5 OUI", bk_btts25_oui, p_btts_ou_25, movement=mvt_btts25_oui)
    display_card("BTTS+2.5 NON", bk_btts25_non, p_btts_ou_25_non, movement=mvt_btts25_non)
