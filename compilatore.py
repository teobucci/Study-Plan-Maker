#!/usr/bin/env python

# importo le librerie
import pandas as pd
import pulp
import logging


# importo le funzioni
from os.path import join
from itertools import product


def generate_plan(dfu, track_choice='MST', CFU_max_sem=35, CFU_max_tot=121, PATH_CFU_COSTRAINTS=join('assets', 'min_CFUs.xlsx')):

    # PARAMETRI DA SCEGLIERE

    # scelta del track
    #choices = ['MCS', 'MMF', 'MST']
    #track = choices[track_choice]
    track = track_choice
    print(f'You chose {track}. Congratulations!')

    df_cfu = pd.read_excel(PATH_CFU_COSTRAINTS, index_col=0).dropna()
    df_cfu[track] = 0  #  aggiungo colonna il gruppo del track con minimo 0 CFU

    GROUPS_names = df_cfu.columns.tolist()
    min_cfus = df_cfu.loc[track].tolist()

    # DATAFRAME CORSI OBBLIGATORI
    PATH1 = join('assets', 'source_'+track+'_1.xlsx')
    PATH2 = join('assets', 'source_'+track+'_2.xlsx')
    # comp = compulsory
    df_comp1 = pd.read_excel(PATH1).dropna()
    df_comp2 = pd.read_excel(PATH2).dropna()
    comp1 = len(df_comp1)
    comp2 = len(df_comp2)
    df_comp = pd.concat([df_comp1, df_comp2])  # unisco i compulsory dei due anni
    df_comp.reset_index(inplace=True, drop=True)  # reset dell'index 0-4,0-1

    logging.info(df_comp)

    # dropna per rimuovere le righe senza rating, valgono 0 e non le consideriamo
    df_user = dfu  # pd.read_excel('source.xlsx', index_col=0).dropna()

    # anche le righe dove il rating è 0 le eliminiamo per risparmiare variabili
    df_user = df_user[df_user['Rating'] != 0]

    df_user['Gruppo'] = df_user['Gruppo'].apply(eval)  # serve perché nel file i gruppi sono ['FREE'], mentre vogliamo [FREE]
    logging.info(df_user)

    # creo un dataframe per dare corrispondenza codice-denominazione
    code_name = pd.concat([df_comp, df_user]).set_index('Codice')

    # tolgo le colonne non necessarie
    code_name.drop(columns=['Sem', 'CFU', 'Gruppo', 'Rating'], inplace=True)

    # NB ci si accede in questo modo
    # code_name.loc[56955]['Denominazione']

    # rimuovo i doppi indici
    # specificare quale tenere perché potrebbero a priori avere "Denominazione" diversa, ma non in questo caso perché uguale codice => uguale nome
    code_name = code_name[~code_name.index.duplicated(keep='last')]

    # converto in un dizionario
    code_name = code_name.to_dict()['Denominazione']

    # code_name

    df_user = df_user.drop(columns=['Denominazione'])
    df_comp = df_comp.drop(columns=['Denominazione'])

    df = pd.concat([df_comp, df_user]).reset_index(drop=True)  # drop serve per far si che il vecchio brutto indice non diventi una colonna

    # df.head(10)

    dfexplode = df.explode('Gruppo')
    # dfexplode.head()

    #dfcrosstab = pd.crosstab(dfexplode['Codice'], dfexplode['Gruppo']).ne(0).reset_index()
    dfcrosstab = pd.crosstab(dfexplode['Codice'], dfexplode['Gruppo'])
    # dfcrosstab.loc[52503]['FREE']
    # dfcrosstab.head()

    dict_base = df.to_dict()

    # PARAMETRI
    codes = dict_base['Codice']
    semester = dict_base['Sem']
    cfus = dict_base['CFU']
    rating = dict_base['Rating']

    # INSIEMI
    COURSES = list(codes.keys())
    YEARS = [1, 2]
    GROUPS = list(range(len(GROUPS_names)))

    # PROBLEMA
    prob = pulp.LpProblem('Piano_di_studi', pulp.const.LpMaximize)

    # VARIABILI
    x = pulp.LpVariable.dicts('corso-anno-gruppo', (COURSES, YEARS, GROUPS), lowBound=0, upBound=1, cat='Continuous')  # quanto corso i anno j gruppo k
    y = pulp.LpVariable.dicts('corso',             (COURSES),                lowBound=0, upBound=1, cat='Binary')      # 1 se corso i è scelto
    z = pulp.LpVariable.dicts('corso-anno',        (COURSES, YEARS),         lowBound=0, upBound=1, cat='Binary')      # 1 se corso i all'anno j

    # FUNZIONE OBIETTIVO
    prob += pulp.lpSum([rating[i]*cfus[i]*x[i][j][k] for (i, j, k) in product(COURSES, YEARS, GROUPS)])

    # VINCOLI

    # (richiesta) obbligatorietà dei corsi
    for i in range(comp1):
        # 5 dovrebbe essere l'indice dell'ultimo gruppo, quello "finto" della track
        prob += x[i][1][GROUPS[-1]] == 1, f"Compulsory course {i} in year 1"

    for i in range(comp1, comp1+comp2):
        prob += x[i][2][GROUPS[-1]] == 1, f"Compulsory course {i} in year 2"

    # (capacità) max cfu totali
    prob += pulp.lpSum([cfus[i]*x[i][j][k] for (i, j, k) in product(COURSES, YEARS, GROUPS)]) <= CFU_max_tot, f"Maximum total CFUs"
    #prob += pulp.lpSum([cfus[i]*y[i] for i in COURSES]) <= CFU_max_tot, f"Maximum total CFUs"

    # (capacità) max cfu per semestre per anno
    for j in YEARS:
        target_groups = [i for i in COURSES if semester[i] == 1]
        prob += pulp.lpSum([cfus[i]*x[i][j][k] for (i, k) in product(target_groups, GROUPS)]) <= CFU_max_sem, f"Maximum CFUs for year {j} semester 1"

        target_groups = [i for i in COURSES if semester[i] == 2]
        prob += pulp.lpSum([cfus[i]*x[i][j][k] for (i, k) in product(target_groups, GROUPS)]) <= CFU_max_sem, f"Maximum CFUs for year {j} semester 2"

    # (logico) se un corso è scelto allora z_ij = 1
    for (i, j) in product(COURSES, YEARS):
        prob += pulp.lpSum([x[i][j][k] for k in GROUPS]) <= 1000 * z[i][j], f"If course {i} chosen, then z[{i}][{j}]=1"

    # (capacità) non posso scegliere un corso in più anni (cioè mettere GAT metà al primo e metà al secondo annno per es.)
    for i in COURSES:
        prob += pulp.lpSum([z[i][j] for j in YEARS]) <= 1, f"Course {i} in no more than one year"

    # i prossimi due potrebbero essere riassunti in sum... = y[i] ma per discorsi di approssimazione forse meglio così

    # (logico) se un corso è scelto allora y[i]=1
    # (capacità) corso scelto al massimo una sola volta (<=1)
    for i in COURSES:
        prob += pulp.lpSum([x[i][j][k] for (j, k) in product(YEARS, GROUPS)]) <= y[i], f"If course {i} chosen, then y[{i}]=1"

    # (assegnamento) se y_i=1 allora tutti quanti sopra tutti i gruppi devono sommare a 1 (circa)
    for i in COURSES:
        prob += y[i] <= pulp.lpSum([x[i][j][k] for (j, k) in product(YEARS, GROUPS)]), f"If course {i} chosen, then sum of x[{i}][j][k]=1"

    # (richiesta) min cfu gruppo (nessun vincolo per l'ultimo che è quello della track)
    for k in GROUPS[:-1]:
        prob += pulp.lpSum([cfus[i]*x[i][j][k] for (i, j) in product(COURSES, YEARS)]) >= min_cfus[k], f"Minimum CFUs for group {k}"  # >=/==

    # (capacità) posso dare peso a un corso in un gruppo solo è consentito
    for (i, k) in product(COURSES, GROUPS):
        prob += pulp.lpSum([x[i][j][k] for j in YEARS]) <= dfcrosstab.loc[codes[i]][GROUPS_names[k]], f"Possibility to choose course {i} in group {k} only if allowed"

    # dfcrosstab.loc[52503]['FREE']
    # dfcrosstab.loc[codes[...]][GROUPS_names[...]]

    # RISOLUZIONE
    status = prob.solve()

    print(f"Status:    {pulp.LpStatus[status]}")
    print(f"Objective: {prob.objective.value()}")

    if status is not 1:
        return pd.DataFrame(), [], status

    # prob.constraints

    # prob.writeLP('pulp_problem_description.txt')

    # servono 2 out
    # - SOMMARIO, quello che uno ha bisogno di sapere, con le variabili z, quale corso in quale anno
    # - DETTAGLI, quello da dare a Gregoratti, quale percentuale di quale corso in quale gruppo, con le x

    corsi = []
    for (i, j, k) in product(COURSES, YEARS, GROUPS):
        val = x[i][j][k].varValue
        if val and val > 0:
            #codice = codes[i]
            #gruppo = GROUPS_names[k]
            #anno = YEARS[j-1]
            #string = f'{val*100:3.0f}% del corso: {codice}\t\tnel gruppo {gruppo}\t\tnell\'anno {anno}'
            # print(string)

            course_name = code_name[codes[i]]
            semester_name = semester[i]
            cfus_name = cfus[i]
            codes_name = codes[i]
            group_name = GROUPS_names[k]
            year_name = YEARS[j-1]
            el = [codes_name, course_name, cfus_name, group_name, year_name, semester_name, val]
            corsi.append(el)
            print(f"{val*100:3.0f}% di {course_name} [{group_name}, {cfus_name} CFU] all'anno {year_name} al semestre {semester_name}")
            # :3.0f

    piano = pd.DataFrame(corsi, columns=['Codice', 'Denominazione', 'CFU', 'Gruppo', 'Anno', 'Sem', '%'])
    piano = piano.set_index('Codice')
    piano = piano.sort_values(['Anno', 'Sem'], ascending=[True, True])

    logging.info(piano)

    total_cfus = pulp.lpSum([cfus[i]*x[i][j][k].varValue for (i, j, k) in product(COURSES, YEARS, GROUPS)])
    print(f'Total number of CFUs:      {total_cfus}')

    cfus_per_semester = []

    for j in YEARS:
        target_groups = [i for i in COURSES if semester[i] == 1]
        cfus_sem_1 = pulp.lpSum([cfus[i]*x[i][j][k].varValue for (i, k) in product(target_groups, GROUPS)])
        cfus_per_semester.append(cfus_sem_1)
        print(f'CFUs for year {j} semester 1: {cfus_sem_1}')

        target_groups = [i for i in COURSES if semester[i] == 2]
        cfus_sem_2 = pulp.lpSum([cfus[i]*x[i][j][k].varValue for (i, k) in product(target_groups, GROUPS)])
        cfus_per_semester.append(cfus_sem_2)
        print(f'CFUs for year {j} semester 2: {cfus_sem_2}')

    return piano, cfus_per_semester, status
