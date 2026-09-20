import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

st.set_page_config(page_title="Forgia & Laminatoio", layout="wide")

st.markdown("## ⭕⚙️ Controllo Forgiatura, Laminazione & Lavorabilità")
st.caption(
    "Sistema integrato multi-scheda: Billetta → Formagella → Preforma → Tranciatura "
    "→ Laminazione → Confronto 2D → Trattamento Termico → Controlli NDT → Report"
)

# =========================================================
# FUNZIONI DI CALCOLO (usate in tutte le schede)
# Convenzione: diametri/altezze in mm, volumi in cm3
# =========================================================

def area_cerchio_cm2(diametro_mm):
    """Area di un cerchio pieno, risultato in cm2 (input in mm)."""
    return np.pi * ((diametro_mm / 20) ** 2)

def area_anulare_cm2(diametro_est_mm, diametro_int_mm):
    """Area di una corona circolare (esterno - foro), risultato in cm2."""
    return area_cerchio_cm2(diametro_est_mm) - area_cerchio_cm2(diametro_int_mm)

def volume_cilindro_cm3(diametro_mm, altezza_mm):
    """Volume di un cilindro pieno, risultato in cm3."""
    return area_cerchio_cm2(diametro_mm) * (altezza_mm / 10)

def volume_anulare_cm3(diametro_est_mm, diametro_int_mm, altezza_mm):
    """Volume di una corona circolare (tubo), risultato in cm3."""
    return area_anulare_cm2(diametro_est_mm, diametro_int_mm) * (altezza_mm / 10)

def diametro_da_volume_pieno(volume_cm3, altezza_mm):
    """Diametro (mm) di un disco pieno dato volume (cm3) e altezza (mm)."""
    if altezza_mm <= 0:
        return 0.0
    area_cm2 = volume_cm3 / (altezza_mm / 10)
    if area_cm2 <= 0:
        return 0.0
    return np.sqrt(4 * area_cm2 / np.pi) * 10

def diametro_est_da_volume_anulare(volume_cm3, diametro_int_mm, altezza_mm):
    """Diametro esterno (mm) di una corona circolare dato volume (cm3), foro e altezza (mm)."""
    if altezza_mm <= 0:
        return 0.0
    area_netta_cm2 = volume_cm3 / (altezza_mm / 10)
    area_est_cm2 = area_netta_cm2 + area_cerchio_cm2(diametro_int_mm)
    if area_est_cm2 <= 0:
        return 0.0
    return np.sqrt(4 * area_est_cm2 / np.pi) * 10

DENSITA_TIPICHE = {
    "C22/C45 (Standard)": 7.85,
    "42CrMo4 (Legato)": 7.85,
    "Inox 304/316": 7.90,
}

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "1. Billetta & Formagella",
    "2. Preformatura",
    "3. Tranciatura",
    "4. Laminazione & Finito",
    "5. Confronto 2D",
    "6. Trattamento Termico",
    "7. Controlli NDT",
    "8. Report",
])

