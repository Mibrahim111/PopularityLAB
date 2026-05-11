import joblib
import logging
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix, classification_report
from classification import engineer_features

classification_dir = Path("ml/artifacts/classification")

classification_preprocessor_path = classification_dir / "preprocessor.pkl"
classification_label_encoder_path = classification_dir / "label_encoder.pkl"
classification_model_path = classification_dir / "stacking_clf.pkl"

data_path = Path("test_data_class.csv")

preprocessor = joblib.load(classification_preprocessor_path)
label_encoder = joblib.load(classification_label_encoder_path)
model = joblib.load(classification_model_path)

df = pd.read_csv(data_path)

df_engineered = engineer_features(df)

TARGET_COLUMN = "GamePopularity"
y_true = None
if TARGET_COLUMN in df_engineered.columns:
    y_true = df_engineered[TARGET_COLUMN].copy()
    df_engineered = df_engineered.drop(columns=[TARGET_COLUMN], errors='ignore')
else:
    print("NO TARGET COLUMN")





X_test_transformed = preprocessor.transform(df_engineered)

y_pred_encoded = model.predict(X_test_transformed)
y_pred = label_encoder.inverse_transform(y_pred_encoded)



if y_true is not None:
    y_true_encoded = label_encoder.transform(y_true)
    
    accuracy = accuracy_score(y_true, y_pred)
    macro_f1 = f1_score(y_true, y_pred, average='macro', zero_division=0)
    weighted_f1 = f1_score(y_true, y_pred, average='weighted', zero_division=0)
    
    
    
    print("\n" + "=" * 60)
    print("CLASSIFICATION TEST RESULTS")
    print("=" * 60) 
    print(f"Accuracy: {accuracy:.4f}")
    print(f"Macro F1 Score: {macro_f1:.4f}")
    print(f"Weighted F1 Score: {weighted_f1:.4f}")
    print("Classification Report:")
    print(classification_report(y_true, y_pred))

else:
    print("ERROR NO Y_TRUE")