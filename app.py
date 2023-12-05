import pandas as pd
import streamlit as st
import base64
import src.compilatore as compilatore
from os.path import join
import constants

st.markdown('# Study Plan maker')
st.markdown("### for the MSc in Mathematical Engineering")

CFU_max_tot = st.number_input('Max Total CFUs', min_value=120, max_value=122, value=121, step=1)
CFU_max_sem = st.number_input('Max CFUs per semester', min_value=30, max_value=80, value=35, step=1)

@st.cache_data
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

st.download_button('Download Example Source CSV File', data=df_base.to_csv(index=False).encode('utf-8'), file_name='study_plan_source_example.csv',)

st.write("To easily edit the CSV file without messing up the formatting, you can use this tool https://www.convertcsv.com/csv-viewer-editor.htm")

df = df_base

uploaded_file = st.file_uploader('Upload your input CSV file', type=['csv'], accept_multiple_files=False)
if uploaded_file:
    df = pd.read_csv(uploaded_file).dropna()
    st.success('File uploaded correctly.')


st.dataframe(df)

num_suboptimal = st.number_input('How many sub-optimal plans would you like to compute? (default: 0)', min_value=0, max_value=5, value=0, step=1)

if st.button('Compute the best Study Plan!'):
    if uploaded_file:
        plans, objective = compilatore.generate_plan(df, track=track_choice, CFU_max_sem=CFU_max_sem, CFU_max_tot=CFU_max_tot, num_suboptimal=num_suboptimal)

        if len(plans) == 0:
            st.error(constants.message_infeasible)
        elif len(plans) == num_suboptimal + 1:
            st.success(constants.message_success)

            for plan, obj in zip(plans, objective):
                st.dataframe(plan)
                cfu_tot = sum(plan['CFU']*plan['%'])
                cfu_sem = plan.groupby(['Anno', 'Sem'])['CFU'].sum()
                st.write(f'Total interest: {obj}')
                st.write(f'The total number of CFUs is: {cfu_tot}')
                st.write(f'Here is the number of CFUs per semester:')
                st.dataframe(cfu_sem)
                st.write(compilatore.get_exchangable_exams(plan, df, track_choice))
                #st.download_button('Download the generated Study Plan', data=piano.to_csv(index=False).encode('utf-8'), file_name='study_plan_output.csv',)
                st.markdown("""---""")
        else:
            st.success('Problem is Optimal!')
            st.warning('But the desired number of sub-optimal solutions could not be computed.')
    else:
        st.error('Please upload a valid input and try again.')

with st.expander("See explanation of the model"):
    st.write(constants.model_description)

with st.expander("About"):
    st.markdown(constants.disclaimer)
    st.markdown(constants.credits, unsafe_allow_html=True)
