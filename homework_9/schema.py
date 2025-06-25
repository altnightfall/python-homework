from pydantic import BaseModel

class InputData(BaseModel):
    a: float
    b: float

class Prediction(BaseModel):
    result: float

class Token(BaseModel):
    access_token: str
    token_type: str
