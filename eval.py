import sys, os, os.path, collections
import dependency, alignment

def flatten(input):
    output = []
    for element in input:
        if isinstance(element, tuple):
            output.extend(element)
        else:
            output.append(element)
    return output

def compute_fscore(correct, num_ref, num_hyp):
    recall = 0
    if num_ref != 0:
        recall = correct / num_ref
    precision = 0
    if num_hyp != 0:
        precision = correct / num_hyp
    fscore = 0
    if precision + recall != 0:
        fscore = 2 * (recall * precision) / (recall + precision)
    return (100 * recall, 100 * precision, 100 * fscore)

class Unordered:
    def __init__(self):
        self.depend = collections.defaultdict(int)
        self.srl = collections.defaultdict(int)

    def update_dict(self, dict, other):
        for key in other:
            dict[key] += other[key]

    def update(self, other):
        self.update_dict(self.depend, other.depend)
        self.update_dict(self.srl, other.srl)

    def output_dep(self, other):
        num_ref_depend = 0.0
        num_hyp_depend = 0.0
        num_both_depend = 0.0
        for key in self.depend:
            num_ref_depend += self.depend[key]
            if key in other.depend:
                if self.depend[key] > other.depend[key]:
                    num_both_depend += other.depend[key]
                else:
                    num_both_depend += self.depend[key]
        for key in other.depend:
            num_hyp_depend += other.depend[key]
        return compute_fscore(num_both_depend, num_ref_depend, num_hyp_depend)

    def output_srl(self, other):
        num_ref_srl = 0.0
        num_hyp_srl = 0.0
        num_both_srl = 0.0
        for key in self.srl:
            num_ref_srl += self.srl[key]
            if key in other.srl:
                if self.srl[key] > other.srl[key]:
                    num_both_srl += other.srl[key]
                else:
                    num_both_srl += self.srl[key]
        for key in other.srl:
            num_hyp_srl += other.srl[key]
        return compute_fscore(num_both_srl, num_ref_srl, num_hyp_srl)

