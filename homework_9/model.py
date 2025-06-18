import numpy as np
from tensorflow import keras
from tensorflow.keras import layers

X = np.random.rand(10000, 2)
y = X.sum(axis=1)


model = keras.Sequential([
    layers.Dense(10, activation="relu", input_shape=(2,)),
    layers.Dense(1)
])

model.compile(optimizer="adam", loss="mse")
model.fit(X, y, epochs=10, batch_size=32, verbose=1)

model.save("sum_model.keras")
