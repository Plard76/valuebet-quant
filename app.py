import streamlit as st
import math

st.set_page_config(page_title="Calculateur Quant xG", page_icon="⚽", layout="centered")

st.title("⚽ CALCULATEUR QUANT - DNB, BTTS & OVER/UNDER")

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

st.divider()

# ---------------------------------------------------------
# 2. COTES BETCLIC
# ---------------------------------------------------------
st.subheader("📊 2. Cotes Betclic")

st.markdown("**Draw No Bet (DNB)**")
cd1, cd2 = st.columns(2)
bk_dnb1 = cd1.number_input("DNB 1", value=1.63, step=0.01, key="bk_dnb1")
bk_dnb2 = cd2.number_input("DNB 2", value=1.90, step=0.01, key="bk_dnb2")

st.markdown("**Les 2 équipes marquent (BTTS)**")
cb1, cb2 = st.columns(2)
bk_btts_oui = cb1.number_input("BTTS Oui", value=1.49, step=0.01, key="bk_btts_oui")
bk_btts_non = cb2.number_input("BTTS Non", value=2.33, step=0.01, key="bk_btts_non")

st.markdown("**Cotes Over / Under (Facultatif - laisser à 1.00 si non renseigné)**")
co1, co2, co3 = st.columns(3)
bk_o15 = co1.number_input("Over 1.5", value=1.25, step=0.01, key="bk_o15")
bk_o25 = co2.number_input("Over 2.5", value=1.80, step=0.01, key="bk_o25")
bk_o35 = co3.number_input("Over 3.5", value=3.00, step=0.01, key="bk_o35")

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
        
        # Correction Dixon-Coles
        if x == 0 and y == 0: p *= (1 - lambda_val * mu_val * rho)
        elif x == 1 and y == 0: p *= (1 + mu_val * rho)
        elif x == 0 and y == 1: p *= (1 + lambda_val * rho)
        elif x == 1 and y == 1: p *= (1 - rho)

        # 1N2
        if x > y: p_1 += p
        elif x == y: p_N += p
        else: p_2 += p

        # BTTS
        if x > 0 and y > 0: p_btts_oui += p

        # OVER / UNDER
        total_goals = x + y
        if total_goals > 1.5: p_over_15 += p
        if total_goals > 2.5: p_over_25 += p
        if total_goals > 3.5: p_over_35 += p

p_btts_non = 1.0 - p_btts_oui
p_dnb1 = p_1 / (p_1 + p_2) if (p_1 + p_2) > 0 else 0
p_dnb2 = p_2 / (p_1 + p_2) if (p_1 + p_2) > 0 else 0
xg_total = lambda_val + mu_val

st.divider()

# ---------------------------------------------------------
# 4. RÉSULTATS
# ---------------------------------------------------------
st.subheader("🎯 3. Résultats & ValueBets")

st.markdown(
    f"""
    <div style="background-color: #0f172a; padding: 10px; border-radius: 6px; text-align: center; margin-bottom: 16px; border: 1px solid #334155;">
        <div style="color: #94a3b8; font-size: 0.85rem; font-weight: bold; letter-spacing: 1px;">xG ATTENDUS DANS LE MATCH (λ + μ)</div>
        <div style="color: #f8fafc; font-size: 1.8rem; font-weight: 900; font-family: monospace;">{xg_total:.2f} BUTS ATTENDUS ({lambda_val:.2f} - {mu_val:.2f})</div>
    </div>
    """,
    unsafe_allow_html=True
)

def display_card(title, bk, prob):
    fair = 1 / prob if prob > 0 else 0
    prob_quant = prob * 100
    prob_book = (1 / bk * 100) if bk > 0 else 0
    
    is_val = bk > fair and bk > 1.0
    val_edge = (((bk * prob) - 1) * 100) if is_val else 0
    is_high_conf = is_val and prob_quant >= 75.0
    
    if is_high_conf:
        card_bg = "background-color: #064e3b; border: 2px solid #f59e0b;"
        badge = f"""
        <div style="background-color: #10b981; color: #000000; font-weight: 900; font-size: 1.1rem; padding: 6px; border-radius: 6px; text-align: center; margin-top: 6px;">
            🔥 ULTRA VALUE (+{val_edge:.1f}%) [PROBA > 75%]
        </div>
        """
    elif is_val:
        card_bg = "background-color: #1e4620; border: 1px solid #10b981;"
        badge = f'<div style="color: #10b981; font-weight: bold; font-size: 1.1rem; margin-top: 6px;">+{val_edge:.1f}% VALUE</div>'
    else:
        card_bg = "background-color: #1e293b; border: 1px solid #334155;"
        badge = '<div style="color: #ef4444; font-weight: bold; font-size: 1.1rem; margin-top: 6px;">NO VALUE</div>'
        
    st.markdown(
        f"""
        <div style="{card_bg} padding: 14px; border-radius: 10px; margin-bottom: 12px;">
            <div style="font-size: 1rem; color: #f1f5f9; font-weight: bold; margin-bottom: 6px;">{title}</div>
            <div style="font-size: 1.8rem; color: #38bdf8; font-weight: 900; margin-bottom: 6px;">{prob_quant:.1f}%</div>
            <div style="font-size: 0.95rem; color: #cbd5e1; margin-bottom: 4px;">
                Cote Betclic : <b style="color: #ffffff;">{bk:.2f}</b> | Cote juste mini : <b style="color: #f59e0b;">≥ {fair:.2f}</b>
            </div>
            {badge}
        </div>
        """,
        unsafe_allow_html=True
    )

# 1. DNB
st.markdown("#### 🎯 MARCHÉ DRAW NO BET (DNB)")
display_card("DNB 1", bk_dnb1, p_dnb1)
display_card("DNB 2", bk_dnb2, p_dnb2)

# 2. BTTS
st.markdown("#### 🎯 MARCHÉ LES 2 ÉQUIPES MARQUENT (BTTS)")
display_card("BTTS OUI", bk_btts_oui, p_btts_oui)
display_card("BTTS NON", bk_btts_non, p_btts_non)

# 3. OVER / UNDER AVEC MARGE DE SÉCURITÉ
st.markdown("#### ⚽ DIAGNOSTIC OVER / UNDER (MARGE DE SÉCURITÉ)")

if xg_total >= 2.70 and p_over_25 >= 0.58:
    st.success(f"✅ **RECOMMANDATION SÉCURISÉE : OVER 2.5 BUTS**\n\n- xG Cumulés : **{xg_total:.2f}** (Marge de sécurité ≥ 2.70 validée)\n- Probabilité : **{p_over_25*100:.1f}%**")
    display_card("OVER 2.5 BUTS", bk_o25, p_over_25)
elif xg_total >= 2.10:
    st.warning(f"🛡️ **OPTION SÉCURISÉE : OVER 1.5 BUTS**\n\n- xG Cumulés : **{xg_total:.2f}** (Trop juste pour l'Over 2.5 en toute sécurité).\n- L'Over 1.5 offre un taux de réussite très élevé : **{p_over_15*100:.1f}%**")
    display_card("OVER 1.5 BUTS (SÉCURISÉ)", bk_o15, p_over_15)
else:
    st.info(f"🔒 **MATCH PEU OFFENSIF : UNDER 2.5 BUTS**\n\n- xG Cumulés : **{xg_total:.2f}** (Match fermé / défensif).\n- Probabilité Under 2.5 : **{(1.0 - p_over_25)*100:.1f}%**")
    display_card("UNDER 2.5 BUTS", 1.0, 1.0 - p_over_25)
