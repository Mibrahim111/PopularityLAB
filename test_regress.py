import joblib
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from classification import engineer_features


regression_dir = Path("ml/artifacts/regression")

regression_model_path = regression_dir / "stacking_reg.pkl"
regression_preprocessor_path = regression_dir / "reg_preprocessor.pkl"

data_path = Path("test_data_reg.csv")

regression_preprocessor = joblib.load(regression_preprocessor_path)
stacking_reg = joblib.load(regression_model_path)

df = pd.read_csv(data_path)



df_engineered = engineer_features(df)

TARGET_COLUMN = "RecommendationCount"
y_true = None
if TARGET_COLUMN in df_engineered.columns:
    y_true = df_engineered[TARGET_COLUMN].copy()
    df_engineered = df_engineered.drop(columns=[TARGET_COLUMN], errors='ignore')
else:
    print("NO TARGET")


X_test_transformed = regression_preprocessor.transform(df_engineered)

y_pred = stacking_reg.predict(X_test_transformed)


if y_true is not None:
    mse = mean_squared_error(y_true, y_pred)
    rmse = np.sqrt(mse)
    mae = mean_absolute_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    
    
    print("\n" + "=" * 60)
    print("REGRESSION TEST RESULTS")
    print("=" * 60)
    print(f"Mean Squared Error (MSE): {mse:.4f}")
    print(f"Root Mean Squared Error (RMSE): {rmse:.4f}")
    print(f"Mean Absolute Error (MAE): {mae:.4f}")
    print(f"R² Score: {r2:.4f}")
    print("=" * 60)
else:
    print("NO Y_TRUE")