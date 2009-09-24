import sys, os, os.path
import collections
import dependency

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

class Stats:
    def __init__(self):
        self.depend = collections.defaultdict(int)
        self.srl = collections.defaultdict(int)

    def update_dict(self, dict, other):
        for key in other:
            dict[key] += other[key]

    def update(self, other):
        self.update_dict(self.depend, other.depend)
        self.update_dict(self.srl, other.srl)

    def output(self, other):
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
        print "unordered dependencies:  r= %05.2f  p= %05.2f  f= %05.2f" \
            % compute_fscore(num_both_depend, num_ref_depend, num_hyp_depend)
        print "unordered semantic arcs: r= %05.2f  p= %05.2f  f= %05.2f" \
            % compute_fscore(num_both_srl, num_ref_srl, num_hyp_srl)


def collect_stats(tree):
    stats = Stats()
    for word in tree:
        if word.parent:
            stats.depend["%s %s %s" % (word.lemma, word.label, word.parent.lemma)] += 1
        else:
            stats.depend["%s %s ROOT" % (word.lemma, word.label)] += 1
        if word.isPredicate():
            stats.srl["%s SENSE %s" % (word.lemma, word.predicate.split(".")[-1])] += 1
            for argument in word.arguments:
                stats.srl["%s %s %s" % (word.lemma, argument[1], argument[0].lemma)] += 1
    return stats

def compare_with_alignment(ref_file, hyp_file):
    ref_stats = Stats()
    for tree in dependency.DependencyNode.readAllTrees(open(ref_file)):
        ref_stats.update(collect_stats(tree))
    hyp_stats = Stats()
    for tree in dependency.DependencyNode.readAllTrees(open(hyp_file)):
        hyp_stats.update(collect_stats(tree))
    return ref_stats, hyp_stats

def recursive(ref_dir, hyp_dir, ref_ext, hyp_ext):
    ref_stats = Stats()
    hyp_stats = Stats()
    for dirpath, dirnames, filenames in os.walk(ref_dir):
        dir = dirpath[len(ref_dir):]
        for file in filenames:
            if not file.endswith(ref_ext): continue
            file = file[:len(file) - len(ref_ext)]
            if os.path.exists(os.path.join(hyp_dir, dir, file + hyp_ext)):
                ref_file = os.path.join(ref_dir, dir, file + ref_ext)
                hyp_file = os.path.join(hyp_dir, dir, file + hyp_ext)
                file_ref_stats, file_hyp_stats = compare_with_alignment(ref_file, hyp_file)
                ref_stats.update(file_ref_stats)
                hyp_stats.update(file_hyp_stats)
                #file_stats.output_values(os.path.join(dir, file))
                #print os.path.join(dir, file), " corr=%5d  ref=%5d  hyp=%5d  recall=%.3f  prec=%.3f  fscore=%.3f" % stats
    ref_stats.output(hyp_stats)

if __name__ == '__main__':
    if len(sys.argv) == 5:
        recursive(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
    elif len(sys.argv) == 3:
        ref_stats, hyp_stats = compare_with_alignment(sys.argv[1], sys.argv[2])
        ref_stats.output(hyp_stats)
    else:
        sys.stderr.write('USAGE: %s <ref_dir> <hyp_dir> <ref_ext> <hyp_ext>\n' % sys.argv[0])
        sys.exit(1)
