import streamlit as st
import pandas as pd
import requests
import time

# --- CONFIGURATION ---
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1mmPHzEY9p7ohdzvIYvwQOvqmKNa_8VQdZyl4sj1nksw/export?format=csv&gid=0"
# Votre URL de script mise à jour
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxhetuY5QpJEvl-Wv1BMGej5FeW6S3-WDcbS1DwcwUVT-Yt3e8th1XG9pPCcbrwPu5ITw/exec"

st.set_page_config(page_title="Planning Simu Pro", layout="wide")
st.title("✈️ Gestion du Planning")

# Fonction de lecture
@st.cache_data(ttl=5)
def load_data():
    try:
        url_force = f"{SHEET_CSV_URL}&v={time.time()}"
        data = pd.read_csv(url_force)
        return data
    except:
        return pd.DataFrame(columns=["Date", "Equipage", "Horaire", "Simu"])

df = load_data()

menu = st.sidebar.selectbox("Menu", ["Consulter le Planning", "Administration 🔐"])

if menu == "Consulter le Planning":
    st.subheader("🗓️ Séances programmées")
    if df.empty or len(df.columns) < 2:
        st.info("Le planning est vide pour le moment.")
    else:
        # On s'assure que les dates sont traitées pour l'affichage
        for _, row in df.iterrows():
            with st.expander(f"📅 {row['Date']} — {row['Equipage']}"):
                st.write(f"**⏰ Horaire :** {row['Horaire']}")
                st.write(f"**🖥️ Simulateur :** {row['Simu']}")

elif menu == "Administration 🔐":
    pwd = st.sidebar.text_input("Code Admin", type="password")
    if pwd == "1234":
        tab1, tab2, tab3 = st.tabs(["➕ Ajouter", "📝 Modifier", "🗑️ Supprimer"])

        # --- ONGLET AJOUTER ---
        with tab1:
            with st.form("add_form", clear_on_submit=True):
                d = st.date_input("Date")
                e = st.text_input("Equipage")
                h = st.text_input("Horaire")
                s = st.selectbox("Simu", ["SIM 1", "SIM 2", "SIM 3"])
                if st.form_submit_button("Valider l'ajout"):
                    payload = {"action": "add", "date": str(d), "equipage": e, "horaire": h, "simu": s}
                    requests.post(SCRIPT_URL, json=payload)
                    st.success("✅ Séance ajoutée au Google Sheet !")
                    st.cache_data.clear()

        # --- ONGLET MODIFIER ---
        with tab2:
            if not df.empty:
                liste_seances = [f"{row['Date']} - {row['Equipage']}" for _, row in df.iterrows()]
                choix = st.selectbox("Sélectionner la séance à modifier", options=liste_seances)
                idx = liste_seances.index(choix)
                row_sel = df.iloc[idx]

                with st.form("edit_form"):
                    st.write("### Modifier les détails")
                    # On tente de convertir la date existante pour le sélecteur
                    try:
                        date_defaut = pd.to_datetime(row_sel['Date'])
                    except:
                        date_defaut = None

                    new_d = st.date_input("Nouvelle Date", value=date_defaut)
                    new_e = st.text_input("Nouvel Equipage", value=row_sel['Equipage'])
                    new_h = st.text_input("Nouvel Horaire", value=row_sel['Horaire'])
                    new_s = st.selectbox("Nouveau Simu", ["SIM 1", "SIM 2", "SIM 3"], 
                                       index=["SIM 1", "SIM 2", "SIM 3"].index(row_sel['Simu']) if row_sel['Simu'] in ["SIM 1", "SIM 2", "SIM 3"] else 0)
                    
                    if st.form_submit_button("Enregistrer les modifications"):
                        payload = {
                            "action": "edit",
                            "old_date": str(row_sel['Date']),
                            "old_equipage": str(row_sel['Equipage']),
                            "new_date": str(new_d),
                            "new_equipage": new_e,
                            "new_horaire": new_h,
                            "new_simu": new_s
                        }
                        requests.post(SCRIPT_URL, json=payload)
                        st.success("📝 Séance mise à jour !")
                        st.cache_data.clear()
            else:
                st.info("Rien à modifier.")

        # --- ONGLET SUPPRIMER ---
        with tab3:
            if not df.empty:
                liste_del = [f"{row['Date']} - {row['Equipage']}" for _, row in df.iterrows()]
                choix_del = st.selectbox("Sélectionner la séance à supprimer", options=liste_del)
                if st.button("🗑️ Supprimer définitivement"):
                    idx_del = liste_del.index(choix_del)
                    payload = {
                        "action": "delete", 
                        "date": str(df.iloc[idx_del]['Date']), 
                        "equipage": str(df.iloc[idx_del]['Equipage'])
                    }
                    requests.post(SCRIPT_URL, json=payload)
                    st.warning("Séance supprimée.")
                    st.cache_data.clear()
            else:
                st.info("Le planning est déjà vide.")
    else:
        st.info("Veuillez entrer le code pour modifier les données.")
