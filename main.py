from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, Field, Session, create_engine, select
import bcrypt
from bot_engine import generate_reply

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

chat_history = []

MYSQL_URL = "mysql+mysqlconnector://root:root@localhost/chatbot_database"
engine = create_engine(MYSQL_URL, echo=True)


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str
    username: str
    password: str


SQLModel.metadata.create_all(engine)


class SignupRequest(BaseModel):
    email: str
    username: str
    password: str


@app.post("/signup")
async def signup(data: SignupRequest):
    hashed_pw = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()

    user = User(email=data.email, username=data.username, password=hashed_pw)

    with Session(engine) as session:
        session.add(user)
        session.commit()

    return {"reply": "Signup success"}


class LoginRequest(BaseModel):
    email: str
    password: str

@app.post("/login")
async def login(data: LoginRequest):
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == data.email)).first()

        if not user:
            return {"reply": "Invalid credentials"}

        if bcrypt.checkpw(data.password.encode(), user.password.encode()):
            return {"reply": "Login success",
                    "username": user.username}

        return {"reply": "Invalid credentials"}

class UserMessage(BaseModel):
    message: str

@app.post("/chat")
async def chat(data: UserMessage):
    global chat_history
    reply, chat_history = generate_reply(chat_history, data.message)
    return {"reply": reply}
class UpdatePasswordRequest(BaseModel):
    email: str
    old_password: str
    new_password: str


@app.patch("/update-password")
async def update_password(data: UpdatePasswordRequest):
    with Session(engine) as session:
        statement = select(User).where(User.email == data.email)
        user = session.exec(statement).first()

        if not user:
            return {"reply": "User not found"}

        if not bcrypt.checkpw(data.old_password.encode(), user.password.encode()):
            return {"reply": "Old password is incorrect"}

        new_hashed_pw = bcrypt.hashpw(data.new_password.encode(), bcrypt.gensalt()).decode()
        user.password = new_hashed_pw

        session.add(user)
        session.commit()

        return {"reply": "Password updated successfully!"}
class ForgotPasswordRequest(BaseModel):
    email: str

@app.post("/forgot-password")
async def forgot_password(data: ForgotPasswordRequest):
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == data.email)).first()

        if not user:
            return {"reply": "Email not found"}
        
        return {"reply": "Email verified"}

class EmailCheck(BaseModel):
    email: str

@app.post("/check-user")
async def check_user(data: EmailCheck):
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == data.email)).first()
        return {"found": bool(user)}
class ForgotUpdate(BaseModel):
    email: str
    new_password: str

@app.patch("/update-password-forgot")
async def update_password_forgot(data: ForgotUpdate):
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == data.email)).first()

        if not user:
            return {"reply": "User not found"}

        hashed_pw = bcrypt.hashpw(data.new_password.encode(), bcrypt.gensalt()).decode()
        user.password = hashed_pw
        session.add(user)
        session.commit()

        return {"reply": "Password reset successful!"}
