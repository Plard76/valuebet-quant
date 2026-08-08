import streamlit as st
import math

st.set_page_config(page_title="Calculateur ValueBet", page_icon="⚽", layout="centered")

# CSS personnalisé pour reproduire le style exact (boutons vert foncé, grands chiffres)
st.markdown("""
<style>
    .stNumberInput input {
        text-align: center;
        font-weight: bold;
        font-size: 1.2rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #1e4620;
        color: white;
        font-weight: bold;
        font-size: 1.2rem;
        padding: 12px;
        border-radius: 4px;
        border: none;
    }
    .stButton>button:hover {
        background-color: #2a5a2d;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

st.title("⚽ CALCULATEUR VALUEBET QUANT")

# =========================================================
# ÉTAPE 1 · ÉQUIPES (xG)
# =========================================================
st.markdown("### ÉTAPE 1 · ÉQUIPES")

c_dom, c_ext = st.columns(2)

with c_dom:
    st.markdown("**DOMICILE**")
    xgA_m = st.number_input("BUTS MARQUÉS / MATCH", value=1.67, step=0.01, key="xgA_m")
    xgA_c = st.number_input("BUTS ENCAISSÉS / MATCH", value=0.83, step=0.01, key="xgA_c")

with c_ext:
    st.markdown("**EXTÉRIEUR**")
    xgB_m = st.number_input("BUTS MARQUÉS / MATCH", value=1.00, step=0.01, key="xgB_m")
    xgB_c = st.number_input("BUTS ENCAISSÉS / MATCH", value=1.33, step=0.01, key="xgB_c")

st.write("")

# =========================================================
# ÉTAPE 2 · LE MARCHÉ (COTES BETCLIC)
# =========================================================
st.markdown("### ÉTAPE 2 · LE MARCHÉ")

st.markdown("**MATCH 1N2**")
c1, cN, c2 = st.columns(3)
bk_1 = c1.number_input("COTE 1", value=2.28, step=0.01)
bk_N = cN.number_input("COTE N", value=3.30, step=0.01)
bk_2 = c2.number_input("COTE 2", value=2.77, step=0.01)

st.markdown("**DRAW NO BET (DNB)**")
cd1, cd2 = st.columns(2)
bk_dnb1 = cd1.number_input("COTE DNB 1", value=1.63, step=0.01)
bk_dnb2 = cd2.number_input("COTE DNB 2", value=1.90, step=0.01)

st.markdown("**BUTS (2.5)**")
co25, cu25 = st.columns(2)
bk_o25 = co25.number_input("COTE OVER 2.5", value=1.70, step=0.01)
bk_u25 = cu25.number_input("COTE UNDER 2.5", value=1.95, step=0.01)

st.markdown("**BTTS**")
cb1, cb2 = st.columns(2)
bk_btts_oui = cb1.number_input("COTE BTTS OUI", value=1.49, step=0.01)
bk_btts_non = cb2.number_input("COTE BTTS NON", value=2.33, step=0.01)

st.write("")

# =========================================================
# BOUTON DE CALCUL & MODÈLE POISSON
# =========================================================
calc_clicked = st.button("CALCULER LES PROBABILITÉS")

# Calculs
lambda_val = (xgA_m + xgB_c) / 2
mu_val = (xgB_m + xgA_c) / 2

def poisson(k, lmbda):
    return (math.pow(lmbda, k) * math.exp(-lmbda)) / math.factorial(k)

p_1, p_N, p_2 = 0.0, 0.0, 0.0
p_o25, p_btts_oui = 0.0, 0.0
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
        if x > 0 and y > 0: p_btts_oui += p

p_u25 = 1.0 - p_o25
p_btts_non = 1.0 - p_btts_oui
p_dnb1 = p_1 / (p_1 + p_2) if (p_1 + p_2) > 0 else 0
p_dnb2 = p_2 / (p_1 + p_2) if (p_1 + p_2) > 0 else 0

st.divider()

# =========================================================
# BLOC RÉSULTAT : BUTS ATTENDUS PAR ÉQUIPE
# =========================================================
st.markdown(
    f"""
    <div style="background-color: #111827; padding: 15px; border-radius: 6px; text-align: center; margin-bottom: 20px; border: 1px solid #374151;">
        <div style="color: #9ca3af; font-size: 0.85rem; font-weight: bold; letter-spacing: 1px; margin-bottom: 5px;">BUTS ATTENDUS PAR ÉQUIPE</div>
        <div style="color: #ffffff; font-size: 2.2rem; font-weight: 900; font-family: monospace;">{lambda_val:.2f} — {mu_val:.2f}</div>
    </div>
    """,
    unsafe_allow_html=True
)

# =========================================================
# FONCTION D'AFFICHAGE DES CARTES DE RÉSULTATS (CÔTE À CÔTE)
# =========================================================
def render_pair_cards(title_left, bk_left, prob_left, title_right, bk_right, prob_right):
    def make_card_html(title, bk, prob):
        fair = 1 / prob if prob > 0 else 0
        prob_quant = prob * 100
        prob_book = (1 / bk * 100) if bk > 0 else 0
        is_val = bk > fair and bk > 0
        val_edge = (((bk * prob) - 1) * 100) if is_val else 0
        
        # Style exact de tes captures (Fond beige/clair si neutre, fond vert foncé si value)
        if is_val:
            bg_color = "#1e4620"
            txt_color = "#ffffff"
            sub_color = "#a7f3d0"
        else:
            bg_color = "#f3f4f6"
            txt_color = "#111827"
            sub_color = "#4b5563"
            
        edge_text = f"Edge estimé : +{val_edge:.1f} pts" if is_val else "NO VALUE"
        
        html = f"""
        <div style="background-color: {bg_color}; color: {txt_color}; padding: 16px; border-radius: 6px; text-align: center; margin-bottom: 10px;">
            <div style="font-size: 0.85rem; font-weight: bold; letter-spacing: 1px; margin-bottom: 8px;">{title}</div>
            <div style="font-size: 2.2rem; font-weight: 900; margin-bottom: 8px;">{prob_quant:.1f}%</div>
            <div style="font-size: 0.85rem; color: {sub_color}; margin-bottom: 4px;">cote proposée : {bk:.2f}</div>
            <div style="font-size: 0.85rem; color: {sub_color}; margin-bottom: 4px;">cote → {prob_book:.1f}% de proba</div>
            <div style="font-size: 0.9rem; font-weight: bold; color: {'#f59e0b' if is_val else '#ef4444'}; margin-top: 6px;">
                cote juste mini : ≥ {fair:.2f}
            </div>
            <div style="font-size: 0.85rem; font-weight: bold; margin-top: 6px; padding: 4px; background-color: rgba(0,0,0,0.15); border-radius: 4px;">
                {edge_text}
            </div>
        </div>
        """
        return html

    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown(make_card_html(title_left, bk_left, prob_left), unsafe_allow_html=True)
    with col_r:
        st.markdown(make_card_html(title_right, bk_right, prob_right), unsafe_allow_html=True)

# Affichage des marchés côte à côte
st.markdown("#### MARCHÉ BTTS")
render_pair_cards("BTTS OUI", bk_btts_oui, p_btts_oui, "BTTS NON", bk_btts_non, p_btts_non)

st.markdown("#### MARCHÉ OVER / UNDER 2.5")
render_pair_cards("OVER 2.5", bk_o25, p_o25, "UNDER 2.5", bk_u25, p_u25)

st.markdown("#### MARCHÉ DRAW NO BET")
render_pair_cards("DNB 1", bk_dnb1, p_dnb1, "DNB 2", bk_dnb2, p_dnb2)

st.markdown("#### MARCHÉ 1N2")
c1, c2, c3 = st.columns(3)
# Pour le 1N2, on affiche sur 3 colonnes côte à côte
def make_single_card(title, bk, prob):
    fair = 1 / prob if prob > 0 else 0
    prob_quant = prob * 100
    is_val = bk > fair and bk > 0
    bg_color = "#1e4620" if is_val else "#f3f4f6"
    txt_color = "#ffffff" if is_val else "#111827"
    
    return f"""
    <div style="background-color: {bg_color}; color: {txt_color}; padding: 12px; border-radius: 6px; text-align: center;">
        <div style="font-size: 0.8rem; font-weight: bold;">{title}</div>
        <div style="font-size: 1.6rem; font-weight: 900;">{prob_quant:.1f}%</div>
        <div style="font-size: 0.8rem;">cote : {bk:.2f}</div>
        <div style="font-size: 0.8rem; font-weight: bold; margin-top: 4px; color: {'#f59e0b' if is_val else '#ef4444'};">
            mini : ≥ {fair:.2f}
        </div>
    </div>
    """

with c1:
    st.markdown(make_single_card("1 (DOM)", bk_1, p_1), unsafe_allow_html=True)
with c2:
    st.markdown(make_single_card("N (NUL)", bk_N, p_N), unsafe_allow_html=True)
with c3:
    st.markdown(make_single_card("2 (EXT)", bk_2, p_2), unsafe_allow_html=True)
