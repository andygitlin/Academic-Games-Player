import copy
import time

# redirect print
from io import StringIO
import sys

# website stuff
from flask import Flask, request, render_template, redirect, url_for, flash, Blueprint
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import Required
import re


wff_length_bound = 10

def wff_length(wff_str):
    counter = 0
    for i in range(len(wff_str)):
        if wff_str[i] != 'N':
            counter += 1
    return counter

class WFF:

    def __init__(self, connector, left, right):
        self.connector = connector
        self.left = left
        self.right = right
        self.str = None
        self.len  = None

    def __str__(self):
        if not self.connector:
            raise ValueError
        if not self.str:
            self.str = self.connector + str(self.left) + str(self.right)
        return self.str

    def __len__(self):
        if not self.connector:
            raise ValueError
        if not self.len:
            self.len = 1 + len(self.left) + len(self.right)
        return self.len

class Base_WFF(WFF):

    def __init__(self, left):
        self.connector = ''
        self.left = left
        self.right = ''

    def __str__(self):
        return self.connector + self.left

    def __len__(self):
        return 1

def read_in_wff(wff_str):
    if len(wff_str) == 0:
        raise ValueError
    if wff_str[0].islower():
        return Base_WFF(wff_str[0])
    connector = wff_str[0]
    wff_str_1 = wff_str[1:]
    if connector == 'N':
        read_wff = read_in_wff(wff_str_1)
        read_wff.connector = 'N' + read_wff.connector
        return read_wff
    left = read_in_wff(wff_str_1)
    wff_str_2 = wff_str_1[len(str(left)):]
    right = read_in_wff(wff_str_2)
    return WFF(connector,left,right)

class WFF_Info:

    def __init__(self, parents, rule):
        self.parents = parents
        self.rule = rule
        self.line = None
        self.parent_lines = None

    def set_line(self, line):
        self.line = line

    def set_parent_lines(self, parent_lines):
        self.parent_lines = parent_lines

nice_a_wffs = []
WFF_Dict = {}
current_line = 1

def print_line(wff):
    global current_line
    wff_info = WFF_Dict[wff]
    parents_list = [str(WFF_Dict[p].line) for p in wff_info.parents]
    rule = wff_info.rule
    if not wff_info.line:
        wff_info.line = current_line
    elif rule == 's':
        rule = "Rp"
        parents_list = [str(wff_info.line)]
    if len(parents_list) == 2 and parents_list[0] == parents_list[1]:
        parents_list[1] = str(current_line-1)
    if not wff_info.parent_lines:
        parent_lines = ', '.join(parents_list)
        wff_info.set_parent_lines(parent_lines)
    q = "{0:<2}) | {1:<12} {2:>10} {3}".format(current_line, str(wff), rule, wff_info.parent_lines)
    print(q)
    current_line += 1

def print_proof(wff):
    global current_line
    parents_list = WFF_Dict[wff].parents
    if len(parents_list) == 2 and parents_list[0] == parents_list[1]:
        if WFF_Dict[parents_list[0]].line is None:
            print_proof(parents_list[0])
        print_line(parents_list[0])
    else:
        for i in range(len(parents_list)):
            if WFF_Dict[parents_list[i]].line is None:
                print_proof(parents_list[i])
    print_line(wff)

def start(start_wffs):
    for wff in start_wffs:
        WFF_Dict[read_in_wff(wff)] = WFF_Info([],'s')

def apply_rules(wff1,wff2=None):
    new_keys = []
    new_values = []
    if wff2:
        # Ki
        new_keys.append(WFF('K',wff1,wff2))
        new_values.append(WFF_Info([wff1,wff2],'Ki'))
        new_keys.append(WFF('K',wff2,wff1))
        new_values.append(WFF_Info([wff2,wff1],'Ki'))
        # Co
        if wff1.connector == 'C' and str(wff1.left) == str(wff2):
            new_keys.append(wff1.right)
            new_values.append(WFF_Info([wff1,wff2],'Co'))
        if wff2.connector == 'C' and str(wff2.left) == str(wff1):
            new_keys.append(wff2.right)
            new_values.append(WFF_Info([wff2,wff1],'Co'))
        # Ei
        if wff1.connector == 'C' and wff2.connector == 'C':
            if str(wff1.left) == str(wff2.right) and str(wff1.right) == str(wff2.left):
                new_keys.append(WFF('E',wff1.left,wff1.right))
                new_values.append(WFF_Info([wff1,wff2],'Ei'))
                new_keys.append(WFF('E',wff1.right,wff1.left))
                new_values.append(WFF_Info([wff2,wff1],'Ei'))
    else:
        # Ko
        if wff1.connector == 'K':
            new_keys.append(wff1.left)
            new_values.append(WFF_Info([wff1],'Ko'))
            new_keys.append(wff1.right)
            new_values.append(WFF_Info([wff1],'Ko'))
        # Eo
        if wff1.connector == 'E':
            new_keys.append(WFF('C',wff1.left,wff1.right))
            new_values.append(WFF_Info([wff1],'Eo'))
            new_keys.append(WFF('C',wff1.right,wff1.left))
            new_values.append(WFF_Info([wff1],'Eo'))
        # Ai
        for i in range(len(nice_a_wffs)-1,-1,-1):
            a_wff = nice_a_wffs[i]
            if str(a_wff.left) == str(wff1) or str(a_wff.right) == str(wff1):
                new_keys.append(a_wff)
                new_values.append(WFF_Info([wff1],'Ai'))
                nice_a_wffs.pop(i)
    L = [str(k) for k in WFF_Dict.keys()]
    global wff_length_bound
    for i in range(len(new_keys)):
        if len(new_keys[i]) < wff_length_bound and str(new_keys[i]) not in L:
            WFF_Dict[new_keys[i]] = new_values[i]
            if new_keys[i].connector != 'A':
                add_nice_a_wffs(new_keys[i])

