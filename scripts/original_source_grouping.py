import pandas as pd
from os.path import join

PATH_ORIGINAL_SOURCE = join('assets', 'source_from_polimi.xlsx')

df_source_polimi = pd.read_excel(PATH_ORIGINAL_SOURCE)

# così è un multiindex con il nome come indice
df_source = pd.DataFrame(df_source_polimi.groupby(['Denominazione', 'Codice', 'Sem', 'CFU', 'Rating'])['Gruppo'].apply(list))

# ora ritornano dei numeri come indice
df_source.reset_index(inplace=True)

# lo scrivo
# df_source.to_excel('source.xlsx')
df_source.to_csv('source.csv', index=False)
