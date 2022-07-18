from typing import Optional
from fastapi import FastAPI, Response, status, HTTPException
from fastapi.params import Body, Depends
from pydantic import BaseModel, EmailStr
import psycopg2
from psycopg2.extras import RealDictCursor
import time
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from fastapi.security import OAuth2PasswordBearer

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
app = FastAPI()

SECRET_KEY = "ñ132132çfjkdljffahtjlfdash423$%/!·¬~€~@#|¬€¬()JlflHKDFÑÇ)/$·¬~#~@|$¨`^Ññ[[€;:hi+"
ALGORITHM = "HS256"
ACCES_TOKEN_EXPIRE_MINUTES = 30

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
    poblation: str

class UserOut(BaseModel):
    id: int
    email: EmailStr
    name:str
    surname:str
    skills: Optional[str]
    poblation:str
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


@app.get("/")
def root():
    cursor.execute("SELECT * FROM posts")
    post = cursor.fetchall()
    return post


@app.post("/posts", status_code=status.HTTP_201_CREATED, response_model=Post)
def create_posts(post: Post, current_user: int = Depends(get_current_user)):
    cursor.execute("INSERT INTO posts (title, description, price, per_hour, per_thing, poblation,user_id, expiration) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING *",
                   (post.title, post.description, post.price, post.per_hour, post.per_thing, post.poblation, current_user["id"], post.expiration))
    new_post = cursor.fetchone()
    print(new_post)
    conn.commit()
    return new_post


@app.get("/posts/{id}")
def get_post(id:int, response: Response):
    cursor.execute("SELECT * FROM posts WHERE id = " + str(id))
    post = cursor.fetchone()
    if not post:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = f"post with id: {id} was not found")
    return post


@app.delete("/posts/{id}")
def delte_post(id:int, status_code = status.HTTP_204_NO_CONTENT, current_user: int = Depends(get_current_user)):
    if get_post(id).user_id != current_user["user_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="not authorized to perform requested action")
    cursor.execute("DELETE FROM posts WHERE ID = %s RETURNING *", str((id)))
    deleted_post = cursor.fetchone()
    conn.commit()
    if deleted_post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail= f"post with id: {id} does not exist.")


    return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.put("/posts/{id}")
def update_post(id:int, post : Post, current_user: int = Depends(get_current_user)):

    if get_post(id).user_id != current_user["user_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="not authorized to perform requested action")
    cursor.execute("UPDATE posts SET title = %s, description = %s, price = %s, per_hour = %s, per_thing = %s, poblation = %s, user_id = %s, expiration = %s WHERE id = %s RETURNING *",
                   (post.title, post.description, post.price, post.per_hour, post.per_thing,  post.poblation, current_user["id"], post.expiration,  str(id)))

    updated_post = cursor.fetchone()

    conn.commit()

    if updated_post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail= f"post with id: {id} does not exist.")

    return updated_post

@app.post("/users", status_code= status.HTTP_201_CREATED,response_model= UserOut)
def create_user(user: User):

    #hash password
    hash_password = pwd_context.hash(user.password)
    user.password = hash_password
    cursor.execute(
        "INSERT INTO users (email, password, name, surname, skills, poblation) VALUES (%s, %s, %s, %s, %s, %s) RETURNING *",
        (user.email, user.password, user.name, user.surname, user.skills, user.poblation))
    new_user = cursor.fetchone()
    conn.commit()
    return new_user

@app.get("/users/{id}", response_model=UserOut)
def get_user(id: int):
    cursor.execute("SELECT * FROM users WHERE id =" + str(id))
    user = cursor.fetchone()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"User with id: {id} does not exist")
    return user

@app.post("/login", response_model=Token)
def login(user_credentials: OAuth2PasswordRequestForm = Depends()):
    cursor.execute("SELECT * FROM users WHERE email = '" + str(user_credentials.username)+ "'")
    password_hash = cursor.fetchone()
    if not password_hash:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="This email is not registered in the app")

    if not pwd_context.verify(user_credentials.password, password_hash["password"]):
        raise HTTPException(status_code = status.HTTP_403_FORBIDDEN, detail = "Password and email don't match")
    acces_token = create_acces_token(data={"user_id":password_hash["id"]})
    return {"acces_token": acces_token, "token_type": "bearer "}

@app.put("/posts/applicate/{id}", status_code= status.HTTP_201_CREATED)
def aplicate(application: Applicate, current_user: int = Depends(get_current_user)):
    cursor.execute("UPDATE posts SET application = %s WHERE id = %s RETURNING *" (application.application_text, str(id)))
    post = cursor.fetchone()
    conn.commit()

    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"post with id: {id} does not exist.")
