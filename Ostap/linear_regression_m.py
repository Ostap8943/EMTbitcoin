import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import mean_absolute_error, accuracy_score

df = pd.read_csv("btcusd_1-min_data.csv")
df = df.tail(100000).copy() 

df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='s')
df = df.sort_values('Timestamp').reset_index(drop=True)

df['return'] = df['Close'].pct_change()
df['volatility_10'] = df['return'].rolling(10).std()
df['sma_10'] = df['Close'].rolling(10).mean()
df['hour'] = df['Timestamp'].dt.hour
df['dayofweek'] = df['Timestamp'].dt.dayofweek

df['target_return'] = df['return'].shift(-1)
df['target_up'] = (df['target_return'] > 0).astype(int)
df = df.dropna()

features = ['Close', 'return', 'volatility_10', 'sma_10', 'hour', 'dayofweek']
X = df[features]
y_reg = df['target_return']
y_clf = df['target_up']

X_train, X_test, y_train_reg, y_test_reg = train_test_split(X, y_reg, test_size=0.2, shuffle=False)
_, _, y_train_clf, y_test_clf = train_test_split(X, y_clf, test_size=0.2, shuffle=False)

model_reg = LinearRegression().fit(X_train, y_train_reg)
model_clf = LogisticRegression().fit(X_train, y_train_clf)

pred_reg = model_reg.predict(X_test)
pred_clf = model_clf.predict(X_test)

print(f"MAE (Next return prediction): {mean_absolute_error(y_test_reg, pred_reg):.6f}")
print(f"Accuracy (Up/Down prediction): {accuracy_score(y_test_clf, pred_clf):.4f}")

print("\nExample next-minute prediction:")
print(f"Real return next minute: {y_test_reg.values[-1]:.6f}")
print(f"Predicted return next minute: {pred_reg[-1]:.6f}")

print(f"\nReal direction: {y_test_clf.values[-1]}")
print(f"Predicted direction: {pred_clf[-1]}")