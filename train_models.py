import os
import pickle

import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC


DATASETS = {
    "iris": "datasets/iris.csv",
    "wine": "datasets/wine.csv",
    "breast_cancer": "datasets/breast_cancer.csv",
}

MODELS = {
    "rf": RandomForestClassifier(n_estimators=100, random_state=42),
    "svm": SVC(kernel="rbf", random_state=42),
    "gb": GradientBoostingClassifier(n_estimators=50, random_state=42),
}

OUTPUT_DIR = "models"
os.makedirs(OUTPUT_DIR, exist_ok=True)


for dataset_name, dataset_path in DATASETS.items():
    print(f"\n--- Training on {dataset_name} ---")
    df = pd.read_csv(dataset_path)
    X = df.iloc[:, :-1].values
    y = df.iloc[:, -1].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    for model_name, model in MODELS.items():
        model.fit(X_train, y_train)
        accuracy = accuracy_score(y_test, model.predict(X_test))
        output_path = os.path.join(OUTPUT_DIR, f"{dataset_name}_{model_name}.pkl")

        with open(output_path, "wb") as model_file:
            pickle.dump(model, model_file)

        print(f"{model_name.upper()} accuracy: {accuracy:.4f} -> saved to {output_path}")


print("\nAll 9 models saved in the models folder.")
