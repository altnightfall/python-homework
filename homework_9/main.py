from fastapi import FastAPI, Depends
from fastapi.security import OAuth2PasswordRequestForm
from schema import InputData, Prediction, Token
from predict import predict_sum
from auth import (
    authenticate_user, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES,
    get_current_user, require_role
)
from datetime import timedelta

app = FastAPI(title="ML Sum API with Auth")

@app.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/predict", response_model=Prediction)
def get_prediction(data: InputData, user=Depends(get_current_user)):
    result = predict_sum(data.a, data.b)
    return Prediction(result=result)

@app.get("/admin")
def admin_area(user=Depends(require_role("admin"))):
    return {"msg": f"Hello admin {user.username}"}
