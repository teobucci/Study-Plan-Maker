#!/usr/bin/env python

# importo le librerie
import pandas as pd
import pulp


# importo le funzioni
from os.path import join
from itertools import product


def generate_plan(dfu, track='MST', CFU_max_sem=35, CFU_max_tot=121, PATH_CFU_COSTRAINTS=join('assets', 'min_CFUs.xlsx'), N_SUBOPTIMAL=0):

    # PARAMETRI DA SCEGLIERE

    # scelta del track
    #choices = ['MCS', 'MMF', 'MST']
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

    # df_comp

    # dropna per rimuovere le righe senza rating, valgono 0 e non le consideriamo
    df_user = dfu  # pd.read_excel('source.xlsx', index_col=0).dropna()

    # anche le righe dove il rating è 0 le eliminiamo per risparmiare variabili
    df_user = df_user[df_user['Rating'] != 0]

    df_user['Gruppo'] = df_user['Gruppo'].apply(eval)  # serve perché nel file i gruppi sono ['FREE'], mentre vogliamo [FREE]
    # df_user

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

    # potrebbe succedere che non sono stati inseriti col rating esami di un intero gruppo
    # per esempio CSCL, ma questo fa si che non appaia nel crosstab, bisogna aggiungere
    # manualmente delle colonne con 0 per poterci accedere
    for group_name in GROUPS_names:
        if group_name not in dfcrosstab:
            dfcrosstab[group_name] = 0

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
        prob += y[i] <= pulp.lpSum([x[i][j][k] for (j, k) in product(YEARS, GROUPS)]), f"If y[{i}]=1 (i.e. course {i} chosen), then sum of x[{i}][j][k]=1"

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

    # TODO
    # anche una funzione che dal dataframe mandi in output i CFU
    # così è più easy ri-eseguire il problema un numero D (=DEEP) di volte

    if status != 1:
        return [], []

    objective = []
    objective.append(prob.objective.value())
    my_study_plans = []
    my_study_plans.append(get_plan_from_variables(x, COURSES, YEARS, GROUPS, code_name, codes, semester, cfus, GROUPS_names))

    epsilon = 0.1
    for i in range(N_SUBOPTIMAL):
        prob += pulp.lpSum([rating[i]*cfus[i]*x[i][j][k] for (i, j, k) in product(COURSES, YEARS, GROUPS)]) <= prob.objective.value() - epsilon
        status = prob.solve()

        print(f"Deep execution {i} Status:    {pulp.LpStatus[status]}")
        print(f"Deep execution {i} Objective: {prob.objective.value()}")

        if status == 1:
            new_plan = get_plan_from_variables(x, COURSES, YEARS, GROUPS, code_name, codes, semester, cfus, GROUPS_names)
            my_study_plans.append(new_plan)
            objective.append(prob.objective.value())
        else:  # non era ammissibile questo, quindi neanche i rimanenti, esco dal loop
            break

    # prob.writeLP('pulp_problem_description.txt')

    return my_study_plans, objective


def get_plan_from_variables(x, COURSES, YEARS, GROUPS, code_name, codes, semester, cfus, GROUPS_names, DEBUG=False):
    corsi = []
    for (i, j, k) in product(COURSES, YEARS, GROUPS):
        val = x[i][j][k].varValue
        if val and val > 0:

            course_name = code_name[codes[i]]
            semester_name = semester[i]
            cfus_name = cfus[i]
            codes_name = codes[i]
            group_name = GROUPS_names[k]
            year_name = YEARS[j-1]
            corsi.append([codes_name, course_name, cfus_name, group_name, year_name, semester_name, val])

            if DEBUG:
                print(f"{val*100:3.0f}% di {course_name} [{group_name}, {cfus_name} CFU] all'anno {year_name} al semestre {semester_name}")

    piano = pd.DataFrame(corsi, columns=['Codice', 'Denominazione', 'CFU', 'Gruppo', 'Anno', 'Sem', '%'])
    piano = piano.set_index('Codice')
    piano = piano.sort_values(['Anno', 'Sem'], ascending=[True, True])

    return piano


def get_exchangable_exams(plan, df, track_choice):
    output = ''
    for idx_chosen, exam_chosen in plan.iterrows():
        for idx_change, exam_change in df.iterrows():
            if exam_chosen['Gruppo'] == track_choice:  # quelli obbligatori non possono essere scambiati e non hanno un rating
                continue
            exchangable = (idx_chosen != exam_change['Codice']
                           and exam_chosen['CFU'] == exam_change['CFU']
                           and exam_chosen['Sem'] == exam_change['Sem']
                           and exam_chosen['Gruppo'] in eval(exam_change['Gruppo'])  # eval perché è da convertire in lista, di base è solo una stringa con "['STAT', 'ING', 'FREE']"
                           and df[df['Codice'] == idx_chosen]['Rating'].values[0] == exam_change['Rating']  # devo recuperare l'interesse dei corsi scelti perché non l'abbiamo trasportato
                           and exam_change['Codice'] not in plan.index  # per poterlo scambiare, non deve essere già nel piano
                           )

            if exchangable:
                output += 'You can exchange '+exam_chosen['Denominazione']+' with '+exam_change['Denominazione']+'.  \n'
    return output
