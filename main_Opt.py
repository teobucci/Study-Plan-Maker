from pulp import *
import pandas as pd
from tkinter import filedialog as fd
from tkinter import *
import streamlit as st
import base64

from gen_piano import genera_piano


# Interfaccia web
st.title('Compilatore Piano di studi MST')

st.markdown("""
Questa app realizza il miglior piano di studio possibile a partire dalla prefereze dei corsi inseriti
* **Python libraries:** base64, pandas, streamlit, pulp
""")


st.write("Scarica il file di esempio e compila la colonna di preferenze")

PATH = "Source.xlsx"
df_base = pd.read_excel(PATH)
df_base['Rating'] = 0


def filedownload(df):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # strings <-> bytes conversions
    href = f'<a href="data:file/csv;base64,{b64}" download="playerstats.csv">Download CSV File</a>'
    return href


st.markdown(filedownload(df_base), unsafe_allow_html=True)

st.write("Carica il file con le preferenze")

df = df_base

uploaded_file = st.file_uploader("Upload your input CSV file", type=["csv"])
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.write('File caricato correttamente')


st.dataframe(df)

if st.button('Calcola piano'):
    piano = genera_piano(df)
    st.dataframe(piano)
