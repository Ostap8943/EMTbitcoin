import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, accuracy_score
from xgboost import XGBRegressor, XGBClassifier

df = pd.read_csv("btcusd_1-min_data.csv")  
df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='s')
df = df.sort_values('Timestamp').reset_index(drop=True)

df['lag1'] = df['Close'].shift(1)
df['lag5'] = df['Close'].shift(5)
df['lag10'] = df['Close'].shift(10)

df['return'] = df['Close'].pct_change()
df['volatility_10'] = df['return'].rolling(10).std()

df['sma_5'] = df['Close'].rolling(5).mean()
df['sma_10'] = df['Close'].rolling(10).mean()
df['sma_20'] = df['Close'].rolling(20).mean()

df['hour'] = df['Timestamp'].dt.hour
df['dayofweek'] = df['Timestamp'].dt.dayofweek

df = df.dropna()

df['target_return'] = df['return'].shift(-1) 

df['target_up'] = (df['target_return'] > 0).astype(int)

df = df.dropna()

features = [
    'lag1', 'lag5', 'lag10',
    'return', 'volatility_10',
    'sma_5', 'sma_10', 'sma_20',
    'hour', 'dayofweek'
]

X = df[features]
y_reg = df['target_return']  
y_clf = df['target_up']      

X_train, X_test, y_train_reg, y_test_reg = train_test_split(X, y_reg, test_size=0.2, shuffle=False)
_, _, y_train_clf, y_test_clf = train_test_split(X, y_clf, test_size=0.2, shuffle=False)

reg_model = XGBRegressor(
    n_estimators=200,
    learning_rate=0.05,
    max_depth=6,
    subsample=0.8,
    objective='reg:squarederror'
)
reg_model.fit(X_train, y_train_reg)

clf_model = XGBClassifier(
    n_estimators=150,
    learning_rate=0.1,
    max_depth=6,
    subsample=0.8
)
clf_model.fit(X_train, y_train_clf)

pred_reg = reg_model.predict(X_test)
mae = mean_absolute_error(y_test_reg, pred_reg)

print(f"MAE (Next return prediction): {mae:.6f}")

pred_clf = clf_model.predict(X_test)
acc = accuracy_score(y_test_clf, pred_clf)
print(f"Accuracy (Up/Down prediction): {acc:.4f}")

print("\nExample next-minute prediction:")
print(f"Real return next minute: {y_test_reg.values[-1]:.6f}")
print(f"Predicted return next minute: {pred_reg[-1]:.6f}")

print(f"\nReal direction: {y_test_clf.values[-1]}")
print(f"Predicted direction: {pred_clf[-1]}")