# =========================================================
# TAB 1: BILLETTA & FORMAGELLA
# =========================================================
with tab1:
    st.subheader("1. Billetta di Partenza")
    st.caption("Inserisci il peso richiesto e le misure della billetta: il sistema calcola il peso reale e lo confronta con quello richiesto.")

    c1, c2, c3 = st.columns(3)
    with c1:
        materiale = st.selectbox("Materiale", list(DENSITA_TIPICHE.keys()), key="mat")
        st.caption(f"Densità tipica: {DENSITA_TIPICHE[materiale]} g/cm³")
        densita = st.number_input("Peso Specifico (g/cm³)", value=DENSITA_TIPICHE[materiale], step=0.01, key="den")
    with c2:
        peso_richiesto_kg = st.number_input("Peso Richiesto (kg)", value=150.0, step=1.0, key="peso_req")
        diametro_billetta_mm = st.number_input("Diametro Billetta (mm)", value=200.0, step=1.0, key="bil_d")
    with c3:
        altezza_billetta_mm = st.number_input("Altezza Billetta (mm)", value=350.0, step=1.0, key="bil_a")

    volume_billetta_cm3 = volume_cilindro_cm3(diametro_billetta_mm, altezza_billetta_mm)
    peso_calcolato_kg = volume_billetta_cm3 * densita / 1000
    differenza_kg = peso_calcolato_kg - peso_richiesto_kg
    differenza_pct = (differenza_kg / peso_richiesto_kg * 100) if peso_richiesto_kg > 0 else 0

    st.markdown("---")
    m1, m2, m3 = st.columns(3)
    m1.metric("Peso Richiesto", f"{peso_richiesto_kg:.1f} kg")
    m2.metric("Peso Calcolato Billetta", f"{peso_calcolato_kg:.1f} kg", f"{differenza_kg:+.1f} kg")
    m3.metric("Scostamento", f"{differenza_pct:+.1f} %")

    if abs(differenza_pct) <= 2:
        st.success("✅ Billetta in linea con il peso richiesto (scostamento ≤ 2%).")
    elif differenza_kg > 0:
        st.warning("⚠️ Billetta più pesante del richiesto: valuta di ridurre altezza o diametro.")
    else:
        st.error("❌ Billetta più leggera del richiesto: rischio mancanza di materiale.")

    st.markdown("---")
    st.subheader("Formagella (Schiacciata Piatta)")
    st.caption("Il volume si conserva (a meno della % di scaglia forno). Inserisci l'altezza desiderata: il diametro viene calcolato di conseguenza.")

    cf1, cf2 = st.columns(2)
    with cf1:
        altezza_formagella_mm = st.number_input("Altezza Formagella Desiderata (mm)", value=180.0, step=1.0, key="f_alt")
    with cf2:
        with st.expander("Parametri avanzati"):
            scaglia_formagella_pct = st.number_input("% Scaglia Forno (perdita di ossidazione)", value=0.0, step=0.1, key="scaglia_f")

    volume_formagella_cm3 = volume_billetta_cm3 * (1 - scaglia_formagella_pct / 100)
    diametro_formagella_mm = diametro_da_volume_pieno(volume_formagella_cm3, altezza_formagella_mm)

    st.metric("Diametro Formagella Calcolato", f"{diametro_formagella_mm:.1f} mm")
    st.info(f"Volume utile dopo formagella: **{volume_formagella_cm3:.0f} cm³**")