class Counter:
    def __init__(self):
        self.correct_labeled_attachments = 0.0
        self.correct_unlabeled_attachments = 0.0
        self.correct_labels = 0.0
        self.correct_lexicalized = 0.0
        self.correct_sem_labeled = 0.0
        self.correct_sem_unlabeled = 0.0
        self.correct_sem_proposition = 0.0
        self.correct_sem_predicate = 0.0
        self.correct_sem_sentence = 0.0
        self.correct_sem_lexicalized = 0.0
        self.correct_sentence_boundaries = 0.0
        self.correct_pos_tags = 0.0
        self.num_ref_sem_predicates = 0.0
        self.num_hyp_sem_predicates = 0.0
        self.num_ref_sem_arcs = 0.0
        self.num_hyp_sem_arcs = 0.0
        self.exact_syntax_match = 0.0
        self.num_ref_sentences = 0.0
        self.num_hyp_sentences = 0.0
        self.num_ref_words = 0.0
        self.num_hyp_words = 0.0
        self.word_errors = 0.0
        self.unordered_ref = Unordered()
        self.unordered_hyp = Unordered()
    def update(self, other):
        self.update_aligned(other)
        self.unordered_ref.update(other.unordered_ref)
        self.unordered_hyp.update(other.unordered_hyp)
    def update_aligned(self, other):
        self.correct_labeled_attachments += other.correct_labeled_attachments
        self.correct_unlabeled_attachments += other.correct_unlabeled_attachments
        self.correct_labels += other.correct_labels
        self.correct_lexicalized += other.correct_lexicalized
        self.correct_sem_labeled += other.correct_sem_labeled
        self.correct_sem_unlabeled += other.correct_sem_unlabeled
        self.correct_sem_proposition += other.correct_sem_proposition
        self.correct_sem_predicate += other.correct_sem_predicate
        self.correct_sem_sentence += other.correct_sem_sentence
        self.correct_sem_lexicalized += other.correct_sem_lexicalized
        self.correct_sentence_boundaries += other.correct_sentence_boundaries
        self.correct_pos_tags += other.correct_pos_tags
        self.num_ref_sem_predicates += other.num_ref_sem_predicates
        self.num_hyp_sem_predicates += other.num_hyp_sem_predicates
        self.num_ref_sem_arcs += other.num_ref_sem_arcs
        self.num_hyp_sem_arcs += other.num_hyp_sem_arcs
        self.exact_syntax_match += other.exact_syntax_match
        self.num_ref_sentences += other.num_ref_sentences
        self.num_hyp_sentences += other.num_hyp_sentences
        self.num_ref_words += other.num_ref_words
        self.num_hyp_words += other.num_hyp_words
        self.word_errors += other.word_errors

    def output(self):
        print "Syntactic labeled attachments:    r= %6.2f  p= %6.2f  f= %6.2f" \
            % compute_fscore(self.correct_labeled_attachments, self.num_ref_words, self.num_hyp_words)
        print "          unlabeled attachments:  r= %6.2f  p= %6.2f  f= %6.2f" \
            % compute_fscore(self.correct_unlabeled_attachments, self.num_ref_words, self.num_hyp_words)
        print "          labels:                 r= %6.2f  p= %6.2f  f= %6.2f" \
            % compute_fscore(self.correct_labels, self.num_ref_words, self.num_hyp_words)
        print "          lexicalized:            r= %6.2f  p= %6.2f  f= %6.2f" \
            % compute_fscore(self.correct_lexicalized, self.num_ref_words, self.num_hyp_words)
        print "          exact sentences:        r= %6.2f  p= %6.2f  f= %6.2f" \
            % compute_fscore(self.exact_syntax_match, self.num_ref_sentences, self.num_hyp_sentences)
        print "          unordered:              r= %6.2f  p= %6.2f  f= %6.2f" \
            % self.unordered_ref.output_dep(self.unordered_hyp)
        print "Semantic  labeled arcs:           r= %6.2f  p= %6.2f  f= %6.2f" \
            % compute_fscore(self.correct_sem_labeled, self.num_ref_sem_arcs, self.num_hyp_sem_arcs)
        print "          unlabeled arcs:         r= %6.2f  p= %6.2f  f= %6.2f" \
            % compute_fscore(self.correct_sem_unlabeled, self.num_ref_sem_arcs, self.num_hyp_sem_arcs)
        print "          lexicalized:            r= %6.2f  p= %6.2f  f= %6.2f" \
            % compute_fscore(self.correct_sem_lexicalized, self.num_ref_sem_arcs, self.num_hyp_sem_arcs)
        print "          predicates:             r= %6.2f  p= %6.2f  f= %6.2f" \
            % compute_fscore(self.correct_sem_predicate, self.num_ref_sem_predicates, self.num_hyp_sem_predicates)
        print "          propositions:           r= %6.2f  p= %6.2f  f= %6.2f" \
            % compute_fscore(self.correct_sem_proposition, self.num_ref_sem_predicates, self.num_hyp_sem_predicates)
        print "          exact sentences:        r= %6.2f  p= %6.2f  f= %6.2f" \
            % compute_fscore(self.correct_sem_sentence, self.num_ref_sentences, self.num_hyp_sentences)
        print "          unordered:              r= %6.2f  p= %6.2f  f= %6.2f" \
            % self.unordered_ref.output_srl(self.unordered_hyp)
        factor = 0.5
        syntax_labeled = compute_fscore(self.correct_labeled_attachments, self.num_ref_words, self.num_hyp_words)
        sem_labeled = compute_fscore(self.correct_sem_labeled, self.num_ref_sem_arcs, self.num_hyp_sem_arcs)
        print "Overall   macro labeled (%g):" % factor + "    r= %6.2f  p= %6.2f  f= %6.2f" \
            % tuple([((1 - factor) * syntax_labeled[i] + factor * sem_labeled[i]) for i in range(3)])
        syntax_unlabeled = compute_fscore(self.correct_unlabeled_attachments, self.num_ref_words, self.num_hyp_words)
        sem_unlabeled = compute_fscore(self.correct_sem_unlabeled, self.num_ref_sem_arcs, self.num_hyp_sem_arcs)
        print "          macro unlabeled (%g):" % factor + "  r= %6.2f  p= %6.2f  f= %6.2f" \
            % tuple([((1 - factor) * syntax_unlabeled[i] + factor * sem_unlabeled[i]) for i in range(3)])
        print "          micro labeled:          r= %6.2f  p= %6.2f  f= %6.2f" \
            % compute_fscore(self.correct_labeled_attachments + self.correct_sem_labeled, self.num_ref_words \
            + self.num_ref_sem_arcs, self.num_hyp_words + self.num_hyp_sem_arcs)
        print "          micro unlabeled:        r= %6.2f  p= %6.2f  f= %6.2f" \
            % compute_fscore(self.correct_unlabeled_attachments + self.correct_sem_unlabeled, \
            self.num_ref_words + self.num_ref_sem_arcs, self.num_hyp_words + self.num_hyp_sem_arcs)
        if self.num_ref_words != 0:
            print "Word error rate:                  %6.2f %%" % (100 * self.word_errors / self.num_ref_words)
        else:
            print "Word error rate:                  100.00 %"
        print "Sentence boundaries:              r= %6.2f  p= %6.2f  f= %6.2f" \
            % compute_fscore(self.correct_sentence_boundaries, self.num_ref_sentences, self.num_hyp_sentences)
        print "Part-of-speech tags:              r= %6.2f  p= %6.2f  f= %6.2f" \
            % compute_fscore(self.correct_pos_tags, self.num_ref_words, self.num_hyp_words)

    def csv_headers(self):
        print ";".join(("file", "syn-r", "syn-p", "syn-f", "sem-r", "sem-p", "sem-f", "pred-r", "pred-p", "pred-f", "macro", "micro", "wer", "sbd-r", "sbd-p", "sbd-f", "pos", "unordered-syn-f", "unordered-sem-f"))

    def output_csv(self,name):
        factor = 0.5
        syntax_labeled = compute_fscore(self.correct_labeled_attachments, self.num_ref_words, self.num_hyp_words)
        sem_labeled = compute_fscore(self.correct_sem_labeled, self.num_ref_sem_arcs, self.num_hyp_sem_arcs)

        print ";".join([ str(x) for x in flatten(( name, \
            compute_fscore(self.correct_labeled_attachments, self.num_ref_words, self.num_hyp_words), \
            compute_fscore(self.correct_sem_labeled, self.num_ref_sem_arcs, self.num_hyp_sem_arcs), \
            compute_fscore(self.correct_sem_predicate, self.num_ref_sem_predicates, self.num_hyp_sem_predicates), \
            (1 - factor) * syntax_labeled[2] + factor * sem_labeled[2], \
            compute_fscore(self.correct_labeled_attachments + self.correct_sem_labeled, self.num_ref_words \
                        + self.num_ref_sem_arcs, self.num_hyp_words + self.num_hyp_sem_arcs)[2], \
            (100 * self.word_errors / self.num_ref_words), \
            compute_fscore(self.correct_sentence_boundaries, self.num_ref_sentences, self.num_hyp_sentences), \
            compute_fscore(self.correct_pos_tags, self.num_ref_words, self.num_hyp_words)[2], \
            self.unordered_ref.output_dep(self.unordered_hyp)[2], \
            self.unordered_ref.output_srl(self.unordered_hyp)[2], \
            compute_fscore(self.correct_lexicalized, self.num_ref_words, self.num_hyp_words)[2], \
            compute_fscore(self.correct_sem_lexicalized, self.num_ref_sem_arcs, self.num_hyp_sem_arcs)[2], \

            ))])

