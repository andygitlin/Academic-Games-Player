import copy
import time
import itertools
from MrBasicWff import *

##### printing

print_option = True
output_string = ""

def printer(str):
    global print_option
    if print_option:
        print(str)
    else:
        output_string = output_string + str + '\n'

##### determining whether or not proof is possible (in Regular WFF)

def base_wffs_mega_wff(start_wffs,end_wff,printer=False):
    global current_line
    line = current_line
    wff_str = str(end_wff)
    if len(start_wffs) != 0:
        wff_str = str(start_wffs[0]) + wff_str
        for i in range(1,len(start_wffs)):
            wff_str = 'K' + str(start_wffs[i]) + wff_str
        wff_str = 'C' + wff_str
    wff = read_in_wff(wff_str)
    return [list(set([c for c in str(wff_str) if c.islower()])), wff]

def proof_possible(start_wffs,end_wff):
    base_wffs, mega_wff = base_wffs_mega_wff(start_wffs,end_wff)
    for n in range(len(base_wffs)+1):
        for true_wffs in itertools.combinations(base_wffs,n):
            if not wff_truth(mega_wff,true_wffs):
                return False
    return True

def wff_truth(wff, true_wffs):
    if len(wff.connector) > 0 and wff.connector[0] == 'N':
        new_wff = copy.copy(wff)
        new_wff.connector = new_wff.connector[1:]
        return (not wff_truth(new_wff, true_wffs))
    if isinstance(wff,Base_WFF):
        return (str(wff.left) in true_wffs)
    if not wff.connector:
        raise ValueError
    connector = wff.connector
    left_truth = wff_truth(wff.left, true_wffs)
    right_truth = wff_truth(wff.right, true_wffs)
    if connector == 'C':
        return ((not left_truth) or right_truth)
    elif connector == 'A':
        return (left_truth or right_truth)
    elif connector == 'K':
        return (left_truth and right_truth)
    elif connector == 'E':
        return (left_truth == right_truth)
    raise ValueError

##### prove wff