# =========================================================
# TAB 2: PREFORMATURA
# =========================================================
with tab2:
    st.subheader("2. Dati Stampo (Fossa)")

    cs1, cs2, cs3 = st.columns(3)
    with cs1:
        altezza_fossa_mm = st.number_input("Altezza Fossa Stampo (mm)", value=200.0, step=1.0, key="s_fossa")
    with cs2:
        diametro_cima_collare_mm = st.number_input("Ø Cima Collare Stampo (mm)", value=280.0, step=1.0, key="s_top")
    with cs3:
        diametro_base_collare_mm = st.number_input("Ø Base Collare Stampo (mm)", value=310.0, step=1.0, key="s_base")

    st.markdown("##### Dati Spina (Sfondatura)")
    csp1, csp2, csp3 = st.columns(3)
    with csp1:
        diametro_spina_mm = st.number_input("Ø Spina (mm)", value=160.0, step=1.0, key="spina_d")
    with csp2:
        altezza_spina_mm = st.number_input("Altezza Spina (mm)", value=60.0, step=1.0, key="spina_h")
    with csp3:
        tolleranza_spina_mm = st.number_input("Tolleranza Chiusura a Pacco (± mm)", value=1.5, step=0.1, key="spina_tol",
                                               help="La spina chiude a pacco: non affonda oltre questa tolleranza rispetto alla sua altezza nominale.")

    st.info(f"Pozzetto atteso (cieco, non forato): **{altezza_spina_mm - tolleranza_spina_mm:.1f} – {altezza_spina_mm + tolleranza_spina_mm:.1f} mm**. "
            "Essendo cieco non toglie volume: il materiale viene solo spostato, non asportato.")

    st.markdown("---")
    st.subheader("Schiacciata di Preforma")
    st.caption("Inserisci l'altezza fascia realmente raggiunta schiacciando la formagella: il diametro esterno preformato viene calcolato per conservazione di volume.")

    cp1, cp2 = st.columns(2)
    with cp1:
        altezza_fascia_preforma_mm = st.number_input("Altezza Fascia Dopo Preforma (mm)", value=120.0, step=1.0, key="p_alt")
    with cp2:
        with st.expander("Parametri avanzati"):
            scaglia_preforma_pct = st.number_input("% Scaglia Aggiuntiva in Preforma", value=0.0, step=0.1, key="scaglia_p")

    volume_preforma_cm3 = volume_formagella_cm3 * (1 - scaglia_preforma_pct / 100)
    diametro_preforma_mm = diametro_da_volume_pieno(volume_preforma_cm3, altezza_fascia_preforma_mm)

    st.markdown("---")
    m1, m2, m3 = st.columns(3)
    m1.metric("Ø Preformato Calcolato", f"{diametro_preforma_mm:.1f} mm")
    m2.metric("Δ vs Base Collare", f"{diametro_preforma_mm - diametro_base_collare_mm:+.1f} mm")
    m3.metric("Δ vs Cima Collare", f"{diametro_preforma_mm - diametro_cima_collare_mm:+.1f} mm")
    st.info(f"Volume utile dopo preforma: **{volume_preforma_cm3:.0f} cm³**")

# =========================================================
# TAB 3: TRANCIATURA
# =========================================================
with tab3:
    st.subheader("3. Tranciatura (Sfondatura Foro)")
    st.caption("La tranciatura asporta il tondino centrale (materozza): il diametro esterno non cambia, cambia solo il foro. "
               "Il volume asportato viene scalato per la fase di laminazione.")

    ct1, ct2 = st.columns(2)
    with ct1:
        diametro_tranciatore_mm = st.number_input("Ø Tranciatore (mm)", value=170.0, step=1.0, key="t_tranc")
    with ct2:
        with st.expander("Confronto con misure reali (opzionale)"):
            altezza_fascia_misurata_mm = st.number_input("Altezza Fascia Misurata (mm)", value=0.0, step=1.0, key="t_misalt")
            diametro_esterno_misurato_mm = st.number_input("Ø Esterno Misurato (mm)", value=0.0, step=1.0, key="t_misest")

    volume_slug_cm3 = volume_cilindro_cm3(diametro_tranciatore_mm, altezza_fascia_preforma_mm)
    volume_dopo_tranciatura_cm3 = volume_preforma_cm3 - volume_slug_cm3
    diametro_esterno_dopo_tranciatura_mm = diametro_preforma_mm  # la tranciatura non modifica l'esterno
    diametro_foro_dopo_tranciatura_mm = diametro_tranciatore_mm

    st.markdown("---")
    st.success("🔍 **RISULTATO TRANCIATURA (teorico):**")
    m1, m2, m3 = st.columns(3)
    m1.metric("Vol. Materozza Asportata", f"{volume_slug_cm3:.0f} cm³")
    m2.metric("Ø Esterno (invariato)", f"{diametro_esterno_dopo_tranciatura_mm:.1f} mm")
    m3.metric("Ø Foro", f"{diametro_foro_dopo_tranciatura_mm:.1f} mm")
    st.info(f"Volume utile dopo tranciatura: **{volume_dopo_tranciatura_cm3:.0f} cm³**")

    if altezza_fascia_misurata_mm > 0 or diametro_esterno_misurato_mm > 0:
        st.markdown("##### Confronto con misure reali")
        cc1, cc2 = st.columns(2)
        if altezza_fascia_misurata_mm > 0:
            cc1.metric("Δ Altezza Fascia (reale - teorica)", f"{altezza_fascia_misurata_mm - altezza_fascia_preforma_mm:+.1f} mm")
        if diametro_esterno_misurato_mm > 0:
            cc2.metric("Δ Ø Esterno (reale - teorico)", f"{diametro_esterno_misurato_mm - diametro_esterno_dopo_tranciatura_mm:+.1f} mm")