def collect_unordered_stats(tree):
    stats = Unordered()
    for word in tree:
        if word.parent:
            stats.depend["%s %s %s" % (word.text, word.label, word.parent.text)] += 1
        else:
            stats.depend["%s %s ROOT" % (word.text, word.label)] += 1
        if word.isPredicate():
            stats.srl["%s SENSE %s" % (word.text, word.predicate.split(".")[-1])] += 1
            for argument in word.arguments:
                stats.srl["%s %s %s" % (word.text, argument[1], argument[0].text)] += 1
    return stats

def compare_with_alignment(ref_file, hyp_file):
    stats = Counter()
    ref_trees = [x for x in dependency.DependencyNode.readAllTrees(open(ref_file))]
    ref_words = []
    num = 0
    for tree in ref_trees:
        stats.unordered_ref.update(collect_unordered_stats(tree))
        for word in tree:
            ref_words.append("%s %d %d" % (word.text, num, word.id))
            word.aligned_to = None
        num += 1
    hyp_trees = [x for x in dependency.DependencyNode.readAllTrees(open(hyp_file))]
    hyp_words = []
    num = 0
    for tree in hyp_trees:
        stats.unordered_hyp.update(collect_unordered_stats(tree))
        for word in tree:
            hyp_words.append("%s %d %d" % (word.text, num, word.id))
            word.aligned_to = None
        num += 1
    for item in alignment.align(ref_words, hyp_words, command=os.path.dirname(__file__) + "/align/align"):
        if item[0] == None or item[1] == None:
            stats.word_errors += 1
            continue
        ref_tree = ref_trees[int(item[0][1])]
        ref_word = ref_tree.words[int(item[0][2]) - 1]
        hyp_tree = hyp_trees[int(item[1][1])]
        hyp_word = hyp_tree.words[int(item[1][2]) - 1]
        ref_word.aligned_to = hyp_word
        hyp_word.algined_to = ref_word
        if ref_word.tag == hyp_word.tag:
            stats.correct_pos_tags += 1
    # sentence boundary detection perf
    for i in xrange(len(ref_words)):
        text, tree_id, word_id = ref_words[i].split()
        tree = ref_trees[int(tree_id)]
        word = tree.words[int(word_id) - 1]
        if word.aligned_to:
            next = i + 1
            next_word = None
            while next < len(ref_words):
                text, tree_id, word_id = ref_words[next].split()
                tree = ref_trees[int(tree_id)]
                next_word = tree.words[int(word_id) - 1]
                if next_word.aligned_to:
                    break
                next += 1
            if next == len(ref_words):
                stats.correct_sentence_boundaries += 1 # last sentence is always right
            else:
                if word.root != next_word.root: # in a different tree on both sides
                    if word.aligned_to.root != next_word.aligned_to.root:
                        stats.correct_sentence_boundaries += 1

    # SRL perf 
    for tree in ref_trees:
        sentence_errors = 0
        for word in tree:
            if word.isPredicate():
                stats.num_ref_sem_predicates += 1
                stats.num_ref_sem_arcs += 1 + len(word.arguments)
                if word.aligned_to == None: 
                    sentence_errors = 1
                    continue
                if word.aligned_to.isPredicate():
                    stats.correct_sem_unlabeled += 1
                    stats.correct_sem_predicate += 1
                    predicate_match = 0
                    if word.predicate.split(".")[-1] == word.aligned_to.predicate.split(".")[-1]:
                        # predicate sense is matched
                        stats.correct_sem_labeled += 1
                        if word.text.lower() == word.aligned_to.text.lower():
                            stats.correct_sem_lexicalized += 1
                        predicate_match = 1
                    found_all = 1
                    for argument in word.arguments:
                        node = argument[0]
                        label = argument[1]
                        found = 0
                        for peer_argument in word.aligned_to.arguments:
                            peer_node = peer_argument[0]
                            peer_label = peer_argument[1]
                            if node.aligned_to == peer_node:
                                stats.correct_sem_unlabeled += 1
                                if label == peer_label:
                                    stats.correct_sem_labeled += 1
                                    if node.text.lower() == node.aligned_to.text.lower():
                                        stats.correct_sem_lexicalized += 1
                                    found = 1
                        if found == 0:
                            found_all = 0
                    if found_all and predicate_match and len(word.arguments) == len(word.aligned_to.arguments):
                        stats.correct_sem_proposition += 1
                    else:
                        sentence_errors = 1
                else:
                    sentence_errors = 1
        if sentence_errors == 0:
            stats.correct_sem_sentence += 1

    for tree in hyp_trees:
        for word in tree:
            if word.isPredicate():
                stats.num_hyp_sem_predicates += 1
                stats.num_hyp_sem_arcs += 1 + len(word.arguments)

    for tree in ref_trees:
        has_errors = 0
        for word in tree:
            if word.aligned_to == None: 
                has_errors = 1
                continue
            if word.text != word.aligned_to.text:
                stats.word_errors += 1
            parent1 = None
            if word.parent: parent1 = word.parent.text
            parent2 = None
            if word.aligned_to.parent: parent2 = word.aligned_to.parent.text
            if word.label == word.aligned_to.label:
                stats.correct_labels += 1
                if word.parent and word.aligned_to.parent:
                    if word.parent.aligned_to == word.aligned_to.parent: # the parents are aligned
                        stats.correct_labeled_attachments += 1
                        if word.text.lower() == word.aligned_to.text.lower():
                            stats.correct_lexicalized += 1
                if not word.parent and not word.aligned_to.parent: # both are ROOT
                    stats.correct_labeled_attachments += 1
                    if word.text.lower() == word.aligned_to.text.lower():
                        stats.correct_lexicalized += 1
            if word.parent and word.aligned_to.parent:
                if word.parent.aligned_to == word.aligned_to.parent: # the parents are aligned
                    stats.correct_unlabeled_attachments += 1
            if not word.parent and not word.aligned_to.parent: # both are ROOT
                stats.correct_unlabeled_attachments += 1
            # check the sentence for errors
            if word.label != word.aligned_to.label or (word.parent == None and word.aligned_to.parent != None) \
                    or (word.parent != None and word.aligned_to.parent == None) \
                    or (word.parent != None and word.aligned_to.parent != None \
                    and word.parent.aligned_to != word.aligned_to.parent):
                has_errors = 1
        if has_errors == 0:
            stats.exact_syntax_match += 1
    stats.num_ref_words = len(ref_words)
    stats.num_hyp_words = len(hyp_words)
    stats.num_ref_sentences = len(ref_trees)
    stats.num_hyp_sentences = len(hyp_trees)
    return stats

