import sys, os

def align(array1, array2, command="./align/align"): #command='%s/align/align' % (os.path.dirname(sys.argv[0]))):
    if array1 == array2:
        return zip([x.split() for x in array1], [x.split() for x in array2])
    if "HOSTNAME" not in os.environ:
        os.environ["HOSTNAME"] = "localhost"
    tmp = "tmp_align.%d.%s" % (os.getpid(), os.environ["HOSTNAME"])
    file1 = open(tmp + ".1", "w")
    for value in array1:
        file1.write(str(value) + '\n')
    file1.close()
    file2 = open(tmp + ".2", "w")
    for value in array2:
        file2.write(str(value) + '\n')
    file2.close()
    aligned = os.popen('%s %s.1 %s.2' % (command, tmp, tmp))
    num = 0
    output = []
    left = None
    right = None
    for line in aligned:
        tokens = line.strip().split()
        if num % 2 == 0:
            if len(tokens) > 1:
                left = tokens[1:]
            else:
                left = None
        else:
            if len(tokens) > 1:
                right = tokens[1:]
            else:
                right = None
            output.append((left, right))
        #print line.strip()
        num += 1
    aligned.close()
    os.unlink(tmp + ".1")
    os.unlink(tmp + ".2")
    return output

if __name__ == "__main__":
    alignment = align([1,2,3,4,5,6,7,8,9], [1,2,2,3,4,5,5,5,5,5,5,6,7,8])
    print alignment
