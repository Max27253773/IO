import streamlit as st
import pandas as pd
import requests
import time
import json
import re
from datetime import datetime, timedelta

# --- CONFIGURATION ---
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1mmPHzEY9p7ohdzvIYvwQOvqmKNa_8VQdZyl4sj1nksw/export?format=csv&gid=0"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxhetuY5QpJEvl-Wv1BMGej5FeW6S3-WDcbS1DwcwUVT-Yt3e8th1XG9pPCcbrwPu5ITw/exec"

# Couleurs pastel inspirées de votre image de référence
SIMU_CONFIG = {
    "Passerelle 1": "#B3E5FC", # Bleu
    "Machine": "#C8E6C9",      # Vert
    "Radar": "#FFF9C4",        # Jaune
    "Manœuvre": "#F8BBD0"      # Rose
}

st.set_page_config(page_title="Planning Naval Visuel", layout="wide", page_icon="⚓")

# --- STYLE CSS PERSONNALISÉ ---
st.markdown("""
    <style>
    .calendar-cell {
        padding: 8px;
        border-radius: 4px;
        margin-bottom: 5px;
        font-size: 13px;
        border: 1px solid rgba(0,0,0,0.1);
        color: #000000 !important;
        background-color: #f9f9f9;
    }
    .day-header {
        text-align: center;
        background-color: #003366;
        color: white;
        padding: 10px;
        border-radius: 5px;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .sim-label {
        font-weight: bold;
        color: #003366;
        padding: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FONCTIONS DE CALCUL ---
def extraire_heures_precises(horaire_str):
    try:
        blocs = re.findall(r'(\d+)[h:]?(\d+)?', str(horaire_str))
        if len(blocs) >= 2:
            h1, m1 = int(blocs[0][0]), int(blocs[0][1]) if blocs[0][1] else 0
            h2, m2 = int(blocs[1][0]), int(blocs[1][1]) if blocs[1][1] else 0
            return round(abs(((h2*60)+m2) - ((h1*60)+m1)) / 60, 2)
        return 4.0
    except: return 4.0

@st.cache_data(ttl=2)
def load_data():
    try:
        url_force = f"{SHEET_CSV_URL}&v={time.time()}"
        data = pd.read_csv(url_force)
        # Conversion forcée en datetime avec gestion des erreurs
        data['Date_DT'] = pd.to_datetime(data['Date'], errors='coerce')
        # On supprime les lignes où la date est invalide pour éviter les crashs
        data = data.dropna(subset=['Date_DT'])
        data['Heures'] = data['Horaire'].apply(extraire_heures_precises)
        return data
    except:
        return pd.DataFrame(columns=["Date", "Equipage", "Horaire", "Simu", "Date_DT", "Heures"])

df = load_data()

# --- NAVIGATION ---
menu = st.sidebar.selectbox("Navigation ⚓", ["📅 Planning Visuel", "📊 Résumé d'Activité", "🔐 Administration"])

# --- 1. PLANNING VISUEL (STYLE RESSOURCES) ---
if menu == "📅 Planning Visuel":
    st.title("🗓️ Calendrier de Planification")
    
    col_nav, _ = st.columns([2, 4])
    with col_nav:
        # Date de référence pour choisir la semaine
        selected_date = st.date_input("Semaine du :", datetime.now())
    
    # Calcul des limites de la semaine (Lundi au Dimanche)
    start_of_week = selected_date - timedelta(days=selected_date.weekday())
    week_days = [start_of_week + timedelta(days=i) for i in range(7)]
    day_names = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]

    # En-têtes des jours
    cols = st.columns([1.5] + [1]*7)
    cols[0].markdown("<div class='sim-label' style='text-align:center;'>Simulateurs</div>", unsafe_allow_html=True)
    for i, d in enumerate(week_days):
        cols[i+1].markdown(f"<div class='day-header'>{day_names[i]}<br>{d.strftime('%d/%m')}</div>", unsafe_allow_html=True)

    # Lignes par simulateur
    for simu, color in SIMU_CONFIG.items():
        row_cols = st.columns([1.5] + [1]*7)
        row_cols[0].markdown(f"<div class='sim-label'>{simu}</div>", unsafe_allow_html=True)
        
        for i, d in enumerate(week_days):
            # Filtrage sécurisé : on compare les dates uniquement
            if not df.empty:
                # On compare le format date (Y-m-d) pour éviter les problèmes de fuseaux horaires ou NaT
                mask = (df['Simu'] == simu) & (df['Date_DT'].dt.date == d)
                resas = df[mask]
            else:
                resas = pd.DataFrame()
            
            with row_cols[i+1]:
                if not resas.empty:
                    for _, r in resas.iterrows():
                        st.markdown(f"""
                            <div class="calendar-cell" style="background-color: {color};">
                                <b>{r['Equipage']}</b><br>
                                <span style='font-size:11px;'>{r['Horaire']}</span>
                            </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown('<div style="min-height:50px; border: 1px dashed #e0e0e0; border-radius:4px; margin-bottom:5px;"></div>', unsafe_allow_html=True)

# --- 2. RÉSUMÉ D'ACTIVITÉ ---
elif menu == "📊 Résumé d'Activité":
    st.header("📊 Statistiques d'entraînement")
    if df.empty:
        st.info("Aucune donnée enregistrée.")
    else:
        df['Annee'] = df['Date_DT'].dt.year
        annees = sorted(df['Annee'].unique().astype(int), reverse=True)
        sel_annee = st.selectbox("Année", annees)
        df_an = df[df['Annee'] == sel_annee]
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Heures totales", f"{round(df_an['Heures'].sum(), 1)}h")
        c2.metric("Équipages", df_an['Equipage'].nunique())
        c3.metric("Séances", len(df_an))
        
        st.subheader("Volume par équipage")
        st.bar_chart(df_an.groupby('Equipage')['Heures'].sum())

# --- 3. ADMINISTRATION ---
elif menu == "🔐 Administration":
    pwd = st.sidebar.text_input("Code", type="password")
    if pwd == "1234":
        t1, t2, t3 = st.tabs(["Ajouter", "Modifier", "Supprimer"])
        
        with t1:
            with st.form("add"):
                d = st.date_input("Date")
                e = st.text_input("Equipage")
                h = st.text_input("Horaire (ex: 08:30-12:00)")
                s = st.selectbox("Simulateur", list(SIMU_CONFIG.keys()))
                if st.form_submit_button("Enregistrer"):
                    requests.post(SCRIPT_URL, data=json.dumps({"action":"add","date":str(d),"equipage":e,"horaire":h,"simu":s}))
                    st.success("Séance ajoutée !")
                    st.cache_data.clear()

        with t2:
            if not df.empty:
                df['label'] = df['Date_DT'].dt.strftime('%Y-%m-%d') + " | " + df['Equipage']
                sel = st.selectbox("Sélectionner la séance", df['label'].tolist())
                idx = df[df['label'] == sel].index[0]
                row_sel = df.loc[idx]
                with st.form("edit"):
                    nd = st.date_input("Date", row_sel['Date_DT'])
                    ne = st.text_input("Equipage", row_sel['Equipage'])
                    nh = st.text_input("Horaire", row_sel['Horaire'])
                    ns = st.selectbox("Simu", list(SIMU_CONFIG.keys()), index=list(SIMU_CONFIG.keys()).index(row_sel['Simu']) if row_sel['Simu'] in SIMU_CONFIG else 0)
                    if st.form_submit_button("Modifier"):
                        requests.post(SCRIPT_URL, data=json.dumps({"action":"edit","row_index":int(idx),"new_date":str(nd),"new_equipage":ne,"new_horaire":nh,"new_simu":ns}))
                        st.cache_data.clear()
                        st.rerun()

        with t3:
            if not df.empty:
                df['label_del'] = df['Date_DT'].dt.strftime('%Y-%m-%d') + " | " + df['Equipage']
                sel_d = st.selectbox("Supprimer la séance", df['label_del'].tolist())
                idx_d = df[df['label_del'] == sel_d].index[0]
                if st.checkbox("Confirmer la suppression"):
                    if st.button("Supprimer"):
                        requests.post(SCRIPT_URL, data=json.dumps({"action":"delete","row_index":int(idx_d)}))
                        st.cache_data.clear()
                        st.rerun()
