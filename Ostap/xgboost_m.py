import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import (mean_absolute_error, accuracy_score, r2_score, f1_score, roc_auc_score, confusion_matrix)
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

plt.figure(figsize=(12, 8))

corr_data = df[features + ['target_return']].corr()
sns.heatmap(corr_data, annot=True, cmap='coolwarm', fmt=".2f")
plt.title("Heatmap of Features with Target Return")
plt.savefig("correlation_heatmap.png")
plt.show()

X_train, X_test, y_train_reg, y_test_reg = train_test_split(X, y_reg, test_size=0.2, shuffle=False)
_, _, y_train_clf, y_test_clf = train_test_split(X, y_clf, test_size=0.2, shuffle=False)


"""
param_grid = {
    'max_depth': [4, 6],
    'learning_rate': [0.05, 0.1],
    'n_estimators': [100, 150]
}
grid_clf = GridSearchCV(XGBClassifier(use_label_encoder=False, eval_metric='logloss'), 
                        param_grid, cv=3, scoring='accuracy')
grid_clf.fit(X_train, y_train_clf)
clf_model = grid_clf.best_estimator_
print(f"Best Params: {grid_clf.best_params_}")
"""

reg_model = XGBRegressor(n_estimators=200, learning_rate=0.05, max_depth=6, subsample=0.8).fit(X_train, y_train_reg)
clf_model = XGBClassifier(n_estimators=150, learning_rate=0.1, max_depth=6, subsample=0.8).fit(X_train, y_train_clf)

pred_reg = reg_model.predict(X_test)
pred_clf = clf_model.predict(X_test)
pred_proba = clf_model.predict_proba(X_test)[:, 1] 

mae = mean_absolute_error(y_test_reg, pred_reg)
r2 = r2_score(y_test_reg, pred_reg)
acc = accuracy_score(y_test_clf, pred_clf)
f1 = f1_score(y_test_clf, pred_clf)
auc = roc_auc_score(y_test_clf, pred_proba)

print(f"--- REGRESSION ---")
print(f"MAE: {mae:.6f}")
print(f"R2 Score: {r2:.6f}")

print(f"\n--- CLASSIFICATION ---")
print(f"Accuracy: {acc:.4f}")
print(f"F1-Score: {f1:.4f}")
print(f"Area Under the Curve (AUC): {auc:.4f}")

plt.figure(figsize=(10, 6))
importances = clf_model.feature_importances_
indices = np.argsort(importances)
plt.title('Explainable AI: Feature Importances (XGBoost)')
plt.barh(range(len(indices)), importances[indices], color='b', align='center')
plt.yticks(range(len(indices)), [features[i] for i in indices])
plt.xlabel('Relative Importance')
plt.savefig("feature_importance.png")
plt.show()

print("\nExample next-minute prediction:")
print(f"Real return: {y_test_reg.values[-1]:.6f} | Predicted: {pred_reg[-1]:.6f}")
print(f"Real direction: {y_test_clf.values[-1]} | Predicted: {pred_clf[-1]}")