def recursive(ref_dir, hyp_dir, ref_ext, hyp_ext, csv=False):
    stats = Counter()
    if csv:
        stats.csv_headers()
    for dirpath, dirnames, filenames in os.walk(ref_dir):
        dir = dirpath[len(ref_dir):]
        for file in filenames:
            if not file.endswith(ref_ext): continue
            file = file[:len(file) - len(ref_ext)]
            if os.path.exists(os.path.join(hyp_dir, dir, file + hyp_ext)):
                ref_file = os.path.join(ref_dir, dir, file + ref_ext)
                hyp_file = os.path.join(hyp_dir, dir, file + hyp_ext)
                file_stats = compare_with_alignment(ref_file, hyp_file)
                if csv:
                    file_stats.output_csv(os.path.join(dir, file))
                stats.update(file_stats)
    if csv:
        stats.output_csv("TOTAL")
    else:
        stats.output()

if __name__ == '__main__':
    if len(sys.argv) == 5:
        recursive(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
    elif len(sys.argv) == 3:
        stats = compare_with_alignment(sys.argv[1], sys.argv[2])
        stats.output()
    else:
        sys.stderr.write('USAGE: %s (ref_file hyp_file|ref_dir hyp_dir ref_ext hyp_ext)\n' % sys.argv[0])
        sys.exit(1)