def prove_wff(wff, base_wffs, true_base_wffs):
    if not wff_truth(wff, true_base_wffs):
        raise ValueError
    global current_line, indentation, pNp_lines
    if isinstance(wff, Base_WFF) and len(wff.connector) < 2:
        Np = "N" + str(wff)
        print_indented_line(indentation+1, Np, 's')
        print_indented_underline(indentation+1)
        line = pNp_lines[base_wffs.index(wff.left)]
        print_indented_line(indentation+1, wff, "R", [line])
        print_indented_line(indentation+1, Np, "Rp", [current_line-2])
        print_indented_line(indentation, wff, "No", [current_line-3])
        return
    if not wff.connector:
        raise ValueError
    if len(wff.connector) >= 2:
        if wff.connector[0] == 'N' and wff.connector[1] == 'N':
            p = copy.copy(wff)
            p.connector = p.connector[2:]
            Np = "N" + str(p)
            prove_wff(p, base_wffs, true_base_wffs)
            print_indented_line(indentation+1, Np, 's')
            print_indented_underline(indentation+1)
            print_indented_line(indentation+1, p, "R", [current_line-2])
            print_indented_line(indentation+1, Np, "Rp", [current_line-2])
            print_indented_line(indentation, wff, "Ni", [current_line-3])
            return
    connector = wff.connector[-1]
    left_truth = wff_truth(wff.left, true_base_wffs)
    right_truth = wff_truth(wff.right, true_base_wffs)
    if connector == 'C':
        if right_truth:
            prove_wff(wff.right, base_wffs, true_base_wffs)
            print_indented_line(indentation+1, wff.left, 's')
            print_indented_underline(indentation+1)
            print_indented_line(indentation+1, wff.right, "R", [current_line-2])
            print_indented_line(indentation, wff, "Ci", [current_line-2])
            return
        if left_truth:
            prove_wff(wff.left, base_wffs, true_base_wffs)
            line1 = current_line - 1
            Nq = copy.copy(wff.right)
            Nq.connector = 'N' + Nq.connector
            prove_wff(Nq, base_wffs, true_base_wffs)
            line2 = current_line - 1
            print_indented_line(indentation+1, "C{0}{1}".format(wff.left,wff.right), 's')
            print_indented_underline(indentation+1)
            print_indented_line(indentation+1, wff.left, "R", [line1])
            print_indented_line(indentation+1, wff.right, "Co", [current_line-1,current_line-2])
            print_indented_line(indentation+1, Nq, "R", [line2])
            print_indented_line(indentation, wff, "Ni", [current_line-4])
            return
        Np = copy.copy(wff.left)
        Np.connector = 'N' + Np.connector
        prove_wff(Np, base_wffs, true_base_wffs)
        print_indented_line(indentation+1, wff.left, 's')
        print_indented_underline(indentation+1)
        print_indented_line(indentation+2, "N" + str(wff.right), 's')
        print_indented_underline(indentation+2)
        print_indented_line(indentation+2, Np, "R", [current_line-3])
        print_indented_line(indentation+2, wff.left, "R", [current_line-3])
        print_indented_line(indentation+1, wff.right, "No", [current_line-3])
        print_indented_line(indentation, wff, "Ci", [current_line-5])
        return
    elif connector == 'A':
        if left_truth or right_truth:
            prove_wff(wff.left if left_truth else wff.right, base_wffs, true_base_wffs)
            print_indented_line(indentation, wff, "Ai", [current_line-1])
            return
        Np = copy.copy(wff.left)
        Np.connector = 'N' + Np.connector
        Nq = copy.copy(wff.right)
        Nq.connector = 'N' + Np.connector
        prove_wff(Np, base_wffs, true_base_wffs)
        line1 = current_line - 1
        prove_wff(Nq, base_wffs, true_base_wffs)
        line2 = current_line - 1
        Apq = "A{0}{1}".format(wff.left,wff.right)
        print_indented_line(indentation+1, Apq, 's')
        print_indented_underline(indentation+1)
        print_indented_line(indentation+2, wff.left, 's')
        print_indented_underline(indentation+2)
        print_indented_line(indentation+3, Nq, 's')
        print_indented_underline(indentation+3)
        print_indented_line(indentation+3, Np, "R", [line1])
        print_indented_line(indentation+3, wff.left, "R", [current_line-3])
        print_indented_line(indentation+2, wff.right, "No", [current_line-3])
        print_indented_line(indentation+2, wff.right, 's')
        print_indented_underline(indentation+2)
        print_indented_line(indentation+2, wff.right, "Rp", [current_line-1])
        print_indented_line(indentation+1, wff.right, "Ao", [current_line-8,current_line-7,current_line-2])
        print_indented_line(indentation+1, Nq, "R", [line2])
        print_indented_line(indentation, wff, "Ni", [current_line-10])
        return
    elif connector == 'K':
        if left_truth and right_truth:
            prove_wff(wff.left, base_wffs, true_base_wffs)
            line1 = current_line - 1
            prove_wff(wff.right, base_wffs, true_base_wffs)
            line2 = current_line - 2
            print_indented_line(indentation, wff, "Ki", [line1,line2])
            return
        r = wff.left if not left_truth else wff.right
        Nr = copy.copy(r)
        Nr.connector = 'N' + Nr.connector
        prove_wff(Nr, base_wffs, true_base_wffs)
        print_indented_line(indentation+1, str(wff)[1:], 's')
        print_indented_underline(indentation+1)
        print_indented_line(indentation+1, Nr, "R", [current_line-2])
        print_indented_line(indentation+1, r, "Ko", [current_line-2])
        print_indented_line(indentation, wff, "Ni", [current_line-3])
        return
    elif connector == 'E':
        if left_truth == right_truth:
            C_wff_1 = WFF('C', wff.left, wff.right)
            prove_wff(C_wff_1, base_wffs, true_base_wffs)
            line1 = current_line - 1
            C_wff_2 = WFF('C', wff.right, wff.left)
            prove_wff(C_wff_2, base_wffs, true_base_wffs)
            line2 = current_line - 1
            print_indented_line(indentation, wff, "Ei", [line1,line2])
            return
        r = wff.left if left_truth else wff.right
        s = wff.right if left_truth else wff.left
        NCrs = WFF("NC",r,s)
        prove_wff(NCrs, base_wffs, true_base_wffs)
        print_indented_line(indentation+1, str(wff)[1:], 's')
        print_indented_underline(indentation+1)
        print_indented_line(indentation+1, NCrs, "R", [current_line-2])
        print_indented_line(indentation+1, str(NCrs)[1:], "Eo", [current_line-2])
        print_indented_line(indentation, wff, "Ni", [current_line-3])
        return
    raise ValueError

##### print proof

indentation = 0
ApNp_lines = []
pNp_lines = []

def print_indented_line(indents, wff, rule, parent_lines = []):
    global current_line, rules_used
    rules_parents = rule + ' ' + ', '.join([str(i) for i in parent_lines])
    printer("{0:<4}|{4}{1:<30} {2:>40} {3}".format(current_line, str(wff), '', rules_parents, "\t |"*indents))
    current_line += 1
    if rule != 's' and rule not in rules_used:
        rules_used.append(rule)

def print_indented_underline(indents):
    printer("{0:<4} {1}----------".format('',"\t "*indents))

