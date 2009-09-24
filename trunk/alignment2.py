import sys, os
from numpy import *

def align(array1, array2, comparator=lambda x, y: cmp(x[0], y[0])):
    array1 = [x.split() for x in array1]
    array2 = [x.split() for x in array2]
    print len(array1), len(array2)
    if array1 == array2:
        return zip(array1, array2)
    cost = zeros((len(array1) + 1, len(array2) + 1))
    backtrace = zeros((len(array1) + 1, len(array2) + 1))
    for i in xrange(len(array1) + 1):
        cost[i][0] = i
        backtrace[i][0] = 1
    for j in xrange(len(array2) + 1):
        cost[0][j] = j
        backtrace[0][j] = 2
    for i in xrange(1, len(array1) + 1):
        for j in xrange(1, len(array2) + 1):
            sub_value = cost[i - 1][j - 1]
            #if comparator(array1[i - 1], array2[j - 1]) != 0:
            if array1[i - 1] != array2[j - 1]:
                sub_value += 3
            del_value = cost[i - 1][j] + 1
            ins_value = cost[i][j - 1] + 1
            if sub_value <= del_value:
                if sub_value <= ins_value:
                    cost[i][j] = sub_value
                    backtrace[i][j] = 0
                else:
                    cost[i][j] = ins_value
                    backtrace[i][j] = 2
            else:
                if del_value <= ins_value:
                    cost[i][j] = del_value
                    backtrace[i][j] = 1
                else:
                    cost[i][j] = ins_value
                    backtrace[i][j] = 2
    output = []
    i = len(array1)
    j = len(array2)
    while i > 0 or j > 0:
        if backtrace[i][j] == 0:
            output.insert(0, (array1[i - 1], array2[j - 1]))
            i -= 1
            j -= 1
        elif backtrace[i][j] == 1:
            output.insert(0, (array1[i - 1], None))
            i -= 1
        else:
            output.insert(0, (None, array2[j - 1]))
            j -= 1
    return output

if __name__ == "__main__":
    alignment = align([1,2,3,4,5,6,7,8,9], [1,2,2,3,4,5,5,5,5,5,5,6,7,8])
    for pair in alignment:
        print pair
