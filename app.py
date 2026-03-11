import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Configuration de la page
st.set_page_config(page_title="Planning Simulateur", layout="wide")

st.title("✈️ Planning Équipages")

# Simulation d'une base de données (on peut remplacer par un fichier .csv)
if 'planning' not in st.session_state:
    st.session_state.planning = pd.DataFrame([
        {"Semaine": 11, "Date": "2026-03-12", "Equipage": "DURAND / MARTIN", "Horaire": "08:00 - 12:00", "Simu": "SIM 1"},
        {"Semaine": 11, "Date": "2026-03-13", "Equipage": "PETIT / LUCAS", "Horaire": "14:00 - 18:00", "Simu": "SIM 2"}
    ])

# --- PARTIE VISUELLE (Pour l'équipe) ---
st.subheader("Programme de la semaine")

# Filtre par semaine
semaines = sorted(st.session_state.planning['Semaine'].unique())
choix_semaine = st.selectbox("Choisir la semaine :", semaines, index=len(semaines)-1)

# Affichage simplifié
df_filtre = st.session_state.planning[st.session_state.planning['Semaine'] == choix_semaine]

for index, row in df_filtre.iterrows():
    with st.expander(f"📅 {row['Date']} - {row['Equipage']}"):
        st.write(f"**Horaire :** {row['Horaire']}")
        st.write(f"**Appareil :** {row['Simu']}")

# --- PARTIE GESTION (Pour vous) ---
st.markdown("---")
with st.sidebar:
    st.subheader("Administration")
    mdp = st.text_input("Code d'accès", type="password")
    
    if mdp == "1234": # À personnaliser
        st.write("Ajouter une séance :")
        new_date = st.date_input("Date")
        new_eq = st.text_input("Équipage (Noms)")
        new_h = st.text_input("Créneau (ex: 09h-13h)")
        
        if st.button("Ajouter au planning"):
            new_data = {
                "Semaine": new_date.isocalendar()[1],
                "Date": str(new_date),
                "Equipage": new_eq,
                "Horaire": new_h,
                "Simu": "SIM 1"
            }
            # Logique pour enregistrer (ici en mémoire session)
            st.success("Séance ajoutée !")
