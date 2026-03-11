import streamlit as st
import pandas as pd
import requests
import time
import json

# --- CONFIGURATION ---
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1mmPHzEY9p7ohdzvIYvwQOvqmKNa_8VQdZyl4sj1nksw/export?format=csv&gid=0"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxhetuY5QpJEvl-Wv1BMGej5FeW6S3-WDcbS1DwcwUVT-Yt3e8th1XG9pPCcbrwPu5ITw/exec"

st.set_page_config(page_title="Planning Simu Pro", layout="wide")
st.title("✈️ Gestion du Planning")

@st.cache_data(ttl=2)
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
        st.info("Le planning est vide.")
    else:
        for _, row in df.iterrows():
            with st.expander(f"📅 {row['Date']} — {row['Equipage']}"):
                st.write(f"**⏰ Horaire :** {row['Horaire']} | **🖥️ Simu :** {row['Simu']}")

elif menu == "Administration 🔐":
    pwd = st.sidebar.text_input("Code Admin", type="password")
    if pwd == "1234":
        tab1, tab2, tab3 = st.tabs(["➕ Ajouter", "📝 Modifier", "🗑️ Supprimer"])

        with tab1:
            with st.form("add_form", clear_on_submit=True):
                d, e, h = st.date_input("Date"), st.text_input("Equipage"), st.text_input("Horaire")
                s = st.selectbox("Simu", ["SIM 1", "SIM 2", "SIM 3"])
                if st.form_submit_button("Valider l'ajout"):
                    payload = {"action": "add", "date": str(d), "equipage": e, "horaire": h, "simu": s}
                    requests.post(SCRIPT_URL, data=json.dumps(payload))
                    st.success("✅ Ajouté ! Actualisez le planning.")
                    st.cache_data.clear()

        with tab2:
            if not df.empty:
                liste = [f"{row['Date']} - {row['Equipage']}" for _, row in df.iterrows()]
                choix = st.selectbox("Sélectionner la séance à modifier", options=liste)
                row_sel = df.iloc[liste.index(choix)]
                with st.form("edit_form"):
                    new_d = st.date_input("Nouvelle Date", value=pd.to_datetime(row_sel['Date']) if pd.notnull(row_sel['Date']) else None)
                    new_e = st.text_input("Nouvel Equipage", value=row_sel['Equipage'])
                    new_h = st.text_input("Nouvel Horaire", value=row_sel['Horaire'])
                    new_s = st.selectbox("Nouveau Simu", ["SIM 1", "SIM 2", "SIM 3"], index=0)
                    if st.form_submit_button("Mettre à jour"):
                        payload = {"action": "edit", "old_equipage": str(row_sel['Equipage']), "new_date": str(new_d), "new_equipage": new_e, "new_horaire": new_h, "new_simu": new_s}
                        requests.post(SCRIPT_URL, data=json.dumps(payload))
                        st.success("📝 Modifié !")
                        st.cache_data.clear()

        with tab3:
            if not df.empty:
                liste_del = [f"{row['Equipage']}" for _, row in df.iterrows()]
                choix_del = st.selectbox("Sélectionner l'équipage à supprimer", options=liste_del)
                if st.button("🗑️ Supprimer définitivement"):
                    payload = {"action": "delete", "equipage": choix_del}
                    requests.post(SCRIPT_URL, data=json.dumps(payload))
                    st.warning(f"Séance de {choix_del} supprimée.")
                    st.cache_data.clear()
                    time.sleep(1)
                    st.rerun()
    else:
        st.info("Entrez le code admin.")
