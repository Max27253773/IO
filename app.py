import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Planning Simu", layout="wide")
st.title("✈️ Planning Équipages")

# Connexion sécurisée au Google Sheet
conn = st.connection("gsheets", type=GSheetsConnection)

# Lecture des données
# Note : on précise le nom de la feuille si nécessaire, sinon il prend la première
df = conn.read(ttl="1m") # ttl="1m" rafraîchit les données toutes les minutes

menu = st.sidebar.selectbox("Menu", ["Consulter le Planning", "Administration 🔐"])

if menu == "Consulter le Planning":
    if df.empty:
        st.info("Aucun vol prévu.")
    else:
        # On trie par date pour que ce soit lisible
        df_view = df.sort_values(by="Date")
        for _, row in df_view.iterrows():
            with st.expander(f"📅 {row['Date']} - {row['Equipage']}"):
                st.write(f"**Horaire :** {row['Horaire']}")
                st.write(f"**Appareil :** {row['Simu']}")

elif menu == "Administration 🔐":
    pwd = st.sidebar.text_input("Code Admin", type="password")
    if pwd == "1234":
        st.subheader("Ajouter une séance")
        with st.form("add_form"):
            d = st.date_input("Date")
            e = st.text_input("Equipage")
            h = st.text_input("Horaire")
            s = st.selectbox("Simu", ["SIM 1", "SIM 2", "SIM 3"])
            
            if st.form_submit_button("Enregistrer"):
                # On ajoute la nouvelle ligne au tableau actuel
                new_row = pd.DataFrame([{"Date": str(d), "Equipage": e, "Horaire": h, "Simu": s}])
                updated_df = pd.concat([df, new_row], ignore_index=True)
                
                # On renvoie tout vers Google Sheets
                conn.update(data=updated_df)
                st.success("Planning mis à jour sur Google Sheets !")
                st.rerun()
