import sys

for line in sys.stdin:
    tokens = line.strip().split()
    if len(tokens) == 0:
        print
        continue
    # input: id word lemma plemma pos ppos features pfeatures head phead label plabel ispred pred arguments
    # output: id word lemma pos ppos sword slemma spos head label pred arguments
    output = [tokens[x] for x in (0, 1, 2, 4, 4, 1, 2, 4, 8, 10)]
    output.extend(tokens[13:])
    print "\t".join(output)
