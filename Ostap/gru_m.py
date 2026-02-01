import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, accuracy_score
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import GRU, Dense, Dropout, Input
from tensorflow.keras.optimizers import Adam

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
X = df[features].values
y_reg = df['target_return'].values
y_clf = df['target_up'].values

scaler = MinMaxScaler()
X_scaled = scaler.fit_transform(X)

def create_sequences(X, y_r, y_c, window=20):
    Xs, yr, yc = [], [], []
    for i in range(window, len(X)):
        Xs.append(X[i-window:i])
        yr.append(y_r[i])
        yc.append(y_c[i])
    return np.array(Xs), np.array(yr), np.array(yc)

WINDOW = 20
X_seq, y_reg_seq, y_clf_seq = create_sequences(X_scaled, y_reg, y_clf, WINDOW)

split = int(0.8 * len(X_seq))
X_train, X_test = X_seq[:split], X_seq[split:]
y_train_reg, y_test_reg = y_reg_seq[:split], y_reg_seq[split:]
y_train_clf, y_test_clf = y_clf_seq[:split], y_clf_seq[split:]

reg_model = Sequential([
    Input(shape=(WINDOW, len(features))),
    GRU(32),
    Dropout(0.2),
    Dense(1)
])
reg_model.compile(optimizer=Adam(0.001), loss='mae')
reg_model.fit(X_train, y_train_reg, epochs=3, batch_size=256, verbose=0)

clf_model = Sequential([
    Input(shape=(WINDOW, len(features))),
    GRU(32),
    Dropout(0.2),
    Dense(1, activation='sigmoid')
])
clf_model.compile(optimizer=Adam(0.001), loss='binary_crossentropy', metrics=['accuracy'])
clf_model.fit(X_train, y_train_clf, epochs=3, batch_size=256, verbose=0)

pred_reg = reg_model.predict(X_test, batch_size=512, verbose=0).flatten()
pred_clf = (clf_model.predict(X_test, batch_size=512, verbose=0) > 0.5).astype(int).flatten()

print(f"MAE (Next return prediction): {mean_absolute_error(y_test_reg, pred_reg):.6f}")
print(f"Accuracy (Up/Down prediction): {accuracy_score(y_test_clf, pred_clf):.4f}")

print("\nExample next-minute prediction:")
print(f"Real return next minute: {y_test_reg[-1]:.6f}")
print(f"Predicted return next minute: {pred_reg[-1]:.6f}")

print(f"\nReal direction: {y_test_clf[-1]}")
print(f"Predicted direction: {pred_clf[-1]}")