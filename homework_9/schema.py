from pydantic import BaseModel

class InputData(BaseModel):
    a: float
    b: float

class Prediction(BaseModel):
    result: float