# =========================================================
# TAB 4: LAMINAZIONE & FINITO
# =========================================================
with tab4:
    st.subheader("4. Riscaldo")

    cr1, cr2, cr3 = st.columns(3)
    with cr1:
        flag_riscaldo = st.radio("Effettuare nuovo riscaldo?", ["Sì", "No"], horizontal=True, key="r_flag")
    with cr2:
        temperatura_riscaldo_c = st.number_input("Temperatura Riscaldo (°C)", value=1200.0, step=10.0, key="r_temp",
                                                   disabled=(flag_riscaldo == "No"))
    with cr3:
        tempo_riscaldo_min = st.number_input("Tempo Riscaldo (min)", value=60.0, step=5.0, key="r_tempo",
                                              disabled=(flag_riscaldo == "No"))

    st.markdown("---")
    st.subheader("Laminazione (Rullatura Anello)")

    tipo_flangia = st.selectbox("Tipo di Flangia/Ralla", ["Flangia Piana", "Flangia a Collarino", "Ralla", "Flangia Cieca", "Altro"], key="tipo_flangia")

    cl1, cl2, cl3 = st.columns(3)
    with cl1:
        velocita_laminazione_mm_s = st.number_input("Velocità Crescita Raggio (mm/sec)", value=3.0, step=0.1, key="l_vel")
    with cl2:
        diametro_esterno_richiesto_mm = st.number_input("Ø Esterno Richiesto (mm)", value=450.0, step=1.0, key="l_dest")
    with cl3:
        diametro_foro_richiesto_mm = st.number_input("Ø Foro Richiesto (mm)", value=200.0, step=1.0, key="l_dfor")

    cl4, cl5 = st.columns(2)
    with cl4:
        altezza_fascia_richiesta_lam_mm = st.number_input("Altezza Fascia Richiesta (mm)", value=100.0, step=1.0, key="l_talt")
    with cl5:
        with st.expander("Parametri avanzati"):
            scaglia_laminazione_pct = st.number_input("% Scaglia in Laminazione", value=0.0, step=0.1, key="scaglia_l")

    volume_laminazione_cm3 = volume_dopo_tranciatura_cm3 * (1 - scaglia_laminazione_pct / 100)

    # Altezza teorica che risulterebbe con le quote esterne/foro richieste, per verificare coerenza col volume disponibile
    area_anulare_richiesta_cm2 = area_anulare_cm2(diametro_esterno_richiesto_mm, diametro_foro_richiesto_mm)
    altezza_teorica_lam_mm = (volume_laminazione_cm3 / area_anulare_richiesta_cm2 * 10) if area_anulare_richiesta_cm2 > 0 else 0
    diff_altezza_lam = altezza_teorica_lam_mm - altezza_fascia_richiesta_lam_mm

    crescita_raggio_mm = (diametro_esterno_richiesto_mm - diametro_esterno_dopo_tranciatura_mm) / 2
    tempo_laminazione_sec = (crescita_raggio_mm / velocita_laminazione_mm_s) if velocita_laminazione_mm_s > 0 else 0

    rapporto_crescita_foro = (diametro_foro_richiesto_mm / diametro_foro_dopo_tranciatura_mm
                               ) if diametro_foro_dopo_tranciatura_mm > 0 else 1
    cima_collare_stimato_mm = diametro_cima_collare_mm * rapporto_crescita_foro
    base_collare_stimato_mm = diametro_base_collare_mm * rapporto_crescita_foro

    st.markdown("---")
    st.success("📊 **STIMA LAMINAZIONE:**")
    m1, m2, m3 = st.columns(3)
    m1.metric("Altezza Teorica Risultante", f"{altezza_teorica_lam_mm:.1f} mm", f"{diff_altezza_lam:+.1f} mm vs richiesta")
    m2.metric("Tempo di Laminazione", f"{tempo_laminazione_sec:.1f} sec")
    m3.metric("Volume Disponibile", f"{volume_laminazione_cm3:.0f} cm³")

    st.caption("⚠️ Ø Cima/Base Collare stimati per proporzione rispetto alla crescita del diametro interno (foro): "
               "sono una stima geometrica semplificata, da verificare/correggere con dati reali di processo.")
    mc1, mc2 = st.columns(2)
    mc1.metric("Ø Cima Collare Stimato", f"{cima_collare_stimato_mm:.1f} mm")
    mc2.metric("Ø Base Collare Stimato", f"{base_collare_stimato_mm:.1f} mm")

    altezza_totale_richiesta_mm = st.number_input("Altezza Totale Pezzo Richiesta (mm)", value=140.0, step=1.0, key="l_talt_tot")

    st.markdown("---")
    st.subheader("Misure Finito (Disegno Macchina)")
    st.caption(f"Quote di disegno per il confronto finale — Tipo pezzo selezionato: **{tipo_flangia}**")

    cfi1, cfi2, cfi3 = st.columns(3)
    with cfi1:
        finito_diam_est_mm = st.number_input("Finito Ø Esterno (mm)", value=430.0, step=1.0, key="fin_est")
        finito_diam_foro_mm = st.number_input("Finito Ø Foro (mm)", value=210.0, step=1.0, key="fin_foro")
    with cfi2:
        finito_altezza_fascia_mm = st.number_input("Finito Altezza Fascia (mm)", value=90.0, step=1.0, key="fin_fascia")
        finito_altezza_totale_mm = st.number_input("Finito Altezza Totale (mm)", value=130.0, step=1.0, key="fin_tot")
    with cfi3:
        finito_diam_cima_collare_mm = st.number_input("Finito Ø Cima Collare (mm)", value=260.0, step=1.0, key="fin_top")
        finito_diam_base_collare_mm = st.number_input("Finito Ø Base Collare (mm)", value=300.0, step=1.0, key="fin_base")

    st.markdown("##### Confronto Teorico Laminazione vs Finito")
    confronto_dati = [
        ("Ø Esterno", diametro_esterno_richiesto_mm, finito_diam_est_mm),
        ("Ø Foro", diametro_foro_richiesto_mm, finito_diam_foro_mm),
        ("Altezza Fascia", altezza_teorica_lam_mm, finito_altezza_fascia_mm),
        ("Altezza Totale", altezza_totale_richiesta_mm, finito_altezza_totale_mm),
        ("Ø Cima Collare", cima_collare_stimato_mm, finito_diam_cima_collare_mm),
        ("Ø Base Collare", base_collare_stimato_mm, finito_diam_base_collare_mm),
    ]
    for nome, grezzo_v, finito_v in confronto_dati:
        sovra = grezzo_v - finito_v
        cA, cB, cC = st.columns(3)
        cA.write(f"**{nome}**")
        cB.write(f"Grezzo teorico: {grezzo_v:.1f} mm | Finito: {finito_v:.1f} mm")
        cC.write(f"Sovrametallo: {sovra:+.1f} mm")

