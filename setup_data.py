"""
Run this once to generate all datasets and train all models.
Place in your blockchain_project_1 folder and run:
    python setup_data.py
"""
import os, pickle
import pandas as pd
import numpy as np
from sklearn.datasets import load_iris, load_wine, load_breast_cancer, load_diabetes, fetch_california_housing
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, GradientBoostingRegressor, RandomForestRegressor
from sklearn.svm import SVC, SVR
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, r2_score, mean_squared_error

os.makedirs("datasets", exist_ok=True)
os.makedirs("models",   exist_ok=True)

# ── CLASSIFICATION ────────────────────────────────────────────────────────────
print("=" * 55)
print("CLASSIFICATION DATASETS & MODELS")
print("=" * 55)

cls_loaders = {
    "iris":          load_iris(),
    "wine":          load_wine(),
    "breast_cancer": load_breast_cancer(),
}

cls_models = {
    "rf":  RandomForestClassifier(n_estimators=100, random_state=42),
    "svm": SVC(kernel="rbf", random_state=42, probability=True),
    "gb":  GradientBoostingClassifier(n_estimators=50, random_state=42),
}

for name, bunch in cls_loaders.items():
    df = pd.DataFrame(bunch.data, columns=bunch.feature_names)
    df["target"] = bunch.target
    train_df = df.sample(frac=0.8, random_state=42)
    test_df  = df.drop(train_df.index)
    train_df.to_csv(f"datasets/{name}.csv",      index=False)
    test_df.to_csv( f"datasets/{name}_test.csv", index=False)
    print(f"\n  {name}: train={len(train_df)} rows, test={len(test_df)} rows")

    X = train_df.iloc[:, :-1].values
    y = train_df.iloc[:, -1].values
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)

    for mname, model in cls_models.items():
        m = type(model)(**model.get_params())
        m.fit(X_tr, y_tr)
        acc = accuracy_score(y_te, m.predict(X_te))
        out = f"models/{name}_{mname}.pkl"
        with open(out, "wb") as f: pickle.dump(m, f)
        print(f"    {mname.upper():<5} accuracy={acc:.4f}  →  {out}")

# ── REGRESSION ────────────────────────────────────────────────────────────────
print()
print("=" * 55)
print("REGRESSION DATASETS & MODELS")
print("=" * 55)

# Diabetes dataset (442 samples, 10 features, predicts disease progression)
diabetes = load_diabetes()
df_diab = pd.DataFrame(diabetes.data, columns=diabetes.feature_names)
df_diab["target"] = diabetes.target
train_diab = df_diab.sample(frac=0.8, random_state=42)
test_diab  = df_diab.drop(train_diab.index)
train_diab.to_csv("datasets/diabetes.csv",      index=False)
test_diab.to_csv( "datasets/diabetes_test.csv", index=False)
print(f"\n  diabetes: train={len(train_diab)} rows, test={len(test_diab)} rows")
print("  Target: disease progression score (continuous)")

# California Housing (20640 samples — use a 2000-row sample to keep it fast)
try:
    housing = fetch_california_housing()
    df_house = pd.DataFrame(housing.data, columns=housing.feature_names)
    df_house["target"] = housing.target
    df_house = df_house.sample(n=2000, random_state=42).reset_index(drop=True)
    train_house = df_house.sample(frac=0.8, random_state=42)
    test_house  = df_house.drop(train_house.index)
    train_house.to_csv("datasets/housing.csv",      index=False)
    test_house.to_csv( "datasets/housing_test.csv", index=False)
    print(f"\n  housing: train={len(train_house)} rows, test={len(test_house)} rows")
    print("  Target: median house price")
    has_housing = True
except Exception as e:
    print(f"  housing: skipped ({e})")
    has_housing = False

reg_models = {
    "rf_reg":  RandomForestRegressor(n_estimators=100, random_state=42),
    "gb_reg":  GradientBoostingRegressor(n_estimators=50, random_state=42),
    "svr":     SVR(kernel="rbf"),
}

reg_datasets = {"diabetes": ("datasets/diabetes.csv", train_diab)}
if has_housing:
    reg_datasets["housing"] = ("datasets/housing.csv", train_house)

for name, (dpath, train_df) in reg_datasets.items():
    print(f"\n  --- {name} ---")
    X = train_df.iloc[:, :-1].values
    y = train_df.iloc[:, -1].values
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)

    for mname, model in reg_models.items():
        m = type(model)(**model.get_params())
        m.fit(X_tr, y_tr)
        preds = m.predict(X_te)
        r2   = r2_score(y_te, preds)
        rmse = np.sqrt(mean_squared_error(y_te, preds))
        out  = f"models/{name}_{mname}.pkl"
        with open(out, "wb") as f: pickle.dump(m, f)
        print(f"    {mname.upper():<8} R²={r2:.4f}  RMSE={rmse:.2f}  →  {out}")

# ── SUMMARY ───────────────────────────────────────────────────────────────────
print()
print("=" * 55)
print("DONE — What to do on the website")
print("=" * 55)
print()
print("CREATE THESE CLASSIFICATION PROJECTS:")
for name in cls_loaders:
    print(f"  Project: '{name}'  task=classification")
    print(f"    Training dataset : datasets/{name}.csv")
    print(f"    Hidden test set  : datasets/{name}_test.csv")
    print(f"    Submit models    : models/{name}_rf.pkl, {name}_svm.pkl, {name}_gb.pkl")
    print()

print("CREATE THESE REGRESSION PROJECTS:")
reg_names = list(reg_datasets.keys())
for name in reg_names:
    print(f"  Project: '{name}'  task=regression")
    print(f"    Training dataset : datasets/{name}.csv")
    print(f"    Hidden test set  : datasets/{name}_test.csv")
    print(f"    Submit models    : models/{name}_rf_reg.pkl, {name}_gb_reg.pkl, {name}_svr.pkl")
    print()

print("RULE: Always match model to its project's dataset.")
