from pulp import *
import pandas as pd
from tkinter import filedialog as fd
from tkinter import *

def genera_piano(df, CFU_max_sem=35, CFU_max_tot=122, MST=TRUE):

    df = df.dropna()
    dict_base = df.to_dict()

    # GENERAZIONE DIZIONARI PARAMETRI
    names = dict_base['Denominazione']
    codes = dict_base['Codice']
    semester = dict_base['Sem']
    cfus = dict_base['CFU']
    group_full = dict_base['Gruppo']
    group_dic = dict_base['Gruppo_id']
    rating = dict_base['Rating']

    Courses = list(names.keys())
    Years = [1, 2]
    combos = [(i, j) for i in Courses for j in Years]

    Groups = [0, 1, 2, 3, 4, 5]
    min_cfus = [10, 16, 10, 16, 0, 0]

    ### PROBLEM
    prob = LpProblem('Il piano di studi', LpMaximize)
    courses_vars = pulp.LpVariable.dicts('corso_anno', (Courses, Years), lowBound = 0, upBound = 1, cat = 'Binary')  # creazione variabili

    prob += (
        pulp.lpSum(
            [
                rating[i] * cfus[i] * (courses_vars[i][j])  # funzione obiettivo
                for (i, j) in combos
            ]
        )
    )

    ### VINCOLI
    if MST:
        prob += courses_vars[153][1] == 1, "Compulsory 1"
        prob += courses_vars[154][1] == 1, "Compulsory 2"
        prob += courses_vars[155][1] == 1, "Compulsory 3"
        prob += courses_vars[156][1] == 1, "Compulsory 4"
        prob += courses_vars[157][1] == 1, "Compulsory 5"
        prob += courses_vars[158][2] == 1, "Compulsory 6"
        prob += courses_vars[159][2] == 1, "Compulsory 7"

    for i in Courses:
        prob += pulp.lpSum(
            [courses_vars[i][j] for j in Years]) <= 1, ("Corso " + str(i) + " scelto una sola volta")

    for i in Courses:
        for k in Courses:
            if (i != k) and (names[i] == names[k]):
                #print("I corsi uguali sono " + str(i) + " " + str(k) + " " + names[i])
                prob += courses_vars[i][1] + courses_vars[i][2] + courses_vars[k][1] + courses_vars[k][2] <= 1, ''

    for j in Years:
        group_courses = [i for i in Courses if semester[i] == 1]
        prob += pulp.lpSum(
            [cfus[i]*courses_vars[i][j] for i in group_courses]) <= CFU_max_sem, ("Max cfu sem 1 anno " + str(j))

        group_courses = [i for i in Courses if semester[i] == 2]
        prob += pulp.lpSum(
            [cfus[i]*courses_vars[i][j] for i in group_courses]) <= CFU_max_sem, ("Max cfu sem 2 anno " + str(j))

    for k in range(0, 4):  #in Groups
        group_courses = [i for i in Courses if group_dic[i] == k]
        group_combos = [(i, j) for i in group_courses for j in Years]
        prob += pulp.lpSum(
            [cfus[i]*courses_vars[i][j] for (i,j) in group_combos]) == min_cfus[k], ("Min cfu gruppo " + str(k)) ##>=

    prob += pulp.lpSum(
        [cfus[i]*courses_vars[i][j] for (i,j) in combos]) <= CFU_max_tot, "Max cfu totali"

    ### RISOLUZIONE
    prob.solve()

    corsi = []
    for (i,j) in combos:
        if courses_vars[i][j].varValue == 1.0:
            course_name = names[i]
            semester_name = semester[i]
            cfus_name = cfus[i]
            codes_name = codes[i]
            group_name = group_full[i]
            group_id = group_dic[i]
            el = [codes_name, course_name, cfus_name, group_name, group_id, j, semester_name]
            corsi.append(el)
            #print("Svolgerai il corso " + str(i) + " " + course_name + " al sem " + str(semester_name) + " all'anno " + str(j))

    piano = pd.DataFrame(corsi, columns = ['Codice', 'Denominazione', 'CFU', 'Gruppo', 'idgruppo', 'Anno', 'Sem'])
    piano = piano.set_index('Codice')
    piano = piano.drop(columns=['idgruppo'])
    piano = piano.sort_values(['Anno','Sem'], ascending = [TRUE, TRUE])
    
    return piano