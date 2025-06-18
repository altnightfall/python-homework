from tensorflow.keras.models import load_model
import numpy as np

model = load_model("sum_model.keras")

def predict_sum(a: float, b: float) -> float:
    x = np.array([[a, b]], dtype=np.float32)
    result = model.predict(x, verbose=0)
    return float(result[0][0])
