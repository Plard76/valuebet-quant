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

# Interrupteur pour le marché combiné "BTTS ou +2.5" : mêmes cotes que le BTTS simple
# quasiment à chaque fois observé (pas d'edge indépendant), donc masqué. Calcul intact plus bas.
SHOW_BTTS25 = False

st.markdown("**Les 2 équipes marquent (BTTS)**")
cb1, cb2 = st.columns(2)
bk_btts_oui = cb1.number_input("BTTS Oui", value=1.49, step=0.01, key="bk_btts_oui")
bk_btts_non = cb2.number_input("BTTS Non", value=2.33, step=0.01, key="bk_btts_non")

st.markdown("**Les 2 équipes marquent OU + de 2.5 buts (gardé en mémoire, non utilisé pour le moment)**")
if SHOW_BTTS25:
    cbo1, cbo2 = st.columns(2)
    bk_btts25_oui = cbo1.number_input("BTTS+2.5 Oui", value=1.55, step=0.01, key="bk_btts25_oui")
    bk_btts25_non = cbo2.number_input("BTTS+2.5 Non", value=2.20, step=0.01, key="bk_btts25_non")
else:
    st.caption("Masqué — passe SHOW_BTTS25 à True en haut du fichier pour le revoir.")

st.markdown("**Variation de la cote (source : oddssafari.com/dropping-odds)**")
st.caption("Rentre le % affiché par OddsSafari (négatif si la cote a baissé, ex: -13 pour -13%). Un drop d'au moins -10% (seuil OddsSafari) confirme le signal.")
DROP_THRESHOLD = -10.0  # %, seuil de confirmation — aligné sur le filtre natif d'OddsSafari
cm1, cm2 = st.columns(2)
pct_btts_oui = cm1.number_input("Variation BTTS Oui (%)", value=0.0, step=1.0, key="pct_btts_oui")
pct_btts_non = cm2.number_input("Variation BTTS Non (%)", value=0.0, step=1.0, key="pct_btts_non")

if SHOW_BTTS25:
    cm3, cm4 = st.columns(2)
    pct_btts25_oui = cm3.number_input("Variation BTTS+2.5 Oui (%)", value=0.0, step=1.0, key="pct_btts25_oui")
    pct_btts25_non = cm4.number_input("Variation BTTS+2.5 Non (%)", value=0.0, step=1.0, key="pct_btts25_non")

st.markdown("**Cotes Over / Under (gardées en mémoire, non utilisées pour le moment)**")
if SHOW_OVER_UNDER:
    co1, co2, co3 = st.columns(3)
    bk_o15 = co1.number_input("Over 1.5", value=1.25, step=0.01, key="bk_o15")
    bk_o25 = co2.number_input("Over 2.5", value=1.80, step=0.01, key="bk_o25")
    bk_u25 = co3.number_input("Under 2.5", value=1.95, step=0.01, key="bk_u25")
else:
    st.caption("Masquées — passe SHOW_OVER_UNDER à True en haut du fichier pour les revoir.")

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
p_btts_and_over25 = 0.0  # intersection : sert au marché combiné "BTTS ou +2.5"
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
        btts_ici = x > 0 and y > 0
        if btts_ici: p_btts_oui += p

        # OVER / UNDER
        total_goals = x + y
        if total_goals > 1.5: p_over_15 += p
        if total_goals > 2.5: p_over_25 += p
        if total_goals > 3.5: p_over_35 += p

        # Intersection BTTS et Over 2.5 (les 2 conditions vraies sur le même score)
        if btts_ici and total_goals > 2.5: p_btts_and_over25 += p

p_btts_non = 1.0 - p_btts_oui
p_under_25 = 1.0 - p_over_25
xg_total = lambda_val + mu_val
xg_total_prudent = xg_total * XG_SAFETY_COEFFICIENT

# Marché combiné "Les 2 équipes marquent OU +2.5 buts" : union des 2 événements
# P(A ou B) = P(A) + P(B) - P(A et B)
p_btts_ou_25 = p_btts_oui + p_over_25 - p_btts_and_over25
p_btts_ou_25_non = 1.0 - p_btts_ou_25

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