# =========================================================
# TAB 5: CONFRONTO 2D
# =========================================================
with tab5:
    st.subheader("5. Confronto Lavorabilità & Incastro 2D")
    st.caption(f"Tipo pezzo: **{tipo_flangia}** — Grezzo = stima laminazione (Tab 4) · Finito = quote disegno (Tab 4)")

    g_est = diametro_esterno_richiesto_mm
    g_int = diametro_foro_richiesto_mm
    g_alt = altezza_teorica_lam_mm

    f_est = finito_diam_est_mm
    f_int = finito_diam_foro_mm
    f_alt = finito_altezza_fascia_mm

    sovra_est = (g_est - f_est) / 2
    sovra_int = (f_int - g_int) / 2
    sovra_alt = g_alt - f_alt

    lavorabile = (sovra_est > 0) and (sovra_int > 0) and (sovra_alt > 0)

    st.markdown("---")
    if lavorabile:
        st.success(f"✅ **PEZZO LAVORABILE** | Sovrametallo Ø Est (per lato): **{sovra_est:.1f} mm** | Ø Int (per lato): **{sovra_int:.1f} mm** | Altezza: **{sovra_alt:.1f} mm**")
    else:
        st.error(f"❌ **MANCANZA MATERIALE / CRITICO** | Sovra Ø Est: **{sovra_est:.1f} mm** | Ø Int: **{sovra_int:.1f} mm** | Altezza: **{sovra_alt:.1f} mm**")

    fig, ax = plt.subplots(figsize=(5, 5))
    ax.add_patch(plt.Circle((0, 0), g_est / 2, color='red', fill=False, linewidth=2, label='Grezzo'))
    ax.add_patch(plt.Circle((0, 0), g_int / 2, color='red', fill=False, linestyle='--', linewidth=2))
    ax.add_patch(plt.Circle((0, 0), f_est / 2, color='green', fill=False, linewidth=2, label='Finito'))
    ax.add_patch(plt.Circle((0, 0), f_int / 2, color='green', fill=False, linestyle='--', linewidth=2))

    limit = max(g_est, f_est) / 2 + 15 if max(g_est, f_est) > 0 else 100
    ax.set_xlim(-limit, limit)
    ax.set_ylim(-limit, limit)
    ax.set_aspect('equal')
    ax.grid(True, linestyle=':', alpha=0.5)
    ax.legend(loc='upper right', fontsize='small')
    st.pyplot(fig)

