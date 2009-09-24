import treenode, utils
import sys

for tree in treenode.TreeNode.readAllTrees(sys.stdin):
    utils.asrify(tree)
    for node in tree:
        node.text = node.text.lower()
    print tree
