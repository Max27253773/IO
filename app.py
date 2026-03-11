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

SIMU_CONFIG = {
    "Passerelle 1": "#B3E5FC", 
    "Machine": "#C8E6C9",      
    "Radar": "#FFF9C4",        
    "Manœuvre": "#F8BBD0"      
}

H_DEBUT = 6
H_FIN = 20
HAUTEUR_HEURE = 60 # 1 heure = 60 pixels

st.set_page_config(page_title="Planning Naval Précis", layout="wide", page_icon="⚓")

# --- STYLE CSS (POSITIONNEMENT PRÉCIS) ---
st.markdown(f"""
    <style>
    .planning-container {{
        position: relative;
        height: {(H_FIN - H_DEBUT) * HAUTEUR_HEURE}px;
        border-left: 1px solid #ddd;
        background-image: linear-gradient(#eee 1px, transparent 1px);
        background-size: 100% {HAUTEUR_HEURE}px; /* Lignes horizontales toutes les heures */
    }}
    .time-col-container {{
        height: {(H_FIN - H_DEBUT) * HAUTEUR_HEURE}px;
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
    }}
    .time-label {{
        height: {HAUTEUR_HEURE}px;
        display: flex;
        align-items: flex-start;
        justify-content: flex-end;
        padding-right: 10px;
        font-weight: bold;
        color: #003366;
        font-size: 14px;
        margin-top: -10px; /* Aligne le texte sur la ligne */
    }}
    .day-column {{
        position: relative;
        height: 100%;
        border-right: 1px solid #eee;
        background-color: rgba(255,255,255,0.5);
    }}
    .resa-block {{
        position: absolute;
        left: 2px;
        right: 2px;
        border-radius: 4px;
        border: 1px solid rgba(0,0,0,0.1);
        padding: 4px;
        font-size: 11px;
        font-weight: bold;
        color: #000;
        overflow: hidden;
        z-index: 10;
        box-shadow: 1px 1px 3px rgba(0,0,0,0.1);
    }}
    .day-header {{
        text-align: center;
        background-color: #003366;
        color: white;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- LOGIQUE DE CALCUL ---
def parse_horaire(h_str):
    try:
        times = re.findall(r'(\d+)[h:](\d+)?', str(h_str))
        res = []
        for t in times:
            h = int(t[0])
            m = int(t[1]) if t[1] else 0
            res.append(h + m/60)
        return res if len(res) >= 2 else None
    except: return None

@st.cache_data(ttl=2)
def load_data():
    try:
        url_force = f"{SHEET_CSV_URL}&v={time.time()}"
        data = pd.read_csv(url_force)
        data['Date_DT'] = pd.to_datetime(data['Date'], errors='coerce')
        return data.dropna(subset=['Date_DT'])
    except:
        return pd.DataFrame(columns=["Date", "Equipage", "Horaire", "Simu", "Date_DT"])

df = load_data()

# --- INTERFACE ---
st.title("⚓ Planning Haute Précision")

c1, c2, _ = st.columns([1.5, 1.5, 4])
with c1: annee_sel = st.selectbox("Année", [2025, 2026, 2027], index=1)
with c2: 
    curr_w = datetime.now().isocalendar()[1]
    semaine_sel = st.selectbox("Semaine", range(1, 54), index=curr_w-1)

# Calcul des jours
first_jan = datetime(annee_sel, 1, 4)
monday = (first_jan - timedelta(days=first_jan.weekday())) + timedelta(weeks=semaine_sel-1)
week_days = [monday + timedelta(days=i) for i in range(5)]

# En-têtes
cols = st.columns([0.6] + [1]*5)
for i, d in enumerate(week_days):
    cols[i+1].markdown(f"<div class='day-header'>{d.strftime('%A')}<br>{d.strftime('%d/%m')}</div>", unsafe_allow_html=True)

# Grille de temps
main_cols = st.columns([0.6] + [1]*5)

# Colonne des heures
with main_cols[0]:
    html_hours = "<div class='time-col-container'>"
    for h in range(H_DEBUT, H_FIN + 1):
        html_hours += f"<div class='time-label'>{h:02d}:00</div>"
    html_hours += "</div>"
    st.markdown(html_hours, unsafe_allow_html=True)

# Colonnes des jours avec blocs précis
for i, d in enumerate(week_days):
    with main_cols[i+1]:
        st.markdown("<div class='planning-container'>", unsafe_allow_html=True)
        
        day_resas = df[df['Date_DT'].dt.date == d.date()]
        
        for _, r in day_resas.iterrows():
            heures = parse_horaire(r['Horaire'])
            if heures:
                h_start, h_end = heures[0], heures[1]
                
                # Calcul de la position et de la taille
                top = (h_start - H_DEBUT) * HAUTEUR_HEURE
                height = (h_end - h_start) * HAUTEUR_HEURE
                color = SIMU_CONFIG.get(r['Simu'], "#EEEEEE")
                
                # Affichage du bloc
                st.markdown(f"""
                    <div class="resa-block" style="top: {top}px; height: {height}px; background-color: {color};">
                        {r['Equipage']}<br>
                        <span style="font-size:9px; font-weight:normal;">{r['Horaire']}</span>
                    </div>
                """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
