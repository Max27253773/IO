import streamlit as st
import pandas as pd
import requests
import time

# --- CONFIGURATION ---
# Votre URL de lecture (CSV)
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1mmPHzEY9p7ohdzvIYvwQOvqmKNa_8VQdZyl4sj1nksw/export?format=csv&gid=0"
# Votre NOUVELLE URL de script
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxhetuY5QpJEvl-Wv1BMGej5FeW6S3-WDcbS1DwcwUVT-Yt3e8th1XG9pPCcbrwPu5ITw/exec"

st.set_page_config(page_title="Planning Simu", layout="wide")
st.title("✈️ Planning Équipages")

# Fonction de lecture optimisée
@st.cache_data(ttl=5)
def load_data():
    try:
        # On ajoute un horodatage pour éviter que Google ne renvoie une vieille version cachée
        url_force = f"{SHEET_CSV_URL}&cache_bust={time.time()}"
        data = pd.read_csv(url_force)
        # Conversion de la colonne Date pour un tri correct
        data['Date'] = pd.to_datetime(data['Date'], errors='coerce')
        return data
    except:
        return pd.DataFrame(columns=["Date", "Equipage", "Horaire", "Simu"])

df = load_data()

menu = st.sidebar.selectbox("Menu", ["Consulter le Planning", "Administration 🔐"])

if menu == "Consulter le Planning":
    st.subheader("Programme de la semaine")
    if df.empty or len(df.columns) < 2:
        st.info("Aucune séance de prévue pour le moment.")
    else:
        # Tri des séances par date
        df_view = df.sort_values(by="Date", ascending=True)
        
        for _, row in df_view.iterrows():
            d_str = row['Date'].strftime('%d/%m/%Y') if pd.notnull(row['Date']) else "Date ?"
            with st.expander(f"📅 {d_str} — {row['Equipage']}"):
                st.write(f"**⏰ Horaire :** {row['Horaire']}")
                st.write(f"**🖥️ Simulateur :** {row['Simu']}")

elif menu == "Administration 🔐":
    pwd = st.sidebar.text_input("Code Admin", type="password")
    if pwd == "1234":
        st.subheader("🛠️ Ajouter une séance")
        
        with st.form("form_ajout", clear_on_submit=True):
            d = st.date_input("Date de la séance")
            e = st.text_input("Noms de l'équipage")
            h = st.text_input("Créneau horaire (ex: 08:30 - 12:30)")
            s = st.selectbox("Choisir le Simulateur", ["SIM 1", "SIM 2", "SIM 3"])
            
            submit = st.form_submit_button("Enregistrer")
            
            if submit:
                if e and h:
                    # Envoi des données au format JSON
                    payload = {
                        "action": "add",
                        "date": str(d),
                        "equipage": e,
                        "horaire": h,
                        "simu": s
                    }
                    try:
                        # Utilisation de 'data' au lieu de 'json' pour certains environnements Google
                        response = requests.post(SCRIPT_URL, json=payload, timeout=10)
                        if response.status_code == 200:
                            st.success("✅ Séance ajoutée ! Retournez dans le menu Planning.")
                            st.cache_data.clear()
                        else:
                            st.error(f"Erreur serveur ({response.status_code})")
                    except Exception as err:
                        st.error(f"Erreur de connexion : {err}")
                else:
                    st.warning("Merci de remplir tous les champs.")
        
        st.markdown("---")
        if st.button("🗑️ Supprimer la dernière séance"):
            try:
                requests.post(SCRIPT_URL, json={"action": "clear_last"})
                st.warning("Dernière ligne supprimée.")
                st.cache_data.clear()
            except:
                st.error("Impossible de supprimer.")
    else:
        st.info("Entrez le code admin pour modifier le planning.")