# =========================================================
# TAB 6: TRATTAMENTO TERMICO
# =========================================================
with tab6:
    st.subheader("6. Trattamento Termico")

    ct1, ct2 = st.columns(2)
    with ct1:
        tipo_trattamento = st.selectbox("Tipo Trattamento", ["Ricottura", "Normalizzazione", "Bonifica (Tempra + Rinvenimento)", "Distensione", "Altro"], key="tt_tipo")
        temperatura_trattamento_c = st.number_input("Temperatura Trattamento (°C)", value=650.0, step=10.0, key="tt_temp")
    with ct2:
        velocita_risalita_c_h = st.number_input("Velocità Risalita Forno (°C/h)", value=100.0, step=5.0, key="tt_vel")
        ore_mantenimento = st.number_input("Ore di Mantenimento", value=4.0, step=0.5, key="tt_ore")

    tempo_salita_h = (temperatura_trattamento_c / velocita_risalita_c_h) if velocita_risalita_c_h > 0 else 0
    tempo_trattamento_totale_h = tempo_salita_h + ore_mantenimento

    st.markdown("---")
    m1, m2 = st.columns(2)
    m1.metric("Tempo Salita Stimato", f"{tempo_salita_h:.1f} h")
    m2.metric("Tempo Ciclo Totale Stimato (salita + mantenimento)", f"{tempo_trattamento_totale_h:.1f} h")

# =========================================================
# TAB 7: CONTROLLI NON DISTRUTTIVI (NDT)
# =========================================================
with tab7:
    st.subheader("7. Controlli Non Distruttivi")

    operatore = st.text_input("Operatore", key="ndt_operatore")
    data_controllo = st.date_input("Data Controllo", key="ndt_data")

    def blocco_controllo(nome, key_prefix):
        st.markdown(f"##### {nome}")
        c1, c2 = st.columns([1, 2])
        with c1:
            esito = st.selectbox("Esito", ["Non Eseguito", "Conforme", "Non Conforme"], key=f"{key_prefix}_esito")
        with c2:
            note = st.text_input("Note", key=f"{key_prefix}_note")
        return esito, note

    visivo_esito, visivo_note = blocco_controllo("Controllo Visivo", "visivo")
    dimensionale_esito, dimensionale_note = blocco_controllo("Controllo Dimensionale", "dimensionale")
    lp_esito, lp_note = blocco_controllo("Liquidi Penetranti", "lp")
    mt_esito, mt_note = blocco_controllo("Magnetoscopico (Particelle Magnetiche)", "mt")
    ut_esito, ut_note = blocco_controllo("Ultrasuoni", "ut")

