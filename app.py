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

# Définition des simulateurs et de leurs couleurs style "Pastel"
SIMU_CONFIG = {
    "Passerelle 1": "#B3E5FC", # Bleu
    "Machine": "#C8E6C9",      # Vert
    "Radar": "#FFF9C4",        # Jaune
    "Manœuvre": "#F8BBD0"      # Rose
}

st.set_page_config(page_title="Planning Naval Visuel", layout="wide", page_icon="⚓")

# --- STYLE CSS ---
st.markdown("""
    <style>
    .calendar-cell {
        padding: 8px;
        border-radius: 4px;
        margin-bottom: 4px;
        font-size: 13px;
        border: 1px solid rgba(0,0,0,0.1);
        color: #000000 !important;
        line-height: 1.2;
    }
    .day-header {
        text-align: center;
        background-color: #1E3A5F;
        color: white;
        padding: 10px;
        border-radius: 5px;
        font-weight: bold;
    }
    .sim-sidebar {
        font-weight: bold;
        color: #1E3A5F;
        padding-top: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FONCTIONS LOGIQUES ---
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
        # Nettoyage et conversion
        data['Date_DT'] = pd.to_datetime(data['Date'], errors='coerce')
        data['Annee'] = data['Date_DT'].dt.year
        data['Heures'] = data['Horaire'].apply(extraire_heures_precises)
        return data
    except:
        return pd.DataFrame(columns=["Date", "Equipage", "Horaire", "Simu", "Date_DT", "Heures"])

df = load_data()

# --- NAVIGATION ---
menu = st.sidebar.selectbox("Navigation ⚓", ["📅 Planning Visuel", "📊 Résumé d'Activité", "🔐 Administration"])

# --- 1. PLANNING VISUEL ---
if menu == "📅 Planning Visuel":
    st.title("🗓️ Calendrier de Planification des Ressources")
    
    # Sélecteur de semaine
    col_nav1, col_nav2 = st.columns([2, 4])
    with col_nav1:
        date_ref = st.date_input("Sélectionner une semaine", datetime.now())
    
    # Calcul des jours de la semaine choisie
    start_week = date_ref - timedelta(days=date_ref.weekday())
    days = [start_week + timedelta(days=i) for i in range(7)]
    days_names = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]

    st.write(f"### Semaine du {start_week.strftime('%d %B')} au {days[-1].strftime('%d %B %Y')}")

    # En-têtes
    cols = st.columns([1.5] + [1]*7)
    cols[0].markdown("<p style='text-align:center; font-weight:bold;'>Simulateurs</p>", unsafe_allow_html=True)
    for i, d in enumerate(days):
        cols[i+1].markdown(f"<div class='day-header'>{days_names[i]}<br>{d.strftime('%d/%m')}</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Grille de données
    for simu, color in SIMU_CONFIG.items():
        row_cols = st.columns([1.5] + [1]*7)
        row_cols[0].markdown(f"<p class='sim-sidebar'>{simu}</p>", unsafe_allow_html=True)
        
        for i, d in enumerate(days):
            # Filtrage précis par date
            if not df.empty:
                mask = (df['Simu'] == simu) & (df['Date_DT'].dt.date == d.date())
                resas = df[mask]
            else:
                resas = pd.DataFrame()
            
            with row_cols[i+1]:
                if not resas.empty:
                    for _, r in resas.iterrows():
                        st.markdown(f"""
                            <div class="calendar-cell" style="background-color: {color};">
                                <b>{r['Equipage']}</b><br>
                                <small>{r['Horaire']}</small>
                            </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown('<div style="min-height:50px; border: 0.5px solid #f0f2f6; border-radius:4px;"></div>', unsafe_allow_html=True)

# --- 2. RÉSUMÉ D'ACTIVITÉ ---
elif menu == "📊 Résumé d'Activité":
    st.header("📊 Synthèse d'entraînement")
    if df.empty or df['Date_DT'].isna().all():
        st.info("Aucune donnée à analyser.")
    else:
        annees = sorted(df['Annee'].dropna().unique().astype(int), reverse=True)
        sel_annee = st.selectbox("Année", annees)
        df_an = df[df['Annee'] == sel_annee]
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Volume total", f"{round(df_an['Heures'].sum(), 1)} h")
        c2.metric("Équipages", df_an['Equipage'].nunique())
        c3.metric("Séances", len(df_an))
        
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
                h = st.text_input("Horaire (ex: 08h00 - 12h00)")
                s = st.selectbox("Simulateur", list(SIMU_CONFIG.keys()))
                if st.form_submit_button("Enregistrer"):
                    requests.post(SCRIPT_URL, data=json.dumps({"action":"add","date":str(d),"equipage":e,"horaire":h,"simu":s}))
                    st.success("Ajouté !")
                    st.cache_data.clear()

        with t2:
            if not df.empty:
                df['label'] = df['Date'].astype(str) + " | " + df['Equipage']
                sel = st.selectbox("Sélectionner la séance à modifier", df['label'].tolist())
                idx = df[df['label'] == sel].index[0]
                row_sel = df.loc[idx]
                with st.form("edit"):
                    nd = st.date_input("Date", pd.to_datetime(row_sel['Date']))
                    ne = st.text_input("Equipage", row_sel['Equipage'])
                    nh = st.text_input("Horaire", row_sel['Horaire'])
                    ns = st.selectbox("Simu", list(SIMU_CONFIG.keys()), index=list(SIMU_CONFIG.keys()).index(row_sel['Simu']) if row_sel['Simu'] in SIMU_CONFIG else 0)
                    if st.form_submit_button("Modifier"):
                        requests.post(SCRIPT_URL, data=json.dumps({"action":"edit","row_index":int(idx),"new_date":str(nd),"new_equipage":ne,"new_horaire":nh,"new_simu":ns}))
                        st.cache_data.clear()
                        st.rerun()

        with t3:
            if not df.empty:
                df['label_del'] = df['Date'].astype(str) + " | " + df['Equipage']
                sel_d = st.selectbox("Séance à supprimer", df['label_del'].tolist())
                idx_d = df[df['label_del'] == sel_d].index[0]
                if st.checkbox("Confirmer la suppression"):
                    if st.button("Supprimer"):
                        requests.post(SCRIPT_URL, data=json.dumps({"action":"delete","row_index":int(idx_d)}))
                        st.cache_data.clear()
                        st.rerun()
