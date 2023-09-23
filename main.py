import pandas as pd
from sklearn.tree import DecisionTreeClassifier, export_graphviz
import graphviz
# import matplotlib.pyplot as plt

bank = pd.read_csv("/Users/nineleaps/Downloads/bank+marketing/bank/bank-full.csv", sep=';')
bank = pd.get_dummies(bank, drop_first=True)
bank.head()
X = bank.drop("y_yes", axis=1)
y = bank["y_yes"]
y = y.astype(str)
clf = DecisionTreeClassifier(max_depth=5, min_samples_split=1000)
clf.fit(X, y)

dot_data = export_graphviz(clf, out_file=None,
                           feature_names=X.columns,
                           class_names=['0', '1'],
                           filled=True, rounded=True,
                           special_characters=True,
                           proportion=True)
p = dot_data.split(";\n")
dic = {}

for i in p:
    index = i.find('samples')
    if index != -1:
        dic[int(i[:2])] = [i[2:].split('<br/>')[-3].split('=')[1].strip(),
                           float(i[2:].split('<br/>')[-2].split(',')[1].strip().split(']')[0].strip())]


def inorder_traversal(tree, i, node_information, node_sequence, sign):
    if i < 0:
        return
    node_sequence[i] = sign
    node_sequence_temp_left = node_sequence.copy()
    node_information[i] = (node_sequence, tree.tree_.impurity[i])
    if tree.tree_.children_left[i] >= 0:
        node_information = inorder_traversal(tree, tree.tree_.children_left[i], node_information,
                                             node_sequence_temp_left, "left")

    else:
        pass

    node_sequence_temp_right = node_sequence.copy()

    if tree.tree_.children_right[i] >= 0:
        node_information = inorder_traversal(tree, tree.tree_.children_right[i], node_information,
                                             node_sequence_temp_right, "right")
    else:
        pass

    return node_information


# Example usage:
# You need to provide the 'tree' object when calling this function
# tree = your_decision_tree_object_here
# node_info, node_seq = inorder_traversal(tree)
# print(node_info)
# print(node_seq)

node_info = inorder_traversal(tree=clf, i=0, node_information={}, node_sequence={}, sign="left")


def information_typer(node_information, tree, gini_threshold, columns, dic):
    information = []
    node_information = [y for x, y in node_information.items()]
    node_information = sorted(node_information, key=lambda x: x[1])
    for info in node_information:
        information_dic = {}
        if info[1] < gini_threshold:
            for node, sign in info[0].items():
                if (columns[clf.tree_.feature[node]], sign) not in information_dic:
                    information_dic[(columns[clf.tree_.feature[node]], sign)] = [tree.tree_.threshold[node], dic[node]]
                elif (tree.tree_.threshold[node] < information_dic[(columns[clf.tree_.feature[node]], sign)][0]) and (
                        sign == "left"):
                    information_dic[(columns[clf.tree_.feature[node]], sign)] = [tree.tree_.threshold[node], dic[node]]
                elif (tree.tree_.threshold[node] > information_dic[(columns[clf.tree_.feature[node]], sign)][0]) and (
                        sign == "right"):
                    information_dic[(columns[clf.tree_.feature[node]], sign)] = [tree.tree_.threshold[node],  dic[node]]

        information.append(information_dic)
    for info in information:
        for feature, threshold in info.items():
            if feature[0] == list(info.keys())[-1][0]:
                print(f"Having total sample size is {threshold[1][0]} and ratio of yes is {threshold[1][1]}")
                print("--------------------------------------------------------------------")
            else:
                if (threshold[0] == 0.5) and (feature[1] == "left"):
                    print(f"{feature[0]} is not True and ", end='')
                elif (threshold[0] == 0.5) and (feature[1] == "right"):
                    print(f"{feature[0]} is True and ", end='')
                elif feature[1] == "left":
                    print(f"{feature[0]} values less than {threshold[0]} and ", end='')
                elif feature[1] == "right":
                    print(f"{feature[0]} values greater than {threshold[0]} and ", end='')


information_typer(node_info, clf, 0.3, list(bank.columns), dic=dic)

graph = graphviz.Source(dot_data)
graph.render("decision_tree_fin")
