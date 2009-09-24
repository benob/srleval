import sys

for line in sys.stdin:
    tokens = line.strip().split()
    if len(tokens) == 0:
        print
        continue
    # input: id word lemma pos ppos sword slemma spos head label pred arguments
    # output: id word lemma plemma pos ppos features pfeatures head phead label plabel ispred pred arguments
    tokens.append('_')
    output = [tokens[x] for x in (0, 1, 2, 2, 3, 4, -1, -1, 8, 8, 9, 9, -1)]
    tokens.pop()
    output.extend(tokens[10:])
    if output[13] != "_":
        output[12] = "Y"
    print "\t".join(output)
