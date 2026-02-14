import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import (mean_absolute_error, accuracy_score, r2_score, f1_score, roc_auc_score)

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

plt.figure(figsize=(10, 8))
sns.heatmap(df[features + ['target_return']].corr(), annot=True, cmap='coolwarm', fmt=".2f")
plt.title("Correlation Heatmap: Features vs Target Return")
plt.show()

X_train, X_test, y_train_reg, y_test_reg = train_test_split(X, y_reg, test_size=0.2, shuffle=False)
_, _, y_train_clf, y_test_clf = train_test_split(X, y_clf, test_size=0.2, shuffle=False)

model_reg = LinearRegression().fit(X_train, y_train_reg)

model_clf = LogisticRegression(max_iter=1000).fit(X_train, y_train_clf)

pred_reg = model_reg.predict(X_test)
pred_clf = model_clf.predict(X_test)
pred_clf_probs = model_clf.predict_proba(X_test)[:, 1] 

print(f"--- LINEAR MODEL EVALUATION ---")
print(f"MAE (Regression): {mean_absolute_error(y_test_reg, pred_reg):.6f}")
print(f"R2 Score: {r2_score(y_test_reg, pred_reg):.6f}")
print(f"Accuracy (Classification): {accuracy_score(y_test_clf, pred_clf):.4f}")
print(f"F1 Score: {f1_score(y_test_clf, pred_clf):.4f}")
print(f"ROC AUC Score: {roc_auc_score(y_test_clf, pred_clf_probs):.4f}")

plt.figure(figsize=(10, 6))
importance = model_clf.coef_[0]
plt.barh(features, importance, color='salmon')
plt.title("Explainable AI: Feature Importance (Logistic Regression Coefficients)")
plt.xlabel("Coefficient Value")
plt.axvline(x=0, color='black', linestyle='--', linewidth=1)
plt.show()

print("\nExample next-minute prediction:")
print(f"Real return: {y_test_reg.values[-1]:.6f} | Predicted: {pred_reg[-1]:.6f}")
print(f"Real direction: {y_test_clf.values[-1]} | Predicted: {pred_clf[-1]}")