from typing import Optional

import psycopg2
from fastapi import  status, HTTPException
from fastapi.params import Depends
from fastapi_mail import ConnectionConfig
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel, EmailStr, constr
from datetime import datetime, timedelta, time
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer
from typing import List
from App.pasw import MAIL_USERNAME, MAIL_PASSWORD


SECRET_KEY = "ñ132132çfjkdljffahtjlfdash423$%/!·¬~€~@#|¬€¬()JlflHKDFÑÇ)/$·¬~#~@|$¨`^Ññ[[€;:hi+"
ALGORITHM = "HS256"
ACCES_TOKEN_EXPIRE_MINUTES = 30

while True:
    try:
        conn = psycopg2.connect(host = "localhost", database="postgres", user="postgres", password="sADAM_hussein123", cursor_factory=RealDictCursor)
        cursor = conn.cursor()
        print("Connection with database was succesful.")
        break
    except Exception as error:
        print("conection to database field")
        print(error)
        time.sleep(5)



conf = ConnectionConfig(
    MAIL_USERNAME = "bingchilling152@gmail.com",
    MAIL_PASSWORD = "humblework",
    MAIL_FROM = "bingchilling152@gmail.com",
    MAIL_PORT = 587,
    MAIL_SERVER = "smtp.gmail.com",
    MAIL_TLS = True,
    MAIL_SSL = False,
    USE_CREDENTIALS = True
)

oath2_scheme =OAuth2PasswordBearer(tokenUrl="login")



def create_acces_token(data: dict):
    to_encode= data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCES_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp":expire})

    encode = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encode

def verify_acces_token(token: str, credential_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms= ALGORITHM)
        id: str = payload.get("user_id")
        if id is None:
            raise credential_exception
        token_data = Token_data(id=id)
    except JWTError:
        raise credential_exception
    return token_data

def get_current_user(token :str = Depends(oath2_scheme)):
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials", headers={"WWW-Authenicate": "Bearer"})
    token = verify_acces_token(token, credentials_exception)
    cursor.execute("SELECT * FROM users WHERE id =" + str(token.id))
    user = cursor.fetchone()
    return user



class Post(BaseModel):
    title: str
    description: str
    price: float
    per_hour: Optional[bool]
    per_thing: Optional[str]
    poblation: str
    expiration: Optional[datetime]

class User(BaseModel):
    email: EmailStr
    password: str
    name: str
    surname: str
    skills: Optional[str]
    country: str
    region: str
    municipality: str
    phone_number: str

class UserOut(BaseModel):
    id: int
    email: EmailStr
    name:str
    surname:str
    skills: Optional[str]
    country: str
    region: str
    municipality: str
    phone_number: str
    created_at: datetime

class Login(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    acces_token: str
    token_type: str

class Token_data(BaseModel):
    id: Optional[str] = None

class Applicate(BaseModel):
    application_text: str

class EmailSchema(BaseModel):
    email: List[EmailStr]

class Message(BaseModel):
    body: constr(max_length=256)