import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (mean_absolute_error, accuracy_score, r2_score, f1_score, roc_auc_score)
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import GRU, Dense, Dropout, Input
from tensorflow.keras.optimizers import Adam

df = pd.read_csv("btcusd_1-min_data.csv")
df = df.tail(80000).copy() 

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
X_raw = df[features].values
y_reg_raw = df['target_return'].values
y_clf_raw = df['target_up'].values

plt.figure(figsize=(10, 8))
sns.heatmap(df[features + ['target_return']].corr(), annot=True, cmap='coolwarm', fmt=".2f")
plt.title("Correlation Heatmap: Features vs Target Return")
plt.show()

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_raw)

def create_sequences(X, y_r, y_c, window=20):
    Xs, yr, yc = [], [], []
    for i in range(window, len(X)):
        Xs.append(X[i-window:i])
        yr.append(y_r[i])
        yc.append(y_c[i])
    return np.array(Xs), np.array(yr), np.array(yc)

WINDOW = 20
X_seq, y_reg_seq, y_clf_seq = create_sequences(X_scaled, y_reg_raw, y_clf_raw, WINDOW)

split = int(0.8 * len(X_seq))
X_train, X_test = X_seq[:split], X_seq[split:]
y_train_reg, y_test_reg = y_reg_seq[:split], y_reg_seq[split:]
y_train_clf, y_test_clf = y_clf_seq[:split], y_clf_seq[split:]

def build_model(output_type='reg'):
    model = Sequential([
        Input(shape=(WINDOW, len(features))),
        GRU(32), 
        Dropout(0.1),
        Dense(1, activation='linear' if output_type=='reg' else 'sigmoid')
    ])
    model.compile(optimizer=Adam(learning_rate=0.001), 
                  loss='mae' if output_type=='reg' else 'binary_crossentropy')
    return model

print("Training Models...")
reg_model = build_model('reg')
reg_model.fit(X_train, y_train_reg, epochs=5, batch_size=512, verbose=0)

clf_model = build_model('clf')
clf_model.fit(X_train, y_train_clf, epochs=5, batch_size=512, verbose=0)

pred_reg = reg_model.predict(X_test, batch_size=1024, verbose=0).flatten()
pred_clf_probs = clf_model.predict(X_test, batch_size=1024, verbose=0).flatten()
pred_clf = (pred_clf_probs > 0.5).astype(int)

print(f"\n--- GRU MODEL EVALUATION ---")
print(f"MAE (Regression): {mean_absolute_error(y_test_reg, pred_reg):.6f}")
print(f"R2 Score: {r2_score(y_test_reg, pred_reg):.6f}")
print(f"Accuracy (Classification): {accuracy_score(y_test_clf, pred_clf):.4f}")
print(f"F1 Score: {f1_score(y_test_clf, pred_clf):.4f}")
print(f"ROC AUC Score: {roc_auc_score(y_test_clf, pred_clf_probs):.4f}")

print("\nAnalyzing Feature Importance (XAI)...")
subset_size = 500 
baseline_acc = accuracy_score(y_test_clf[:subset_size], (clf_model.predict(X_test[:subset_size], verbose=0).flatten() > 0.5).astype(int))

importances = []
for i in range(len(features)):
    X_temp = X_test[:subset_size].copy()
    X_temp[:, :, i] = np.random.permutation(X_temp[:, :, i]) 
    perm_acc = accuracy_score(y_test_clf[:subset_size], (clf_model.predict(X_temp, verbose=0).flatten() > 0.5).astype(int))
    importances.append(baseline_acc - perm_acc)

plt.figure(figsize=(10, 6))
plt.barh(features, importances, color='skyblue')
plt.title("Explainable AI: Feature Importance (GRU Permutation)")
plt.xlabel("Decrease in Accuracy")
plt.show()

print("\nExample next-minute prediction:")
print(f"Real return: {y_test_reg[-1]:.6f} | Predicted: {pred_reg[-1]:.6f}")
print(f"Real direction: {y_test_clf[-1]} | Predicted: {pred_clf[-1]}")