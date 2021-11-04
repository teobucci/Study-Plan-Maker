import pulp
import pandas as pd
from tkinter import filedialog as fd
from tkinter import *

from itertools import product  # per il prodotto cartesiano tra insiemi


def genera_piano(df, CFU_max_sem=35, CFU_max_tot=122, MST=TRUE):

    df = df.dropna()
    dict_base = df.to_dict()

    # TODO quando facciamo il parsing, bisogna che ci sia un parametro che dice se un corso è obbligatorio o meno
    # in tal caso, aggiungiamo il suo id (0,1,2,3,...) a un gruppo speciale tipo MANDATORY_COURSES = [18,24,27,...]

    # GENERAZIONE DIZIONARI PARAMETRI
    names = dict_base['Denominazione']
    codes = dict_base['Codice']  # solo per output
    semester = dict_base['Sem']
    cfus = dict_base['CFU']
    group_full = dict_base['Gruppo']
    group_dic = dict_base['Gruppo_id']
    rating = dict_base['Rating']
    min_cfus = [10, 16, 10, 16, 0, 0]

    # INSIEMI
    # TODO far sì che queste cose siano dinamiche in base al source
    COURSES = list(names.keys())
    YEARS = [1, 2]
    GROUPS = [0, 1, 2, 3, 4, 5]

    # PARAMETRI

    # combos = [(i, j) for i in COURSES for j in YEARS]
    # combos = product(COURSES, YEARS, GROUPS)

    # PROBLEM
    prob = pulp.LpProblem('Il piano di studi', pulp.const.LpMaximize)
    x = pulp.LpVariable.dicts('corso_anno', (COURSES, YEARS, GROUPS), lowBound=0, upBound=1, cat='Continuous')  # creazione variabili

    # FUNZIONE OBIETTIVO
    prob += (
        pulp.lpSum([
            rating[i] * cfus[i] * (x[i][j][k]) for (i, j, k) in product(COURSES, YEARS, GROUPS)
        ])
    )

    # VINCOLI
    # for i in MANDATORY_COURSES:
    #     prob += x[i][1] == 1, "Compulsory 1" # ah merda in quale anno è fatto...

    if MST:
        prob += x[153][1] == 1, "Compulsory 1"
        prob += x[154][1] == 1, "Compulsory 2"
        prob += x[155][1] == 1, "Compulsory 3"
        prob += x[156][1] == 1, "Compulsory 4"
        prob += x[157][1] == 1, "Compulsory 5"
        prob += x[158][2] == 1, "Compulsory 6"
        prob += x[159][2] == 1, "Compulsory 7"

    # corso scelto al massimo una sola volta
    for i in COURSES:
        prob += pulp.lpSum([x[i][j][k] for (j, k) in product(YEARS, GROUPS)] <= 1, ("Corso " + str(i) + " scelto una sola volta")


    # immagino di avere un parametro bidimensionale a[i,k] = 1 se corso i è nel gruppo k



    # se i nomi sono uguali puoi sceglierlo solo una volta
    for i in COURSES:
        for k in COURSES:
            if (i != k) and (names[i] == names[k]):
                # print("I corsi uguali sono " + str(i) + " " + str(k) + " " + names[i])
                prob += x[i][1] + x[i][2] + x[k][1] + x[k][2] <= 1, ''

    # max cfu per semestre per anno
    for j in YEARS:
        group_courses=[i for i in COURSES if semester[i] == 1]
        prob += pulp.lpSum(
            [cfus[i]*x[i][j] for i in group_courses]) <= CFU_max_sem, ("Max cfu sem 1 anno " + str(j))

        group_courses=[i for i in COURSES if semester[i] == 2]
        prob += pulp.lpSum(
            [cfus[i]*x[i][j] for i in group_courses]) <= CFU_max_sem, ("Max cfu sem 2 anno " + str(j))

    # min cfu gruppo
    for k in GROUPS:
        group_courses=[i for i in COURSES if group_dic[i] == k]
        group_combos=[(i, j) for i in group_courses for j in YEARS]
        prob += pulp.lpSum(
            [cfus[i]*x[i][j] for (i, j) in group_combos]) == min_cfus[k], ("Min cfu gruppo " + str(k))  # >=

    prob += pulp.lpSum(
        [cfus[i]*x[i][j] for (i, j) in product(COURSES, YEARS, GROUPS)]) <= CFU_max_tot, "Max cfu totali"

    # RISOLUZIONE
    prob.solve()

    corsi=[]
    for (i, j) in product(COURSES, YEARS):
        if sum[x[i][j][k].varValue for k in GROUPS] == 1.0:
            course_name=names[i]
            semester_name=semester[i]
            cfus_name=cfus[i]
            codes_name=codes[i]
            group_name=group_full[i]
            group_id=group_dic[i]
            el=[codes_name, course_name, cfus_name, group_name, group_id, j, semester_name]
            corsi.append(el)
            # print("Svolgerai il corso " + str(i) + " " + course_name + " al sem " + str(semester_name) + " all'anno " + str(j))

    piano=pd.DataFrame(corsi, columns=['Codice', 'Denominazione', 'CFU', 'Gruppo', 'idgruppo', 'Anno', 'Sem'])
    piano=piano.set_index('Codice')
    piano=piano.drop(columns=['idgruppo'])
    piano=piano.sort_values(['Anno', 'Sem'], ascending=[TRUE, TRUE])

    return piano
