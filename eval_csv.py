import sys, eval

if __name__ == '__main__':
    if len(sys.argv) == 5:
        eval.recursive(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], csv=True)
    elif len(sys.argv) == 3:
        stats = eval.compare_with_alignment(sys.argv[1], sys.argv[2])
        stats.csv_headers()
        stats.output_csv("TOTAL")
    else:
        sys.stderr.write('USAGE: %s <ref_dir> <hyp_dir> <ref_ext> <hyp_ext>\n' % sys.argv[0])
        sys.exit(1)
