import pandas as pd
import streamlit as st
import base64
import scripts.compilatore as mylib
from math import floor
from os.path import join

# Interfaccia web
st.markdown('# Study Plan maker')
st.markdown("### for the MSc in Mathematical Engineering")

CFU_max_tot = st.number_input('Max Total CFUs', min_value=120, max_value=122, value=121, step=1)
CFU_max_sem = st.number_input('Max CFUs per semester', min_value=30, max_value=80, value=35, step=1)


@st.cache
def format_func(track):
    return {
        'MCS': 'MCS - Computational Science and Computational Learning',
        'MMF': 'MMF - Quantitative Finance',
        'MST': 'MST - Statistical Learning'
    }[track]


track_choice = st.selectbox('Major', ('MCS', 'MMF', 'MST'), 2, format_func=format_func)

st.write('Download the example file and fill in the ``Rating`` column.')

PATH = join('assets', 'source.csv')
df_base = pd.read_csv(PATH, header=0)
df_base['Rating'] = 0


@st.cache
def filedownload(df):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # strings <-> bytes conversions
    href = f'<a href="data:file/csv;base64,{b64}" download="study_plan_source_example.csv">Download Example Source CSV File</a>'
    return href


#st.markdown(filedownload(df_base), unsafe_allow_html=True)

st.download_button('Download Example Source CSV File', data=df_base.to_csv(index=False).encode('utf-8'), file_name='study_plan_source_example.csv',)

st.write("To easily edit the CSV file without messing up the formatting, you can use this tool https://www.convertcsv.com/csv-viewer-editor.htm")

df = df_base

uploaded_file = st.file_uploader('Upload your input CSV file', type=['csv'], accept_multiple_files=False)
if uploaded_file:
    df = pd.read_csv(uploaded_file).dropna()
    st.success('File uploaded correctly.')


st.dataframe(df)


if st.button('Compute the best Study Plan!'):
    if uploaded_file:
        piano, cfus, status = mylib.generate_plan(df, track_choice=track_choice, CFU_max_sem=CFU_max_sem, CFU_max_tot=CFU_max_tot)
        if status == 1:
            st.success("Problem is Optimal!")
            st.dataframe(piano)
            st.write(f'Total number of CFUs: {sum(cfus)}')
            for idx, cfu in enumerate(cfus):
                st.write(f'CFUs for year {floor(idx/2)+1} semester {idx%2+1}: {cfu}')
            st.download_button('Download the generated Study Plan', data=piano.to_csv(index=False).encode('utf-8'), file_name='study_plan_output.csv',)
        else:
            st.error('Problem is Infeasible. Try again relaxing some constraints.')
    else:
        st.error('Please upload a valid input and try again.')