def display_card(title, bk, prob, pct_change=0.0):
    prob_quant = prob * 100

    # --- Edge en POINTS (proba modèle - proba implicite de la cote) ---
    implied_prob = (1 / bk) if bk > 0 else 0
    edge_points = (prob - implied_prob) * 100  # écart brut, sert à l'affichage
    fair = 1 / prob if prob > 0 else 0  # cote juste mini = seuil de rentabilité pur, sans marge

    # --- ROI attendu (valeur espérée par euro misé) — indicateur complémentaire, affiché à part ---
    roi = ((bk * prob) - 1) * 100 if bk > 0 else 0

    # --- Seuils de badge ---
    EDGE_THRESHOLD_ULTRA = 3.0  # pts
    is_val = edge_points > 0 and bk > 0
    is_ultra = is_val and edge_points > EDGE_THRESHOLD_ULTRA and prob_quant >= 75.0

    # --- Décision finale : vert UNIQUEMENT si edge positif ET drop de cote >= seuil (marché qui confirme) ---
    movement_confirms = pct_change <= DROP_THRESHOLD
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
        # Edge positif mais drop de cote insuffisant (< seuil) -> pas de vert
        card_bg = "background-color: #1e293b; border: 1px solid #f59e0b;"
        badge = f'<div style="color: #f59e0b; font-weight: bold; font-size: 1rem; margin-top: 6px;">+{edge_points:.1f} pts d\'edge, mais non confirmé par le marché</div>'
    else:
        card_bg = "background-color: #1e293b; border: 1px solid #334155;"
        badge = f'<div style="color: #ef4444; font-weight: bold; font-size: 1rem; margin-top: 6px;">NO VALUE ({edge_points:+.1f} pts)</div>'

    # --- Interprétation de la variation de cote (purement indicative) ---
    movement_html = ""
    if pct_change != 0.0:
        if pct_change <= DROP_THRESHOLD:
            mvt_note = f"drop ≥ seuil ({DROP_THRESHOLD:.0f}%) → confirmation forte, signal favorable pour jouer."
            mvt_color = "#10b981"
        elif pct_change < 0:
            mvt_note = f"baisse mais sous le seuil ({DROP_THRESHOLD:.0f}%) → signal trop faible pour confirmer seul."
            mvt_color = "#f59e0b"
        else:
            mvt_note = "cote en hausse → le marché s'éloigne de ce résultat, signal défavorable."
            mvt_color = "#ef4444"
        movement_html = f'<div style="font-size: 0.8rem; color: {mvt_color}; margin-top: 4px; margin-bottom: 4px;">{pct_change:+.0f}% — {mvt_note}</div>'

    # --- Verdict final, gros et en gras ---
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


# OVER / UNDER — masqué pour l'instant (voir SHOW_OVER_UNDER en haut du fichier), code intact
if SHOW_OVER_UNDER:
    st.markdown("#### ⚽ OVER / UNDER")
    display_card("OVER 1.5 BUTS", bk_o15, p_over_15)
    display_card("OVER 2.5 BUTS", bk_o25, p_over_25)
    display_card("UNDER 2.5 BUTS", bk_u25, p_under_25)

# BTTS — marché actif
st.markdown("#### 🎯 MARCHÉ LES 2 ÉQUIPES MARQUENT (BTTS)")
display_card("BTTS OUI", bk_btts_oui, p_btts_oui, pct_change=pct_btts_oui)
display_card("BTTS NON", bk_btts_non, p_btts_non, pct_change=pct_btts_non)

# BTTS ou +2.5 — marché combiné, masqué (voir SHOW_BTTS25 en haut du fichier), code intact
if SHOW_BTTS25:
    st.markdown("#### 🎯 BTTS OU + DE 2.5 BUTS")
    display_card("BTTS+2.5 OUI", bk_btts25_oui, p_btts_ou_25, pct_change=pct_btts25_oui)
    display_card("BTTS+2.5 NON", bk_btts25_non, p_btts_ou_25_non, pct_change=pct_btts25_non)
