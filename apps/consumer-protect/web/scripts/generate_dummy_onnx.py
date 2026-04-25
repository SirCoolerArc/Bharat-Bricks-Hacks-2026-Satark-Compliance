import numpy as np
from sklearn.ensemble import RandomForestClassifier
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType

# Simple dummy dataset matching the 7 features
# [amount_log, age_days, fan_in, durationSec, isNewDevice, ipStateMatch, isVpn]
X = np.array([
    [0.0, 365.0, 2.0,  120.0, 0.0, 1.0, 0.0],
    [5.0, 1.0,   50.0, 10.0,  1.0, 0.0, 1.0],
    [2.0, 30.0,  5.0,  60.0,  0.0, 1.0, 0.0],
    [6.0, 0.0,   100.0,5.0,   1.0, 0.0, 1.0]
], dtype=np.float32)

y = np.array([0, 1, 0, 1])

clf = RandomForestClassifier(n_estimators=10, max_depth=3, random_state=42)
clf.fit(X, y)

# Convert to ONNX
initial_type = [('float_input', FloatTensorType([None, 7]))]
onnx_model = convert_sklearn(clf, initial_types=initial_type, target_opset=12)

with open("/home/neepun/satark/web/data/model_b_xgboost.onnx", "wb") as f:
    f.write(onnx_model.SerializeToString())

print("Successfully generated dummy ONNX model (using RF as a stable stub)!")
