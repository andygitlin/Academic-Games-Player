import numpy as np
import itertools

'''
following represents (RuG)n(Yu(BuV))
nums = ["R","G","Y","B","V"]
ops = ['u','n','u','u']
ooo = [0,2,1,0]
'''

'''
    -   B   BR  R
-   0   1   2   3
G   4   5   6   7
GY  8   9   10  11
Y   12  13  14  15
'''

CARDS = [1,1,0,1,
         0,1,1,0,
         1,0,1,0,
         0,1,0,0]

# MOP_PERMITTED = False
# if True, allows each operation in ops to be used any number of times (including zero times)
# if False, every operation in ops is used exactly once (so len(ops) must equal len(nums)-1)

SETS = dict()
SETS["V"] = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]
SETS["∏"] = []
SETS["B"] = [1,2,5,6,9,10,13,14]
SETS["R"] = [2,3,6,7,10,11,14,15]
SETS["G"] = [4,5,6,7,8,9,10,11]
SETS["Y"]= [12,13,14,15]

OPS = dict()
OPS["u"] = lambda a,b : list(set(a) | set(b))
OPS["n"] = lambda a,b : list(set(a) & set(b))
OPS["-"] = lambda a,b : list(set(a) - set(b))
OPS["'"] = lambda b : OPS["-"](SETS["V"],b)
OPS["∆"] = lambda a,b : OPS["u"](OPS["-"](a,b),OPS["-"](b,a))

def apply(nums):
    def primal(L,n):
        if n == 0:
            return L
        return primal(OPS["'"](L),n-1)
    return [primal(SETS[nums[i][0]],len(nums[i])-1) for i in range(len(nums))]

def eval(nums, ops, ooo):
    def primal(f,n):
        if n == 0:
            return f
        return lambda a,b : OPS["'"](primal(f,n-1)(a,b))
    if len(ooo) == 0:
        return nums[0]
    new_nums = [i for i in nums]
    new_ops = [i for i in ops]
    new_ooo = [i for i in ooo]
    new_nums[ooo[0]] = primal(OPS[ops[ooo[0]][0]],len(ops[ooo[0]])-1)(nums[ooo[0]],nums[ooo[0]+1])
    new_nums.pop(ooo[0]+1)
    new_ops.pop(ooo[0])
    new_ooo.pop(0)
    return eval(new_nums, new_ops, new_ooo)

def evalint(nums, ops, ooo):
    L = eval(nums, ops, ooo)
    return sum([CARDS[i] for i in L])

def printer(nums, ops, ooo):
    new_nums = [nums[i] for i in range(len(nums))]
    new_ops = [i for i in ops]
    new_ooo = [i for i in ooo]
    while len(new_nums) > 1:
        if len(new_nums) != 2 or len(new_ops[new_ooo[0]]) != 1:
            new_nums[new_ooo[0]] = '(' + new_nums[new_ooo[0]] + new_ops[new_ooo[0]][0] + new_nums[new_ooo[0]+1] + ')' + ("'" * (len(new_ops[new_ooo[0]])-1))
        else:
            new_nums[new_ooo[0]] = new_nums[new_ooo[0]] + new_ops[new_ooo[0]] + new_nums[new_ooo[0]+1]
        new_nums.pop(new_ooo[0]+1)
        new_ops.pop(new_ooo[0])
        new_ooo.pop(0)
    return new_nums[0]

def primage(S,primes):
    L = [s for s in S]
    for p in primes:
        L[p] += "'"
    return L

def try_all(nums_ = ['R','B','G','∏'], ops_ = ['u','n','-',"'","'"], run = [1]):
    n = len(nums_)
    new_run = [i for i in run]
    all_nums = [list(x) for x in list(itertools.permutations(nums_))]
    unprimed_ops = [x for x in ops_ if x != "'"]
    all_ops = [list(x) for x in list(itertools.permutations(unprimed_ops))]
    y = [[j for j in range(i)] for i in range(n-1,0,-1)]
    all_ooo = [list(x) for x in list(itertools.product(*y))]
    num_primes = ops_.count("'")
    all_primes = [list(x) for x in list(itertools.product(range(2*n-1), repeat = num_primes))]
    for primes in all_primes:
        for nums in all_nums:
            Pnums = primage(nums,[pr for pr in primes if pr < n])
            w = apply(Pnums)
            for ops in all_ops:
                Pops = primage(ops,[pr-n for pr in primes if pr >= n])
                for ooo in all_ooo:
                    e = evalint(w, Pops, ooo)
                    if e in new_run:
                        print(e, '=', printer(Pnums,Pops,ooo))
                        new_run.remove(e)

if __name__ == '__main__':
    try_all()


