# lime_run.py

import pandas as pd
import joblib
from lime.lime_tabular import LimeTabularExplainer
from sklearn.pipeline import Pipeline
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ----------------------------------------------------
# CONFIG
# ----------------------------------------------------
PIPE_PATH = os.path.join(BASE_DIR, "preproc_pipeline.joblib")
DATA_PATH = os.path.join(BASE_DIR, "loan_approval.csv")

NUMERIC_FEATURES = ["income", "credit_score", "loan_amount", "years_employed", "points"]

# ----------------------------------------------------
# BUILD LIME EXPLAINER
# ----------------------------------------------------
def build_lime_explainer(df: pd.DataFrame) -> LimeTabularExplainer:
    return LimeTabularExplainer(
        training_data=df[NUMERIC_FEATURES].values,
        feature_names=NUMERIC_FEATURES,
        class_names=["Rejected", "Approved"],
        mode="classification",
        random_state=42
    )

# ----------------------------------------------------
# EXPLAIN ONE INSTANCE WITH LIME
# ----------------------------------------------------
def explain_instance_lime(
    pipe: Pipeline,
    lime_exp: LimeTabularExplainer,
    instance: pd.DataFrame
):
    """
    Returns LIME feature contributions as a dict:
    {feature: contribution weight}
    """
    def predict_fn(x):
        df_x = pd.DataFrame(x, columns=NUMERIC_FEATURES)
        return pipe.predict_proba(df_x)

    explanation = lime_exp.explain_instance(
        data_row=instance[NUMERIC_FEATURES].iloc[0].values,
        predict_fn=predict_fn,
        num_features=len(NUMERIC_FEATURES)
    )

    result = {}
    for feature_condition, weight in explanation.as_list():
        clean_feat = feature_condition.split()[0]
        result[clean_feat] = float(weight)

    return result

# ----------------------------------------------------
# MAIN
# ----------------------------------------------------
if __name__ == "__main__":
    print("Loading model and data...")

    pipe = joblib.load(PIPE_PATH)
    df = pd.read_csv(DATA_PATH)

    lime_exp = build_lime_explainer(df)

    # choose row to explain
    idx = 0
    row = df.iloc[[idx]]   # keep as DataFrame

    # generate explanation
    print(f"\nRunning LIME on row index {idx}...")
    lime_result = explain_instance_lime(pipe, lime_exp, row)

    print("\nLIME Feature Contributions:")
    for feat, val in sorted(lime_result.items(), key=lambda x: -abs(x[1])):
        print(f"  - {feat}: {val:.4f}")
