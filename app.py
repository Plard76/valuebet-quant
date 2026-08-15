import streamlit as st
import math

st.set_page_config(page_title="Calculateur Quant xG", page_icon="⚽", layout="centered")

st.title("⚽ CALCULATEUR QUANT - OVER/UNDER & BTTS")

# ---------------------------------------------------------
# 1. STATISTIQUES xG
# ---------------------------------------------------------
st.subheader("📝 1. Statistiques xG")

col_dom, col_ext = st.columns(2)

with col_dom:
    st.markdown("### 🏠 Domicile")
    xgA_m = st.number_input("xG Marqués (Dom)", value=1.67, step=0.01, key="xgA_m")
    xgA_c = st.number_input("xG Concédés (Dom)", value=0.83, step=0.01, key="xgA_c")

with col_ext:
    st.markdown("### ✈️ Extérieur")
    xgB_m = st.number_input("xG Marqués (Ext)", value=1.00, step=0.01, key="xgB_m")
    xgB_c = st.number_input("xG Concédés (Ext)", value=1.33, step=0.01, key="xgB_c")

# Coefficient de sécurité : réduit le xG calculé pour avoir une version plus prudente,
# partant du principe qu'un modèle simple (sans forme récente précise, sans absences)
# a tendance à surestimer la confiance qu'on peut avoir dans le chiffre brut.
XG_SAFETY_COEFFICIENT = 0.85

st.divider()

# ---------------------------------------------------------
# 2. COTES BETCLIC
# ---------------------------------------------------------
st.subheader("📊 2. Cotes Betclic")

# Interrupteur d'affichage : passe à True si tu veux revoir l'Over/Under un jour.
# Le calcul et les cotes Over/Under restent intacts plus bas, juste non affichés.
SHOW_OVER_UNDER = False

st.markdown("**Les 2 équipes marquent (BTTS)**")
cb1, cb2 = st.columns(2)
bk_btts_oui = cb1.number_input("BTTS Oui", value=1.49, step=0.01, key="bk_btts_oui")
bk_btts_non = cb2.number_input("BTTS Non", value=2.33, step=0.01, key="bk_btts_non")

st.markdown("**Évolution de la cote depuis ta première consultation**")
st.caption("Cote qui baisse = le marché se resserre vers ce résultat (signal favorable). Cote qui monte = le marché s'en éloigne (signal défavorable, mieux vaut ne pas jouer).")
cm1, cm2 = st.columns(2)
MOVEMENT_OPTIONS = ["➡️ Stable / pas suivi", "↗️ En hausse", "↘️ En baisse"]
mvt_btts_oui = cm1.selectbox("Évolution BTTS Oui", MOVEMENT_OPTIONS, key="mvt_btts_oui")
mvt_btts_non = cm2.selectbox("Évolution BTTS Non", MOVEMENT_OPTIONS, key="mvt_btts_non")

st.markdown("**Cotes Over / Under (gardées en mémoire, non utilisées pour le moment)**")
co1, co2, co3 = st.columns(3)
bk_o15 = co1.number_input("Over 1.5", value=1.25, step=0.01, key="bk_o15")
bk_o25 = co2.number_input("Over 2.5", value=1.80, step=0.01, key="bk_o25")
bk_u25 = co3.number_input("Under 2.5", value=1.95, step=0.01, key="bk_u25")

# ---------------------------------------------------------
# 3. CALCULS DU MODÈLE DIXON-COLES & POISSON
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
rho = -0.13

for x in range(10):
    for y in range(10):
        p = poisson(x, lambda_val) * poisson(y, mu_val)

        # Correction Dixon-Coles (corrige la corrélation des scores bas, indépendant du coefficient xG ci-dessus)
        if x == 0 and y == 0: p *= (1 - lambda_val * mu_val * rho)
        elif x == 1 and y == 0: p *= (1 + mu_val * rho)
        elif x == 0 and y == 1: p *= (1 + lambda_val * rho)
        elif x == 1 and y == 1: p *= (1 - rho)

        # BTTS
        if x > 0 and y > 0: p_btts_oui += p

        # OVER / UNDER
        total_goals = x + y
        if total_goals > 1.5: p_over_15 += p
        if total_goals > 2.5: p_over_25 += p
        if total_goals > 3.5: p_over_35 += p

