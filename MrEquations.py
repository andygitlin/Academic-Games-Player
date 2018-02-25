import numpy as np
import itertools

'''
following represents (1+24)x(6+(2+120))
nums = [1,24,6,2,120]
ops = ['+','x','+','+']
ooo = [0,2,1,0]
'''

MOP_PERMITTED = True
# if True, allows each operation in ops to be used any number of times (including zero times)
# if False, every operation in ops is used exactly once (so len(ops) must equal len(nums)-1)
SIDEWAYS = True
# if True, allows sideways variation to be used
# if False, forbids sideways variation

def apply(nums, app):
    def application(x,n):
        if n == -1 and SIDEWAYS:
            return 1.0 / x
        if n == 0:
            return x
        if n == 1:
            return np.math.factorial(x)
        return application(np.math.factorial(x),n-1)
    return [application(nums[i],app[i]) for i in range(len(nums))]

def eval(nums, ops, ooo):
    if len(ooo) == 0:
        return nums[0]
    new_nums = [i for i in nums]
    new_ops = [i for i in ops]
    new_ooo = [i for i in ooo]
    try:
        if ops[ooo[0]] == '+':
            new_nums[ooo[0]] = nums[ooo[0]] + nums[ooo[0]+1]
        elif ops[ooo[0]] == '-':
            new_nums[ooo[0]] = nums[ooo[0]] - nums[ooo[0]+1]
        elif ops[ooo[0]] == 'x':
            new_nums[ooo[0]] = nums[ooo[0]] * nums[ooo[0]+1]
        elif ops[ooo[0]] == '/':
            new_nums[ooo[0]] = nums[ooo[0]] / nums[ooo[0]+1]
        elif ops[ooo[0]] == '*':
            new_nums[ooo[0]] = np.power(float(nums[ooo[0]]),float(nums[ooo[0]+1]))
        elif ops[ooo[0]] == 'r':
            new_nums[ooo[0]] = np.power(float(nums[ooo[0]+1]),float(1.0/nums[ooo[0]]))
    except:
        return np.nan
    new_nums.pop(ooo[0]+1)
    new_ops.pop(ooo[0])
    new_ooo.pop(0)
    return eval(new_nums, new_ops, new_ooo)

def printer(nums, ops, ooo, app):
    def apply_string(x,n):
        if n == -1 and SIDEWAYS:
            return str(x) + 's'
        if n == 0:
            return str(x)
        return '(' + str(x) + ('!' * n) + ')'
    new_nums = [apply_string(nums[i],app[i]) for i in range(len(nums))]
    new_ops = [i for i in ops]
    new_ooo = [i for i in ooo]
    while len(new_nums) > 1:
        if len(new_nums) != 2:
            new_nums[new_ooo[0]] = '(' + new_nums[new_ooo[0]] + new_ops[new_ooo[0]] + new_nums[new_ooo[0]+1] + ')'
        else:
            new_nums[new_ooo[0]] = new_nums[new_ooo[0]] + new_ops[new_ooo[0]] + new_nums[new_ooo[0]+1]
        new_nums.pop(new_ooo[0]+1)
        new_ops.pop(new_ooo[0])
        new_ooo.pop(0)
    return new_nums[0]

def try_all(nums_ = [1,2,3,4,5], ops_ = ['+','-','x','/','*','r'], factorial = 1, run = []):
    n = len(nums_)
    new_run = [i for i in run]
    all_nums = [list(x) for x in list(itertools.permutations(nums_))]
    all_ops = [list(x) for x in list(itertools.permutations(ops_))] if not MOP_PERMITTED else [list(x) for x in list(itertools.product(ops_, repeat = n-1))]
    y = [[j for j in range(i)] for i in range(n-1,0,-1)]
    all_ooo = [list(x) for x in list(itertools.product(*y))]
    yy = [j for j in range(-1,factorial+1)] if SIDEWAYS else [j for j in range(0,factorial+1)]
    all_app = [list(x) for x in list(itertools.product(yy, repeat = n))]
    for nums in all_nums:
        for app in all_app:
            good_to_go = True
            for i in range(len(nums)):
                if (nums[i] == 1 and app[i] != 0):
                    good_to_go = False
                elif (nums[i] == 2 and app[i] >= 1):
                    good_to_go = False
            if good_to_go:
                w = apply(nums, app)
                for ops in all_ops:
                    for ooo in all_ooo:
                        e = eval(w, ops, ooo)
                        for rr in range(len(new_run)):
                            try:
                                if np.isfinite(e) and abs(run[rr]-e) < 0.001:
                                    print(e, '=', printer(nums,ops,ooo,app))
                                    new_run.remove(new_run[rr])
                            except:
                                pass

if __name__ == '__main__':
    try_all(factorial = 2, run = [884,886,887,889,890,892])


