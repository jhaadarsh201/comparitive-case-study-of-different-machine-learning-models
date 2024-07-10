# -*- coding: utf-8 -*-
"""EXP_5.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/13r86rOJnmENV705-JglWd1Hlwpqpvlpu
"""

!pip install ucimlrepo

!pip install dtreeviz

from ucimlrepo import fetch_ucirepo

# fetch dataset
heart_disease = fetch_ucirepo(id=45)

# data (as pandas dataframes)
X = heart_disease.data.features
y = heart_disease.data.targets

# metadata
print(heart_disease.metadata)

# variable information
print(heart_disease.variables)

X

y

!pip install missingno

import missingno as msno

msno.matrix(X)

for col in X:
  print(f"unique entries in {col} are: \n{X[col].value_counts()}")
  print("**************************")



"""# ID3"""

import pandas as pd
import numpy as np

class Node:
    def __init__(self, feature=None, split_value=None, label=None):
        self.feature = feature
        self.split_value = split_value
        self.label = label
        self.children = {}

def entropy(labels):
    unique_labels, counts = np.unique(labels, return_counts=True)
    probabilities = counts / len(labels)
    entropy = -np.sum(probabilities * np.log2(probabilities))
    return entropy

def information_gain(data, feature, target):
    total_entropy = entropy(data[target])
    values, counts = np.unique(data[feature], return_counts=True)
    weighted_entropy = np.sum([(counts[i] / np.sum(counts)) * entropy(data.where(data[feature]==values[i]).dropna()[target]) for i in range(len(values))])
    information_gain = total_entropy - weighted_entropy
    return information_gain

def id3(data, original_data, features, target):
    if len(np.unique(data[target])) == 1:
        return Node(label=np.unique(data[target])[0])

    if len(features) == 0:
        return Node(label=np.unique(data[target]).max())

    information_gains = [information_gain(data, feature, target) for feature in features]
    best_feature_index = np.argmax(information_gains)
    best_feature = features[best_feature_index]

    tree = Node(feature=best_feature)

    features = [f for f in features if f != best_feature]

    for value in np.unique(data[best_feature]):
        subset = data.where(data[best_feature] == value).dropna()
        subtree = id3(subset, original_data, features, target)
        tree.children[value] = subtree

    return tree

def predict(node, sample):
    if node.label is not None:
        return node.label
    else:
        value = sample[node.feature]
        if value in node.children:
            return predict(node.children[value], sample)
        else:
            return None

def print_tree(node, depth=0):
    if node.label is not None:
        print('    ' * depth, 'Predict:', node.label)
    else:
        print('    ' * depth, '|__ ', node.feature)
        for value, child_node in node.children.items():
            if len(node.children) == 2:
                if value == list(node.children.keys())[0]:
                    branch_symbol = "├── "
                else:
                    branch_symbol = "└── "
            else:
                branch_symbol = "|-- "
            print('    ' * (depth + 1), branch_symbol, value)
            print_tree(child_node, depth + 1)

df = heart_disease.data.original

target = 'num'
features = [col for col in df.columns if col != target]


ID3_tree = id3(df, df, features, target)
print_tree(ID3_tree)

def calculate_metrics(tree, data, target):
    correct_predictions = 0
    true_positives = 0
    false_positives = 0
    true_negatives = 0
    false_negatives = 0

    for _, sample in data.iterrows():
        predicted_label = predict(tree, sample)
        actual_label = sample[target]

        if predicted_label == actual_label:
            correct_predictions += 1
            if predicted_label == 1:
                true_positives += 1
            else:
                true_negatives += 1
        else:
            if predicted_label == 1:
                false_positives += 1
            else:
                false_negatives += 1

    accuracy = correct_predictions / len(data)
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) != 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) != 0 else 0
    sensitivity = recall  # Sensitivity is another name for recall

    return accuracy, precision, recall, sensitivity

res = calculate_metrics(ID3_tree,df,'num')
print(
    'Metrics for ID3: \n'
    'Accuracy: ' + str(res[0]) + '\n'
    'Precision: ' + str(res[1]) + '\n'
    'Recall: ' + str(res[2]) + '\n'
    'sensitivity: ' + str(res[3]) + '\n'
)

