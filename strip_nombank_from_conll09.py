import sys, re

pred_count = 0
words = []
strip_list = []
for line in sys.stdin:
    tokens = line.strip().split()
    if len(tokens) == 0:
        #print "** REMOVING", strip_list
        pred_count = 0
        for word in words:
            output = []
            for i in xrange(len(word)):
                if i > 13:
                    word[i] = re.sub(r'^[CR]-', '', word[i])
                    word[i] = re.sub(r'^A', 'ARG', word[i])
                if i not in strip_list:
                    output.append(word[i])
            print "\t".join(output)
        words = []
        strip_list = []
        print
        continue
    if tokens[12] == "Y":
        if not tokens[5].startswith("V"):
            tokens[12] = "_"
            tokens[13] = "_"
            strip_list.append(pred_count + 14)
        pred_count += 1
    words.append(tokens)
