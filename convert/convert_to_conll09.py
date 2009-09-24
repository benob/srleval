import sys, re
import treenode

if len(sys.argv) != 5 and len(sys.argv) != 4:
    sys.stderr.write('USAGE: %s <parse_file> <prop_file> <dep_file> [dep_auto_file]\n' % sys.argv[0])
    sys.exit(1)

# setup args
parse_file = sys.argv[1]
prop_file = sys.argv[2]
dep_file = sys.argv[3]
dep_auto_file = False
if len(sys.argv) == 5:
    dep_auto_file = sys.argv[4]

# read treebank
parses = [x for x in treenode.TreeNode.readAllTrees(open(parse_file))]
# fix brackets
for parse in parses:
    for leaf in parse.leaves:
        if leaf.text == '-LRB-': leaf.text = '('
        if leaf.text == '-RRB-': leaf.text = ')'
        if leaf.text == '-LSB-': leaf.text = '['
        if leaf.text == '-RSB-': leaf.text = ']'
        if leaf.text == '-LCB-': leaf.text = '{'
        if leaf.text == '-RCB-': leaf.text = '{'

# read conll09 dependency trees (already speechified)
deps = []
dep = []

line_num = 0
for line in open(dep_file).xreadlines():
    line_num += 1
    line = line.strip()
    if line == '':
        if len(dep) > 0:
            deps.append(dep)
        dep = []
        continue
    tokens = line.split()
    dep.append([tokens[1], tokens[3], int(tokens[8]) - 1, tokens[9], '_', '_'])
if len(dep) > 0:
    deps.append(dep)

# read propbank
line_num = 0
lines = []
for line in open(prop_file).xreadlines():
    line_num += 1
    tokens = line.strip().split()
    tokens.insert(0, line_num)
    lines.append(tokens)

# DATA: prop files are not sorted correctly in ontonotes2.9
lines.sort(lambda x, y: cmp(int(x[2]) * 1000 + int(x[3]), int(y[2]) * 1000 + int(y[3])))

# align propbank to treebank
for tokens in lines:
    line_num = tokens[0]
    tokens = tokens[1:]
    if tokens[5] in ['have.01', 'be.03', 'do.01']:
        # DATA: skip auxiliares which should not be annotated! (vsj_0039)
        continue
    parse = parses[int(tokens[1])]
    predicate = parse.leaves[int(tokens[2])]
    predicate.sense = tokens[5]
    predicate.is_predicate = True
    predicate.arguments = []
    for location in tokens[7:]:
        # DATA: sometimes, rel is in upper case
        if location.lower().endswith('-rel'):
            continue
        type = '-'.join(location.split('-')[1:])
        for argument in location.split('-')[0].split('*'):
            # DATA: a few files have ; instead of ,
            for part in re.split(r'[,;]', argument):
                if not re.search(r'^\d+:\d+$', part):
                    # DATA: ontonotes2.0/wsj_1160 has an empty location
                    sys.stderr.write("WARNING: cannot parse argument '%s' in %s, line %d\n" % (location, prop_file, line_num))
                    continue
                start, depth = [int(x) for x in part.split(':')]
                node = parse.leaves[start]
                while depth > 0:
                    depth -= 1
                    node = node.parent
                predicate.arguments.append((node, type))

# speechify treebank
import utils
for tree in parses:
    utils.asrify(tree)
    #sys.stderr.write(str( tree) + '\n')
    for node in tree.leaves:
        if not hasattr(node, "is_predicate"): node.is_predicate = False
    for node in tree.leaves:
        if node.is_predicate:
            node.arguments = filter(lambda arg:arg[0].hasParent(node.root), node.arguments)

# align speechified dependency trees to speechified treebank
current = -1
dep_num = 0
for dep in deps:
    match = False
    while not match:
        match = True
        current += 1
        if current > len(parses) - 1:
            break
        for word in [x[0] for x in dep]:
            if not re.search(r'[a-zA-Z]', word):
                continue
            if not parses[current].hasLeaf(lambda x: x.text == word):
                sys.stderr.write('WARNING: while searching for %s, skipping %s\n' % (word, parses[current]))
                match = False
                break
    if current < len(parses):
        #print parses[current]
        word = 0
        parses[current].root.dep_num = dep_num
        used = [False for x in dep]
        for leaf in parses[current].leaves:
            leaf.dep_word = -2
            if leaf.label == '-NONE-':
                continue
            for word in range(len(dep)):
                if leaf.text == dep[word][0] and not used[word]:
                    leaf.dep_word = word
                    used[word] = True
                    found = True
                    break

    else:
        sys.stderr.write('ERROR: not found ' + str([x[0] for x in dep]) + ' in %s, line %d\n' % (dep_file, line_num))
        sys.exit(2)
    dep_num += 1

# transfer propbank annotation
for tree in parses:
    if not hasattr(tree, "dep_num") or tree.dep_num < 0 or tree.dep_num >= len(deps):
        sys.stderr.write('WARNING: dependency tree not found for %s\n' % str(tree))
        continue
    for leaf in tree.leaves:
        if leaf.is_predicate:
            if not hasattr(leaf, "dep_word") or leaf.dep_word < 0:
                sys.stderr.write('WARNING: predicate "%s" not found in dependency tree, in %s\n' % (leaf.text, str(tree)))
                continue
            dep = deps[tree.dep_num]
            dep[leaf.dep_word][5] = leaf.sense
            dep[leaf.dep_word][4] = 'Y'
            for word in dep:
                word.append('_')
            for argument in leaf.arguments:
                first_leaf = argument[0].leaves[0]
                last_leaf = argument[0].leaves[-1]
                for i in range(first_leaf.dep_word, last_leaf.dep_word + 1):
                    if dep[i][2] < first_leaf.dep_word or dep[i][2] > last_leaf.dep_word:
                                dep[i][-1] = argument[1]

# output conll09 dep+SRL format
if dep_auto_file:
    dep_auto = open(dep_auto_file)
line_num = 0
for dep in deps:
    if len(dep) == 1 and (dep[0][0] == '<TURN>' or dep[0][0] == 'MSNBC'):
        continue
    for i in range(len(dep)):
        line_num += 1
        output = [i + 1, dep[i][0], '_', '_', dep[i][1], '_', '_', '_', dep[i][2] + 1, '_', dep[i][3], '_', dep[i][4], dep[i][5]]
        if dep_auto_file:
            auto = dep_auto.readline().strip().split()
            if len(auto) < 10:
                print # add an empty line to help with "cat *|" commands
                sys.stderr.write('ERROR: desnynchronization with auto %s, in %s, line %d\n' % (auto, dep_auto_file, line_num))
                sys.exit(3)
            output[5] = auto[7] # pos
            output[9] = auto[8] # head
            output[11] = auto[9] # label
        output.extend(dep[i][6:])
        print '\t'.join([str(x) for x in output])
    line_num += 1
    if dep_auto_file:
        auto = dep_auto.readline().strip()
        if auto != '':
            print
            sys.stderr.write('ERROR: desnynchronization with auto %s, in %s, line %d\n' % (auto, dep_auto_file, line_num))
            sys.exit(3)
    print
