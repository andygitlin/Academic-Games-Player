import copy

wff_length_bound = 10

class WFF:

    def __init__(self, connector, left, right):
        self.connector = connector
        self.left = left
        self.right = right
        self.str = None

    def __str__(self):
        if not self.connector:
            raise ValueError
        if not self.str:
            self.str = self.connector + str(self.left) + str(self.right)
        return self.str

class Base_WFF(WFF):

    def __init__(self, left):
        self.connector = ''
        self.left = left
        self.right = ''
        self.str = self.left

    def __str__(self):
        return self.left

def read_in_wff(wff_str):
    if len(wff_str) == 0:
        raise ValueError
    if wff_str[0].islower():
        return Base_WFF(wff_str[0])
    connector = wff_str[0]
    wff_str_1 = wff_str[1:]
    left = read_in_wff(wff_str_1)
    wff_str_2 = wff_str_1[len(str(left)):]
    right = read_in_wff(wff_str_2)
    return WFF(connector,left,right)

class WFF_Info:

    def __init__(self, parents, rule):
        self.parents = parents
        self.rule = rule
        self.line = None

    def set_line(self, line):
        self.line = line

nice_a_wffs = []
WFF_Dict = {}
current_line = 1

def print_line(wff,repeat=False):
    wff_info = WFF_Dict[wff]
    parents_list = [str(WFF_Dict[p].line) for p in wff_info.parents]
    if repeat:
        parents_list = [parents_list[0],str(current_line-1)]
    parent_lines = ', '.join(parents_list)
    q = "{0:<2}) | {1:<12} {2:>10} {3}".format(wff_info.line, str(wff), wff_info.rule, parent_lines)
    print(q)

def print_proof(wff):
    global current_line
    parents_list = WFF_Dict[wff].parents
    repeat = False
    for p in parents_list:
        if not WFF_Dict[p].line:
            print_proof(p)
    if len(parents_list) == 2:
        if parents_list[0] == parents_list[1]:
            repeat = True
            p = parents_list[0]
            q = "{0:<2}) | {1:<12} {2:>10} {3}".format(current_line, str(p), "Rp", WFF_Dict[p].line)
            print(q)
            current_line += 1
    WFF_Dict[wff].set_line(current_line)
    print_line(wff,repeat)
    current_line += 1

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
    for i in range(len(new_keys)):
        s = str(new_keys[i])
        global wff_length_bound
        if len(s) < wff_length_bound and str(new_keys[i]) not in L:
            WFF_Dict[new_keys[i]] = new_values[i]

def add_nice_a_wffs(wff):
    if wff.connector == 'A':
        nice_a_wffs.append(wff)
    if wff.connector:
        add_nice_a_wffs(wff.left)
        add_nice_a_wffs(wff.right)

def update_nice_a_wffs():
    for wff in WFF_Dict.keys():
        add_nice_a_wffs(wff)
                            
def look_for_proof(start_wffs,end_wff):
    start(start_wffs)
    end = read_in_wff(end_wff)
    add_nice_a_wffs(end)
    L = WFF_Dict.keys()
    while str(end) not in [str(l) for l in L]:
        current_wffs = [k for k in WFF_Dict.keys()]
        for wff in current_wffs:
            apply_rules(wff)
        for i in range(len(current_wffs)):
            for j in range(i,len(current_wffs)):
                apply_rules(current_wffs[i],current_wffs[j])
        update_nice_a_wffs()
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

##### test cases

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
    #look_for_proof(['p'],'Kpp')
    #look_for_proof(['Cqp','q'],'Kpp')
    look_for_proof(['Kqs','Krp'],'KKssr')

def test7():
    #look_for_proof(['Ksr'],'KrAsp')
    look_for_proof(['EAsrp','s'],'KAsqKpp')

##### main

if __name__ == '__main__':
    test7()