p_btts_non = 1.0 - p_btts_oui
p_under_25 = 1.0 - p_over_25
xg_total = lambda_val + mu_val
xg_total_prudent = xg_total * XG_SAFETY_COEFFICIENT

st.divider()

# ---------------------------------------------------------
# 4. RÉSULTATS
# ---------------------------------------------------------
st.subheader("🎯 3. Résultats & ValueBets")

# Bloc d'info neutre : affiche les 2 chiffres côte à côte, sans donner de "recommandation"
# (le calcul du xG total/prudent ne compare jamais aux cotes -> ce n'est jamais lui qui doit
# dire si un pari est bon, seulement donner un repère de contexte sur le match)
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

    # --- Edge en POINTS (proba modèle - proba implicite de la cote), avec marge de sécurité ---
    EDGE_MARGE = 0.03  # marge de sécurité (3 pts), même logique que les outils HTML BTTS/DNB
    implied_prob = (1 / bk) if bk > 0 else 0
    edge_points = (prob - implied_prob) * 100  # écart brut, sert à l'affichage
    fair = 1 / (prob - EDGE_MARGE) if prob > EDGE_MARGE else 0  # cote juste mini, avec marge

    # --- ROI attendu (valeur espérée par euro misé) — indicateur complémentaire, affiché à part ---
    roi = ((bk * prob) - 1) * 100 if bk > 0 else 0

    # --- Seuils de badge ---
    EDGE_THRESHOLD_ULTRA = 3.0  # pts
    is_val = edge_points > 0 and bk > 0
    is_ultra = is_val and edge_points > EDGE_THRESHOLD_ULTRA and prob_quant >= 75.0

    if is_ultra:
        card_bg = "background-color: #064e3b; border: 2px solid #f59e0b;"
        badge = f"""
        <div style="background-color: #10b981; color: #000000; font-weight: 900; font-size: 1.1rem; padding: 6px; border-radius: 6px; text-align: center; margin-top: 6px;">
            🔥 ULTRA VALUE (+{edge_points:.1f} pts) [PROBA ≥ 75%]
        </div>
        """
    elif is_val:
        card_bg = "background-color: #1e4620; border: 1px solid #10b981;"
        badge = f'<div style="color: #10b981; font-weight: bold; font-size: 1.1rem; margin-top: 6px;">+{edge_points:.1f} pts VALUE</div>'
    else:
        card_bg = "background-color: #1e293b; border: 1px solid #334155;"
        badge = f'<div style="color: #ef4444; font-weight: bold; font-size: 1.1rem; margin-top: 6px;">NO VALUE ({edge_points:+.1f} pts)</div>'

    # --- Interprétation de l'évolution de cote (purement indicative, ne change jamais le badge ci-dessus) ---
    movement_html = ""
    if movement and movement != "➡️ Stable / pas suivi":
        if movement == "↘️ En baisse":
            mvt_note = "le marché se resserre vers ce résultat (confirmation) → signal favorable pour jouer."
            mvt_color = "#10b981"
        else:  # En hausse
            mvt_note = "le marché s'éloigne de ce résultat (doute) → signal défavorable, mieux vaut ne pas jouer même si l'edge semble bon."
            mvt_color = "#ef4444"
        movement_html = f'<div style="font-size: 0.8rem; color: {mvt_color}; margin-top: 4px; margin-bottom: 4px;">{movement} — {mvt_note}</div>'

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
        </div>
        """,
        unsafe_allow_html=True
    )


# OVER / UNDER — masqué pour l'instant (voir SHOW_OVER_UNDER en haut du fichier), code intact
if SHOW_OVER_UNDER:
    st.markdown("#### ⚽ OVER / UNDER")
    display_card("OVER 1.5 BUTS", bk_o15, p_over_15)
    display_card("OVER 2.5 BUTS", bk_o25, p_over_25)
    display_card("UNDER 2.5 BUTS", bk_u25, p_under_25)

# BTTS — seul marché actif pour le moment
st.markdown("#### 🎯 MARCHÉ LES 2 ÉQUIPES MARQUENT (BTTS)")
display_card("BTTS OUI", bk_btts_oui, p_btts_oui, movement=mvt_btts_oui)
display_card("BTTS NON", bk_btts_non, p_btts_non, movement=mvt_btts_non)