def add_nice_a_wffs(wff,end=False):
    if isinstance(wff,WFF):
        if end:
            if wff.connector == 'A':
                nice_a_wffs.append(wff)
                add_nice_a_wffs(wff.left,True)
                add_nice_a_wffs(wff.right,True)
            elif wff.connector == 'K':
                add_nice_a_wffs(wff.left,True)
                add_nice_a_wffs(wff.right,True)
        if not end:
            if wff.connector == 'C':
                add_nice_a_wffs(wff.left,True)
            elif wff.connector == 'E':
                add_nice_a_wffs(wff.left,True)
                add_nice_a_wffs(wff.right,True)
                            
def look_for_proof(start_wffs,end_wff):
    start(start_wffs)
    end = read_in_wff(end_wff)
    add_nice_a_wffs(end,True)
    L = WFF_Dict.keys()
    while str(end) not in [str(l) for l in L]:
        current_wffs = [k for k in WFF_Dict.keys()]
        for wff in current_wffs:
            apply_rules(wff)
        for i in range(len(current_wffs)):
            for j in range(i,len(current_wffs)):
                apply_rules(current_wffs[i],current_wffs[j])
        L = WFF_Dict.keys()
    print("    | {0} -> {1}".format(', '.join(start_wffs),str(end_wff)))
    print('-----------------------------------')
    for k in WFF_Dict.keys():
        if WFF_Dict[k].rule == 's':
            print_proof(k)
    print('----------')
    wff = None
    for k in WFF_Dict.keys():
        if str(k) == str(end_wff):
            wff = k
            break
    print_proof(wff)


################################################## website stuff

wff_blueprint = Blueprint('wff', __name__, template_folder="templates")

class WffForm(FlaskForm):
    premises = StringField("Premises (separate with comma):")
    conclusion = StringField("Conclusion:")
    submit = SubmitField()

@wff_blueprint.route('/MrWff', methods = ['GET', 'POST'])
def wff():
    form = WffForm()
    if request.method == 'POST':
        start_wff = list(re.split(r", *", form.premises.data)) if form.premises.data else []
        end_wff = form.conclusion.data
        
        # code adapted from https://stackoverflow.com/questions/1218933/can-i-redirect-the-stdout-in-python-into-some-sort-of-string-buffer
        old_stdout = sys.stdout
        sys.stdout = mystdout = StringIO()
        look_for_proof(start_wff, end_wff)
        sys.stdout = old_stdout
        solution = mystdout.getvalue()

        return render_template('WffResult.html', solution=solution)
    return render_template('MrWff.html', form=form)

##### test cases

def reset_all():
    global nice_a_wffs, WFF_Dict, current_line
    nice_a_wffs = []
    WFF_Dict = {}
    current_line = 1

def test1():
    wff = WFF('C',Base_WFF('r'),Base_WFF('p'))
    wff_info = WFF_Info([], 's')
    wff_info.set_line(1)
    WFF_Dict[wff] = wff_info
    print_line(wff)

def test2():
    wff1 = Base_WFF('p')
    wff1_info = WFF_Info([], 's')
    wff2 = Base_WFF('q')
    wff2_info = WFF_Info([], 's')
    wff3 = WFF('K',wff1,wff2)
    wff3_info = WFF_Info([wff1,wff2],'Ki')
    WFF_Dict[wff1] = wff1_info
    WFF_Dict[wff2] = wff2_info
    WFF_Dict[wff3] = wff3_info
    print_proof(wff3)

def test3():
    start(['Kpr','KCprKqq'])
    for wff in WFF_Dict.keys():
        print(wff)

def test4():
    look_for_proof(['Kqs','Krp'],'Ksr')

def test5():
    #look_for_proof(['Eqp','q', 'r'],'Kpr')
    look_for_proof(['Eqp','q','r'],'KCpqKpr')

def test6():
    look_for_proof(['p'],'Kpp')
    #look_for_proof(['Cqp','q'],'Kpp')
    #look_for_proof(['Kqs','Krp'],'KKssr')

def test7():
    #look_for_proof(['Ksr'],'KrAsp')
    look_for_proof(['EAsrp','s'],'KAsqKpp')

def test_nick_wang():
    look_for_proof(['EKrps','Kpr'],'KAqpKrs')

def test8():
    #look_for_proof(['Nr','NNs','NNKNrp'],'KNNKNrpKNrNNs')
    look_for_proof(['Nr'],'KKNrNrKNrNr')

def test9():
    look_for_proof(['p'],'p')
    #look_for_proof(['Cpp'],'Epp')

def test10():
    look_for_proof(['p','q'],'KKppKqq')

##### main

# if __name__ == '__main__':
#     for test in [test9,test4,test6,test7,test8,test5,test_nick_wang]:
#         start_time = time.time()
#         test()
#         reset_all()
#         end_time = time.time()
#         print(end_time-start_time)

