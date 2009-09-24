import sys, os, random
import eval

def collect(ref_dir, hyp_dir, ref_ext, hyp_ext, csv=False):
    output = []
    for dirpath, dirnames, filenames in os.walk(ref_dir):
        dir = dirpath[len(ref_dir):]
        for file in filenames:
            if not file.endswith(ref_ext): continue
            file = file[:len(file) - len(ref_ext)]
            if os.path.exists(os.path.join(hyp_dir, dir, file + hyp_ext)):
                ref_file = os.path.join(ref_dir, dir, file + ref_ext)
                hyp_file = os.path.join(hyp_dir, dir, file + hyp_ext)
                file_stats = eval.compare_with_alignment(ref_file, hyp_file)
                output.append(file_stats)
    return output

def compute_difference(sys1_list, sys2_list):
    sys1 = eval.Counter()
    for stats in sys1_list:
        sys1.update_aligned(stats)
    sys2 = eval.Counter()
    for stats in sys2_list:
        sys2.update_aligned(stats)
    if sys1.num_ref_words == 0:
        sys1.num_ref_words = 1
        sys1.word_errors = 0
    if sys2.num_ref_words == 0:
        sys2.num_ref_words = 1
        sys2.word_errors = 0
    difference = [ \
        eval.compute_fscore(sys1.correct_labeled_attachments, sys1.num_ref_words, sys1.num_hyp_words)[2] - eval.compute_fscore(sys2.correct_labeled_attachments, sys2.num_ref_words, sys2.num_hyp_words)[2], \
        eval.compute_fscore(sys1.correct_unlabeled_attachments, sys1.num_ref_words, sys1.num_hyp_words)[2] - eval.compute_fscore(sys2.correct_unlabeled_attachments, sys2.num_ref_words, sys2.num_hyp_words)[2], \
        eval.compute_fscore(sys1.correct_sem_labeled, sys1.num_ref_sem_arcs, sys1.num_hyp_sem_arcs)[2] - eval.compute_fscore(sys2.correct_sem_labeled, sys2.num_ref_sem_arcs, sys2.num_hyp_sem_arcs)[2], \
        eval.compute_fscore(sys1.correct_sem_unlabeled, sys1.num_ref_sem_arcs, sys1.num_hyp_sem_arcs)[2] - eval.compute_fscore(sys2.correct_sem_unlabeled, sys2.num_ref_sem_arcs, sys2.num_hyp_sem_arcs)[2], \
        eval.compute_fscore(sys1.correct_sem_predicate, sys1.num_ref_sem_predicates, sys1.num_hyp_sem_predicates)[2] - eval.compute_fscore(sys2.correct_sem_predicate, sys2.num_ref_sem_predicates, sys2.num_hyp_sem_predicates)[2], \
        (100 * sys1.word_errors / sys1.num_ref_words) -  (100 * sys2.word_errors / sys2.num_ref_words), \
        eval.compute_fscore(sys1.correct_sentence_boundaries, sys1.num_ref_sentences, sys1.num_hyp_sentences)[2] - eval.compute_fscore(sys2.correct_sentence_boundaries, sys2.num_ref_sentences, sys2.num_hyp_sentences)[2], \
        eval.compute_fscore(sys1.correct_pos_tags, sys1.num_ref_words, sys1.num_hyp_words)[2] - eval.compute_fscore(sys2.correct_pos_tags, sys2.num_ref_words, sys2.num_hyp_words)[2] \
        ]

    return difference

def compute_fast_difference(sys1, sys2):
    sys1_agregate = [0, 0, 0]
    for stats in sys1:
        for i in xrange(3):
            sys1_agregate[i] += stats[i]
    sys2_agregate = [0, 0, 0]
    for stats in sys2:
        for i in xrange(3):
            sys2_agregate[i] += stats[i]
    score1 = eval.compute_fscore(sys1_agregate[0], sys1_agregate[1], sys1_agregate[2])
    score2 = eval.compute_fscore(sys2_agregate[0], sys2_agregate[1], sys2_agregate[2])
    return score1[2] - score2[2]
    
if __name__ == '__main__':
    if len(sys.argv) == 7:
        #print "collecting stats from sys1"
        #sys1 = [(x.correct_labeled_attachments, x.num_ref_words, x.num_hyp_words) for x in collect(sys.argv[1], sys.argv[2], sys.argv[4], sys.argv[5])]
        sys1 = collect(sys.argv[1], sys.argv[2], sys.argv[4], sys.argv[5])
        #print "collecting stats from sys2"
        #sys2 = [(x.correct_labeled_attachments, x.num_ref_words, x.num_hyp_words) for x in collect(sys.argv[1], sys.argv[3], sys.argv[4], sys.argv[6])]
        sys2 = collect(sys.argv[1], sys.argv[3], sys.argv[4], sys.argv[6])
        original_difference = compute_difference(sys1, sys2)
        random_difference = [0 for x in original_difference]
        random.seed()
        iterations = 10000
        pvalue = 0
        #print "computing p-value"
        for i in xrange(iterations):
            for j in xrange(len(sys1)):
                if random.random() > 0.5:
                    tmp = sys1[j]
                    sys1[j] = sys2[j]
                    sys2[j] = tmp
            difference = compute_difference(sys1, sys2)
            for j in xrange(len(difference)):
                if original_difference[j] >= 0 and difference[j] >= original_difference[j]:
                    random_difference[j] += 1
                if original_difference[j] <= 0 and difference[j] <= original_difference[j]:
                    random_difference[j] += 1
        pvalue = [(x + 1.0) / (iterations + 1.0) for x in random_difference]
        significance = ['no' for x in pvalue]
        for i in xrange(len(pvalue)):
            if pvalue[i] > 1: pvalue[i] = 1
            if pvalue[i] < .01:
                significance[i] = 'yes <1%'
            elif pvalue[i] < .05:
                significance[i] = 'yes <5%'
        print "Syntactic labeled attachments:     diff= %8.2f p-value= %6.3g  %s" % (original_difference[0], pvalue[0], significance[0])
        print "          unlabeled attachments:   diff= %8.2f p-value= %6.3g  %s" % (original_difference[1], pvalue[1], significance[1])
        print "Semantic  labeled attachments:     diff= %8.2f p-value= %6.3g  %s" % (original_difference[2], pvalue[2], significance[2])
        print "          unlabeled attachments:   diff= %8.2f p-value= %6.3g  %s" % (original_difference[3], pvalue[3], significance[3])
        print "          predicates:              diff= %8.2f p-value= %6.3g  %s" % (original_difference[4], pvalue[4], significance[4])
        print "Word error rate:                   diff= %8.2f p-value= %6.3g  %s" % (original_difference[5], pvalue[5], significance[5])
        print "Sentence boundaries:               diff= %8.2f p-value= %6.3g  %s" % (original_difference[6], pvalue[6], significance[6])
        print "Part-of-speech tags:               diff= %8.2f p-value= %6.3g  %s" % (original_difference[7], pvalue[7], significance[7])

    else:
        sys.stderr.write('USAGE: %s <ref_dir> <sys1_dir> <sys2_dir> <ref_ext> <sys1_ext> <sys2_ext>\n' % sys.argv[0])
        sys.exit(1)
