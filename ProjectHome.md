# Summary #
Semantic role labeling (SRL) is an important module of spoken language understanding systems.
This project extends the CoNLL-09 evaluation [metrics](http://ufal.mff.cuni.cz/conll2009-st/scorer.html) for joint dependency parsing and
SRL of text in order to be able to handle speech recognition output
with word errors and sentence segmentation errors. `srleval` performs a word alignment between the reference and the hypothesis, and derives performance measures from this alignment. It also outputs a bag-of-relation ("unaligned") metric that is independent from location and does not require alignment.

# File format #

The file format is described in the CoNLL-09 shared task at http://ufal.mff.cuni.cz/conll2009-st/task-description.html. It's one word per line, a blank line at the end of a sentence. The column names are:
```
ID FORM LEMMA PLEMMA POS PPOS FEAT PFEAT HEAD PHEAD DEPREL PDEPREL FILLPRED PRED APREDs 
```
We provide scripts to convert from and to the CoNLL-08 format.

# Performing an evaluation #
  1. Go to `./align` and build the alignment tool using make
  1. Put the reference files, show by show, in a directory (e.g. `ref/`) with a specific file extension (e.g. .ref)
  1. Run the ASR system, sentence segmenter, dependency parser and SRL system
  1. Put the output files, show by show, in a directory (e.g. `hyp/`) with a specific file extension (e.g. .hyp)
  1. Run the evaluation script:

```
$ python eval.py ref/ hyp/ .ref .hyp

Syntactic labeled attachments:    r=  67.27  p=  69.34  f=  68.29
          unlabeled attachments:  r=  70.48  p=  72.65  f=  71.55
          labels:                 r=  72.42  p=  74.65  f=  73.52
          lexicalized:            r=  64.94  p=  66.94  f=  65.93
          exact sentences:        r=   9.68  p=  11.24  f=  10.40
          unordered:              r=  67.71  p=  69.80  f=  68.74
Semantic  labeled arcs:           r=  63.41  p=  65.07  f=  64.23
          unlabeled arcs:         r=  71.04  p=  72.91  f=  71.96
          lexicalized:            r=  61.49  p=  63.10  f=  62.28
          predicates:             r=  87.94  p=  87.49  f=  87.72
          propositions:           r=  25.12  p=  24.99  f=  25.06
          exact sentences:        r=  21.25  p=  24.66  f=  22.83
          unordered:              r=  65.01  p=  66.72  f=  65.86
Overall   macro labeled (0.5):    r=  65.34  p=  67.21  f=  66.26
          macro unlabeled (0.5):  r=  70.76  p=  72.78  f=  71.76
          micro labeled:          r=  65.98  p=  67.91  f=  66.93
          micro unlabeled:        r=  70.67  p=  72.74  f=  71.69
Word error rate:                   16.01 %
Sentence boundaries:              r=  48.53  p=  56.33  f=  52.14
Part-of-speech tags:              r=  83.89  p=  86.48  f=  85.17
```

# Significance testing #

If you have two system outputs, in `ref1/` and `ref2/`, the significance script gives you the difference (hyp1 - hyp2) and the p-value using [stratified shuffling](http://www.cis.upenn.edu/~dbikel/software.html#comparator) (10000 iterations).
```
$python significance.py ref/ hyp1/ hyp2/ .ref .hyp .hyp

Syntactic labeled attachments:     diff=    -0.85 p-value= 0.0386  yes <5%
          unlabeled attachments:   diff=    -0.71 p-value= 0.0847  no
Semantic  labeled attachments:     diff=   -13.47 p-value= 0.0001  yes <1%
          unlabeled attachments:   diff=    -4.87 p-value= 0.0001  yes <1%
          predicates:              diff=    -5.18 p-value= 0.0001  yes <1%
Word error rate:                   diff=     0.00 p-value=      1  no
Sentence boundaries:               diff=     0.00 p-value=      1  no
Part-of-speech tags:               diff=    -0.13 p-value=  0.318  no
```

Note that the "unaligned" (bag-of-relation) metric is not included because its implementation is very slow (each compuation has to be repeated 10k times).