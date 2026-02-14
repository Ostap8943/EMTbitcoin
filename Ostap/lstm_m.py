import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import (mean_absolute_error, accuracy_score, r2_score, f1_score, roc_auc_score)
from sklearn.inspection import permutation_importance
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, Input
from tensorflow.keras.optimizers import Adam

df = pd.read_csv("btcusd_1-min_data.csv")
df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='s')
df = df.sort_values('Timestamp').reset_index(drop=True)

df = df.tail(50000).copy()

df['return'] = df['Close'].pct_change()
df['lag1'] = df['Close'].shift(1)
df['lag5'] = df['Close'].shift(5)
df['lag10'] = df['Close'].shift(10)
df['volatility_10'] = df['return'].rolling(10).std()
df['sma_5'] = df['Close'].rolling(5).mean()
df['sma_10'] = df['Close'].rolling(10).mean()
df['sma_20'] = df['Close'].rolling(20).mean()
df['hour'] = df['Timestamp'].dt.hour
df['dayofweek'] = df['Timestamp'].dt.dayofweek

df['target_return'] = df['return'].shift(-1)
df['target_up'] = (df['target_return'] > 0).astype(int)
df = df.dropna()

features = ['lag1', 'lag5', 'lag10', 'return', 'volatility_10', 'sma_5', 'sma_10', 'sma_20', 'hour', 'dayofweek']
X_raw = df[features].values
y_reg_raw = df['target_return'].values
y_clf_raw = df['target_up'].values

plt.figure(figsize=(12, 10))
sns.heatmap(df[features + ['target_return']].corr(), annot=True, cmap='coolwarm', fmt=".2f")
plt.title("Correlation Heatmap: Features vs Target Return")
plt.savefig("lstm_heatmap.png")
plt.show()

scaler = MinMaxScaler()
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

def build_lstm(output_type='reg'):
    model = Sequential([
        Input(shape=(WINDOW, len(features))),
        LSTM(64, return_sequences=True),
        Dropout(0.2),
        LSTM(32),
        Dropout(0.2),
        Dense(1, activation='linear' if output_type=='reg' else 'sigmoid')
    ])
    opt = Adam(learning_rate=0.001)
    loss = 'mae' if output_type=='reg' else 'binary_crossentropy'
    model.compile(optimizer=opt, loss=loss, metrics=['accuracy'] if output_type=='clf' else [])
    return model

print("Training LSTM Regression model...")
reg_model = build_lstm('reg')
reg_model.fit(X_train, y_train_reg, epochs=5, batch_size=128, verbose=0)

print("Training LSTM Classification model...")
clf_model = build_lstm('clf')
clf_model.fit(X_train, y_train_clf, epochs=5, batch_size=128, verbose=0)

pred_reg = reg_model.predict(X_test).flatten()
pred_clf_probs = clf_model.predict(X_test).flatten()
pred_clf = (pred_clf_probs > 0.5).astype(int)

mae = mean_absolute_error(y_test_reg, pred_reg)
r2 = r2_score(y_test_reg, pred_reg)
acc = accuracy_score(y_test_clf, pred_clf)
f1 = f1_score(y_test_clf, pred_clf)
auc = roc_auc_score(y_test_clf, pred_clf_probs)

print(f"\n--- LSTM RESULTS ---")
print(f"MAE (Regression): {mae:.6f}")
print(f"R2 Score: {r2:.6f}")
print(f"Accuracy (Classification): {acc:.4f}")
print(f"F1 Score: {f1:.4f}")
print(f"Area Under Curve (AUC): {auc:.4f}")

print("\nCalculating Feature Importance (XAI)...")

def get_score(indices):
    p = clf_model.predict(X_test[:500], verbose=0).flatten()
    return accuracy_score(y_test_clf[:500], (p > 0.5).astype(int))

baseline = get_score(None)
importances = []
for i in range(len(features)):
    save = X_test[:500, :, i].copy()
    X_test[:500, :, i] = np.random.permutation(X_test[:500, :, i])
    importances.append(baseline - get_score(None))
    X_test[:500, :, i] = save

plt.figure(figsize=(10, 6))
plt.barh(features, importances)
plt.title("Explainable AI: Feature Importance (LSTM Permutation)")
plt.savefig("lstm_feature_importance.png")
plt.show()
