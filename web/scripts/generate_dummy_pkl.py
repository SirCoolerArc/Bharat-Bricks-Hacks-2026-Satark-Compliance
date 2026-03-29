import os
import pickle
import numpy as np
import xgboost as xgb
import json

base_dir = '/home/neepun/satark/web/src/lib/ml/model'
os.makedirs(base_dir, exist_ok=True)

# Train a dummy XGBoost model on 22 features
X = np.random.rand(100, 22).astype('float32')
y = np.random.randint(0, 2, size=100)

clf = xgb.XGBClassifier(n_estimators=5, max_depth=2, use_label_encoder=False, eval_metric="logloss")
clf.fit(X, y)

# Save the model 
model_path = os.path.join(base_dir, 'model_b_xgboost.pkl')
with open(model_path, 'wb') as f:
    pickle.dump(clf, f)

print(f"Generated dummy model at {model_path} with {clf.n_features_in_} features")