# =========================================================
# TAB 8: REPORT
# =========================================================
with tab8:
    st.subheader("8. Report Riepilogativo")
    st.caption("Genera un report HTML scaricabile con tutti i dati inseriti e calcolati. Apribile nel browser e stampabile in PDF.")

    if st.button("📄 Genera Report"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        file_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        def riga(nome, valore):
            return f"<tr><td>{nome}</td><td>{valore}</td></tr>"

        report_html = f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<title>Report Forgiatura & Laminazione</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 30px; color: #222; }}
h1 {{ border-bottom: 3px solid #444; padding-bottom: 8px; }}
h2 {{ background: #f0f0f0; padding: 6px 10px; margin-top: 30px; }}
table {{ border-collapse: collapse; width: 100%; margin-bottom: 15px; }}
td {{ border: 1px solid #ccc; padding: 6px 10px; }}
td:first-child {{ font-weight: bold; width: 40%; background: #fafafa; }}
</style>
</head>
<body>
<h1>Report Forgiatura, Laminazione & Controlli</h1>
<p>Generato il: {timestamp}</p>

<h2>1. Billetta & Formagella</h2>
<table>
{riga("Materiale", materiale)}
{riga("Peso Specifico", f"{densita:.2f} g/cm³")}
{riga("Peso Richiesto", f"{peso_richiesto_kg:.1f} kg")}
{riga("Ø Billetta", f"{diametro_billetta_mm:.1f} mm")}
{riga("Altezza Billetta", f"{altezza_billetta_mm:.1f} mm")}
{riga("Peso Calcolato Billetta", f"{peso_calcolato_kg:.1f} kg")}
{riga("Scostamento vs Richiesto", f"{differenza_pct:+.1f} %")}
{riga("Altezza Formagella", f"{altezza_formagella_mm:.1f} mm")}
{riga("Ø Formagella Calcolato", f"{diametro_formagella_mm:.1f} mm")}
</table>

<h2>2. Preformatura</h2>
<table>
{riga("Altezza Fossa Stampo", f"{altezza_fossa_mm:.1f} mm")}
{riga("Ø Cima Collare Stampo", f"{diametro_cima_collare_mm:.1f} mm")}
{riga("Ø Base Collare Stampo", f"{diametro_base_collare_mm:.1f} mm")}
{riga("Ø Spina", f"{diametro_spina_mm:.1f} mm")}
{riga("Altezza Spina", f"{altezza_spina_mm:.1f} mm")}
{riga("Altezza Fascia Dopo Preforma", f"{altezza_fascia_preforma_mm:.1f} mm")}
{riga("Ø Preformato Calcolato", f"{diametro_preforma_mm:.1f} mm")}
</table>

<h2>3. Tranciatura</h2>
<table>
{riga("Ø Tranciatore", f"{diametro_tranciatore_mm:.1f} mm")}
{riga("Volume Materozza Asportata", f"{volume_slug_cm3:.0f} cm³")}
{riga("Ø Esterno Dopo Tranciatura", f"{diametro_esterno_dopo_tranciatura_mm:.1f} mm")}
{riga("Ø Foro Dopo Tranciatura", f"{diametro_foro_dopo_tranciatura_mm:.1f} mm")}
</table>

<h2>4. Riscaldo & Laminazione</h2>
<table>
{riga("Nuovo Riscaldo", flag_riscaldo)}
{riga("Temperatura Riscaldo", f"{temperatura_riscaldo_c:.0f} °C" if flag_riscaldo == "Sì" else "N/A")}
{riga("Tempo Riscaldo", f"{tempo_riscaldo_min:.0f} min" if flag_riscaldo == "Sì" else "N/A")}
{riga("Tipo Flangia/Ralla", tipo_flangia)}
{riga("Ø Esterno Richiesto", f"{diametro_esterno_richiesto_mm:.1f} mm")}
{riga("Ø Foro Richiesto", f"{diametro_foro_richiesto_mm:.1f} mm")}
{riga("Altezza Fascia Richiesta", f"{altezza_fascia_richiesta_lam_mm:.1f} mm")}
{riga("Altezza Fascia Teorica Risultante", f"{altezza_teorica_lam_mm:.1f} mm")}
{riga("Tempo di Laminazione", f"{tempo_laminazione_sec:.1f} sec")}
{riga("Ø Cima Collare Stimato", f"{cima_collare_stimato_mm:.1f} mm")}
{riga("Ø Base Collare Stimato", f"{base_collare_stimato_mm:.1f} mm")}
</table>

<h2>Confronto Finale (Grezzo Teorico vs Finito Disegno)</h2>
<table>
{riga("Ø Esterno — Finito", f"{finito_diam_est_mm:.1f} mm")}
{riga("Ø Foro — Finito", f"{finito_diam_foro_mm:.1f} mm")}
{riga("Altezza Fascia — Finito", f"{finito_altezza_fascia_mm:.1f} mm")}
{riga("Altezza Totale — Finito", f"{finito_altezza_totale_mm:.1f} mm")}
{riga("Ø Cima Collare — Finito", f"{finito_diam_cima_collare_mm:.1f} mm")}
{riga("Ø Base Collare — Finito", f"{finito_diam_base_collare_mm:.1f} mm")}
{riga("Sovrametallo Ø Esterno (per lato)", f"{sovra_est:+.1f} mm")}
{riga("Sovrametallo Ø Foro (per lato)", f"{sovra_int:+.1f} mm")}
{riga("Sovrametallo Altezza", f"{sovra_alt:+.1f} mm")}
{riga("Esito Lavorabilità", "LAVORABILE" if lavorabile else "CRITICO / MANCANZA MATERIALE")}
</table>

<h2>6. Trattamento Termico</h2>
<table>
{riga("Tipo Trattamento", tipo_trattamento)}
{riga("Temperatura", f"{temperatura_trattamento_c:.0f} °C")}
{riga("Velocità Risalita Forno", f"{velocita_risalita_c_h:.0f} °C/h")}
{riga("Ore Mantenimento", f"{ore_mantenimento:.1f} h")}
{riga("Tempo Salita Stimato", f"{tempo_salita_h:.1f} h")}
{riga("Tempo Ciclo Totale Stimato", f"{tempo_trattamento_totale_h:.1f} h")}
</table>

<h2>7. Controlli Non Distruttivi</h2>
<table>
{riga("Operatore", operatore)}
{riga("Data Controllo", str(data_controllo))}
{riga("Controllo Visivo", f"{visivo_esito} — {visivo_note}")}
{riga("Controllo Dimensionale", f"{dimensionale_esito} — {dimensionale_note}")}
{riga("Liquidi Penetranti", f"{lp_esito} — {lp_note}")}
{riga("Magnetoscopico", f"{mt_esito} — {mt_note}")}
{riga("Ultrasuoni", f"{ut_esito} — {ut_note}")}
</table>

</body>
</html>
"""
        st.download_button(
            label="⬇️ Scarica Report (HTML)",
            data=report_html.encode("utf-8"),
            file_name=f"report_flangia_{file_timestamp}.html",
            mime="text/html",
        )
        st.success("Report generato. Clicca sopra per scaricarlo (apribile nel browser e stampabile in PDF).")
