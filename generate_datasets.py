# generate_datasets.py
import pandas as pd
from sklearn.datasets import load_iris, load_wine, load_breast_cancer

# Dataset 1 — Iris (flower classification, 150 rows)
iris = load_iris()
df = pd.DataFrame(iris.data, columns=iris.feature_names)
df['target'] = iris.target
df.to_csv('iris.csv', index=False)
print("iris.csv saved")

# Dataset 2 — Wine (wine type classification, 178 rows)
wine = load_wine()
df = pd.DataFrame(wine.data, columns=wine.feature_names)
df['target'] = wine.target
df.to_csv('wine.csv', index=False)
print("wine.csv saved")

# Dataset 3 — Breast Cancer (medical, 569 rows)
bc = load_breast_cancer()
df = pd.DataFrame(bc.data, columns=bc.feature_names)
df['target'] = bc.target
df.to_csv('breast_cancer.csv', index=False)
print("breast_cancer.csv saved")