"""# C4.5"""

import pandas as pd
import numpy as np

class Node:
    def __init__(self, feature=None, split_value=None, label=None):
        self.feature = feature
        self.split_value = split_value
        self.label = label
        self.children = {}

def entropy(labels):
    unique_labels, counts = np.unique(labels, return_counts=True)
    probabilities = counts / len(labels)
    entropy = -np.sum(probabilities * np.log2(probabilities))
    return entropy

def information_gain_ratio(data, feature, target):
    total_entropy = entropy(data[target])
    values, counts = np.unique(data[feature], return_counts=True)
    weighted_entropy = np.sum([(counts[i] / np.sum(counts)) * entropy(data.where(data[feature]==values[i]).dropna()[target]) for i in range(len(values))])
    information_gain = total_entropy - weighted_entropy
    split_info = entropy(data[feature])
    if split_info == 0:  # Avoid division by zero
        split_info = 1
    gain_ratio = information_gain / split_info
    return gain_ratio

def bin_numerical_feature(data, feature, bins):
    data[feature] = pd.cut(data[feature], bins=bins, labels=False)
    return data

def c45(data, original_data, features, target, numerical_features=None, bin_size=5):

    if len(np.unique(data[target])) == 1:
        return Node(label=np.unique(data[target])[0])

    if len(features) == 0:
        return Node(label=np.unique(data[target]).max())

    if numerical_features:
        for feature in numerical_features:
            data = bin_numerical_feature(data, feature, bin_size)

    gain_ratios = [information_gain_ratio(data, feature, target) for feature in features]
    best_feature_index = np.argmax(gain_ratios)
    best_feature = features[best_feature_index]

    tree = Node(feature=best_feature)

    features = [f for f in features if f != best_feature]

    for value in np.unique(data[best_feature]):

        subset = data.where(data[best_feature] == value).dropna()

        subtree = c45(subset, original_data, features, target, numerical_features=numerical_features, bin_size=bin_size)

        tree.children[value] = subtree

    return tree

def predict(node, sample):
    if node.label is not None:
        return node.label
    else:
        value = sample[node.feature]
        if value in node.children:
            return predict(node.children[value], sample)
        else:
            return None

def print_tree(node, depth=0):
    if node.label is not None:
        print('  ' * depth, 'Predict:', node.label)
    else:
        print('  ' * depth, node.feature)
        for value, child_node in node.children.items():
            print('  ' * (depth+1), value)
            print_tree(child_node, depth + 2)

target = 'num'
features = [col for col in df.columns if col != target]


C45_tree = c45(df, df, features, target)
print_tree(C45_tree)

res = calculate_metrics(C45_tree,df,'num')

print(
    'Metrics for C4.5: \n'
    'Accuracy: ' + str(res[0]) + '\n'
    'Precision: ' + str(res[1]) + '\n'
    'Recall: ' + str(res[2]) + '\n'
    'sensitivity: ' + str(res[3]) + '\n'
)

"""## CART"""

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score

data = df.dropna()
# Assuming the last column is the target variable, and rest are features
X = data.iloc[:, :-1]  # Features
y = data.iloc[:, -1]   # Target variable

# Split dataset into training set and test set
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Create Decision Tree classifer object
clf = DecisionTreeClassifier()

# Train Decision Tree Classifer
clf = clf.fit(X_train,y_train)

# Predict the response for test dataset
y_pred = clf.predict(X_test)

from sklearn.metrics import accuracy_score, precision_score, recall_score

y_train_pred = clf.predict(X_train)

accuracy_train = accuracy_score(y_train, y_train_pred)
precision_train = precision_score(y_train, y_train_pred, average='weighted')
recall_train = recall_score(y_train, y_train_pred, average='weighted')

print("Metrics on C4.5:")
print("Accuracy:", accuracy_train)
print("Precision:", precision_train)
print("Recall:", recall_train)

