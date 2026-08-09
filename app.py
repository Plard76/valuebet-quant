# Extrait du code mis à jour pour le bloc Over / Under avec marge de sécurité :

xg_total = lambda_val + mu_val

st.markdown("#### ⚽ CONSEIL OVER / UNDER (AVEC MARGE DE SÉCURITÉ)")

if xg_total >= 2.70 and p_over_25 >= 0.58:
    st.success(f"🛡️ **RECOMMANDATION SÉCURISÉE : OVER 2.5 BUTS**\n\n- xG Cumulés : **{xg_total:.2f}** (Seuil de sécurité ≥ 2.70 atteint ✅)\n- Proba Poisson : **{p_over_25*100:.1f}%**")
    display_card("OVER 2.5 BUTS", bk_o25, p_over_25)
elif xg_total >= 2.10:
    st.warning(f"⚠️ **ZONE INTERMÉDIAIRE ({xg_total:.2f} xG)** : Trop juste pour l'Over 2.5 en toute sécurité. **Option recommandée : OVER 1.5 BUTS** (Proba : {p_over_15*100:.1f}%)")
    display_card("OVER 1.5 BUTS (SÉCURITÉ)", bk_o15, p_over_15)
else:
    st.info(f"🔒 **MATCH PEU OFFENSIF ({xg_total:.2f} xG)** : Recommandation vers les marchés **UNDER** ou **UNDER 3.5** (Proba : {(1-p_over_35)*100:.1f}%)")
    display_card("UNDER 2.5 BUTS", 1.0, 1.0 - p_over_25)
