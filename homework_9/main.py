from fastapi import FastAPI
from schema import InputData, Prediction
from predict import predict_sum

app = FastAPI(title="Sum API")

@app.post("/predict", response_model=Prediction)
def get_prediction(data: InputData):
    result = predict_sum(data.a, data.b)
    return Prediction(result=result)
