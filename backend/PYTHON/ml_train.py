# Create ML training script
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib

# Generate synthetic medical data
np.random.seed(42)
n_samples = 1000

# Features: age, heart_rate, bp_systolic, bp_diastolic, spo2, temperature
X = np.random.rand(n_samples, 6)
X[:, 0] = X[:, 0] * 80 + 20  # age: 20-100
X[:, 1] = X[:, 1] * 100 + 40  # heart_rate: 40-140
X[:, 2] = X[:, 2] * 100 + 80  # bp_systolic: 80-180
X[:, 3] = X[:, 3] * 60 + 50   # bp_diastolic: 50-110
X[:, 4] = X[:, 4] * 15 + 85   # spo2: 85-100
X[:, 5] = X[:, 5] * 4 + 35    # temperature: 35-39

# Labels: 0=white, 1=green, 2=yellow, 3=red
y = np.random.randint(0, 4, n_samples)

# Train model
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
model = RandomForestClassifier(n_estimators=100)
model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"Model accuracy: {accuracy:.2f}")

# Save model
joblib.dump(model, '../models/triage_model.pkl')
print("Model saved to models/triage_model.pkl")
