from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

fake_users_db = {
    "alice": {
        "username": "alice",
        "hashed_password": pwd_context.hash("secret"),
        "role": "user"
    },
    "bob": {
        "username": "bob",
        "hashed_password": pwd_context.hash("adminpass"),
        "role": "admin"
    }
}