def prove_ApNp(p):
    global current_line
    line = current_line
    Np = "N{0}".format(p)
    ApNp = "A{0}N{0}".format(p)
    NApNp = "NA{0}N{0}".format(p)
    print_indented_line(1, NApNp, 's')
    print_indented_underline(1)
    print_indented_line(2, p, 's')
    print_indented_underline(2)
    print_indented_line(2, ApNp, "Ai", [line+1])
    print_indented_line(2, NApNp, "R", [line])
    print_indented_line(1, Np, "Ni", [line+1])
    print_indented_line(1, ApNp, "Ai", [line+4])
    print_indented_line(1, NApNp, "Rp", [line])
    print_indented_line(0, ApNp, "No", [line])
    return current_line - 1

def prove_mega_wff(mega_wff, base_wffs, true_base_wffs, base_wff_index):
    global indentation, current_line
    if base_wff_index == len(base_wffs):
        prove_wff(mega_wff, base_wffs, true_base_wffs)
        return
    indentation += 1
    # proof if base_wffs[base_wff_index] is True
    line1 = current_line
    pNp_lines[base_wff_index] = line1
    print_indented_line(indentation, base_wffs[base_wff_index], 's')
    print_indented_underline(indentation)
    TBW = copy.copy(true_base_wffs)
    TBW.append(base_wffs[base_wff_index])
    prove_mega_wff(mega_wff, base_wffs, TBW, base_wff_index+1)
    # proof if base_wffs[base_wff_index] is False
    line2 = current_line
    pNp_lines[base_wff_index] = line2
    print_indented_line(indentation, "N"+base_wffs[base_wff_index], 's')
    print_indented_underline(indentation)
    prove_mega_wff(mega_wff, base_wffs, true_base_wffs, base_wff_index+1)
    # final touches
    indentation -= 1
    if base_wff_index != 0:
        line3 = current_line
        ApNp = "A{0}N{0}".format(base_wffs[base_wff_index])
        print_indented_line(indentation, ApNp, "R", [ApNp_lines[base_wff_index]])
        print_indented_line(indentation, mega_wff, "Ao", [line1,line2,line3])
    else:
        print_indented_line(indentation, mega_wff, "Ao", [line1,line2,ApNp_lines[0]])

def prove_finish(start_wffs, end_wff):
    if len(start_wffs) == 0:
        return
    mega_wff_line = current_line - 1
    wff_str = str(start_wffs[0])
    line  = 1
    for i in range(1,len(start_wffs)):
        wff_str = 'K' + str(start_wffs[i]) + wff_str
        print_indented_line(0, wff_str, "Ki", [i+1, line])
        line = current_line - 1
    print_indented_line(0, end_wff, "Co", [mega_wff_line, line])

def print_proof(start_wffs,end_wff):
    global ApNp_lines, pNp_lines
    if not proof_possible(start_wffs, end_wff):
        printer("proof is not possible")
        return
    base_wffs, mega_wff = base_wffs_mega_wff(start_wffs,end_wff)
    pNp_lines = [-1 for i in range(len(base_wffs))]
    printer("    | {0} -> {1}".format(', '.join(start_wffs),str(end_wff)))
    printer('-----------------------------------'*3)
    for s_wff in start_wffs:
        print_indented_line(0, str(s_wff), 's')
    if len(start_wffs) != 0:
        printer('----------')
    # ApNp
    ApNp_lines = [prove_ApNp(p) for p in base_wffs]
    # recursion
    prove_mega_wff(mega_wff, base_wffs, [], 0)
    # final touches
    prove_finish(start_wffs,end_wff)
    printer(', '.join(start_wffs) + ' / ' + ', '.join(rules_used))

def REGULAR_get_proof_string(start_wffs,end_wff):
    global print_option, output_string
    print_option = False
    print_proof(start_wffs,end_wff)
    return output_string

##### tests

def RESET_ALL():
    global current_line, indentation, ApNp_lines, pNp_lines
    current_line = 1
    indentation = 0
    ApNp_lines = []
    pNp_lines = []

def TEST1():
    print(proof_possible(['EKrps','Kpr'],'s'))
    print(proof_possible(['EAsrp','s'],'KAsqKpp'))
    print(proof_possible(['Np','Kqs'],'KqNr'))
    print(proof_possible(['Np'],'NNNp'))

def TEST2():
    print_proof(['EKrps','Kpr','Nq'],'s')
    RESET_ALL()

def TEST3():
    print_proof(['p'],'p')
    RESET_ALL()
    print_proof(['Np'],'Np')
    RESET_ALL()
    print_proof(['p'],'NNp')
    RESET_ALL()
    print_proof(['Np'],'NNNp')
    RESET_ALL()
    print_proof([],'ApNp')
    RESET_ALL()

def TEST4():
    print_proof(['EKrps','Kpr'],'s')
    RESET_ALL()
    print_proof(['EAsrp','s'],'KAsqKpp')
    RESET_ALL()
    print_proof(['Np','Kqs'],'KqNr')
    RESET_ALL()
    print_proof(['Np'],'NNNp')
    RESET_ALL()

##### main

if __name__ == '__main__':
    TEST2()
    TEST3()
    TEST4()
