from dotenv import dotenv_values
from fastapi import FastAPI, Response, status, HTTPException, Request
from fastapi.params import Depends
import psycopg2
from fastapi_mail import MessageSchema, FastMail
from psycopg2.extras import RealDictCursor
import time
from passlib.context import CryptContext
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from fastapi.security import OAuth2PasswordBearer
from starlette.templating import Jinja2Templates
from typing import List
from App.schemas import Post, get_current_user, UserOut, User, Token, create_acces_token, Applicate, Message, \
    verify_acces_token, conf

config_credentials = dict(dotenv_values(".env"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
app = FastAPI()

oath2_scheme = OAuth2PasswordBearer(tokenUrl="login")


async def send_email(email: List, token):
    template = f"""
            <!DOCTYPE html>
            <html>
            <head>
            </head>
            <body>
                <div style=" display: flex; align-items: center; justify-content: center; flex-direction: column;">
                    <h3> Account Verification </h3>
                    <br>
                    <p>Thanks for choosing EasyShopas, please 
                    click on the link below to verify your account</p> 
                    <a style="margin-top:1rem; padding: 1rem; border-radius: 0.5rem; font-size: 1rem; text-decoration: none; background: #0275d8; color: white;"
                     href="http://localhost:8000/verification/?token={token}">
                        Verify your email
                    <a>
                    <p style="margin-top:1rem;">If you did not register for EasyShopas, 
                    please kindly ignore this email and nothing will happen. Thanks<p>
                </div>
            </body>
            </html>
        """

    message = MessageSchema(
        subject="EasyShopas Account Verification Mail",
        recipients=email,  # List of recipients, as many as you can pass
        body=template,
        subtype="html"
    )

    fm = FastMail(conf)
    await fm.send_message(message)


while True:
    try:
        conn = psycopg2.connect(host="localhost", database="postgres", user="postgres", password="sADAM_hussein123",
                                cursor_factory=RealDictCursor)
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
def create_posts(post: Post, current_user: psycopg2.extras.RealDictRow = Depends(get_current_user)):
    cursor.execute(
        "INSERT INTO posts (title, description, price, per_hour, per_thing, poblation,user_id, expiration) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING *",
        (post.title, post.description, post.price, post.per_hour, post.per_thing, post.poblation, current_user["id"],
         post.expiration))
    new_post = cursor.fetchone()
    conn.commit()
    return new_post


@app.get("/posts/{id}")
def get_post(id: int, response: Response):
    cursor.execute("SELECT * FROM posts WHERE id = " + str(id))
    post = cursor.fetchone()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"post with id: {id} was not found")
    return post


@app.delete("/posts/{id}")
def delte_post(id: int, status_code=status.HTTP_204_NO_CONTENT,
               current_user: psycopg2.extras.RealDictRow = Depends(get_current_user)):
    if get_post(id).user_id != current_user["user_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Please don't try to delete other people posts")
    cursor.execute("DELETE FROM posts WHERE ID = %s RETURNING *", str((id)))
    deleted_post = cursor.fetchone()
    conn.commit()
    if deleted_post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"post with id: {id} does not exist.")

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.put("/posts/{id}", status_code=status.HTTP_200_OK)
def update_post(id: int, post: Post, current_user: psycopg2.extras.RealDictRow = Depends(get_current_user)):
    if get_post(id).user_id != current_user["user_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You should edit your own posts")
    cursor.execute(
        "UPDATE posts SET title = %s, description = %s, price = %s, per_hour = %s, per_thing = %s, poblation = %s, user_id = %s, expiration = %s WHERE id = %s RETURNING *",
        (post.title, post.description, post.price, post.per_hour, post.per_thing, post.poblation, current_user["id"],
         post.expiration, str(id)))

    updated_post = cursor.fetchone()

    conn.commit()

    if updated_post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"post with id: {id} does not exist.")

    return updated_post


@app.post("/users", status_code=status.HTTP_201_CREATED, response_model=UserOut)
def create_user(user: User):
    # hash password
    hash_password = pwd_context.hash(user.password)
    user.password = hash_password
    cursor.execute(
        "INSERT INTO users (email, password, name, surname, skills, country, region, municipality, phone_number) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING *",
        (user.email, user.password, user.name, user.surname, user.skills, user.country, user.region, user.municipality,
         user.phone_number))
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
    cursor.execute("SELECT * FROM users WHERE email = '" + str(user_credentials.username) + "'")
    password_hash = cursor.fetchone()
    if not password_hash:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="This email is not registered in the app")

    if not pwd_context.verify(user_credentials.password, password_hash["password"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Password and email don't match")
    acces_token = create_acces_token(data={"user_id": password_hash["id"]})
    return {"acces_token": acces_token, "token_type": "bearer "}


@app.post("/posts/apply/{id}", status_code=status.HTTP_201_CREATED)
def aplicate(application: Applicate, id: int, current_user: psycopg2.extras.RealDictRow = Depends(get_current_user)):
    if get_post(id).user_id == current_user["user_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can't apply to your own post")
    cursor.execute("UPDATE posts SET num_applications = num_applications + 1 WHERE id = %s RETURNING *" % (str(id)))
    post = cursor.fetchone()
    cursor.execute("INSERT INTO applications (post_id, user_id, message) VALUES(%s, %s, %s)",
                   (str(post["id"]), str(current_user["id"]), str(application.application_text)))
    conn.commit()

    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"post with id: {id} does not exist.")
    return post


@app.put("/users", status_code=status.HTTP_200_OK, response_model=UserOut)
def edit_user():
    pass


# verify email, encara no funciona perque necesitem un domini perque google ens deixi entrar al gmail desde el codi.
@app.get("/verification")
async def email_sending(request: Request, current_user: psycopg2.extras.RealDictRow = Depends(get_current_user),
                        token: str = Depends(oath2_scheme)):
    verify_acces_token(token,
                       HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials",
                                     headers={"WWW-Authenicate": "Bearer"}))
    templates = Jinja2Templates(directory="templates")
    await send_email(["casas5roger@gmail.com"], token)

    return templates.TemplateResponse("verification.html",
                                      {"request": request, "username": "casas5roger@gmail.com"})


#enviar missatges si sel enviant a ell mateix me la lien
@app.post("/message/{id}", status_code=status.HTTP_201_CREATED)
def create_chat(id: int, message: Message, current_user: psycopg2.extras.RealDictRow = Depends(get_current_user)):
    cursor.execute("SELECT chat_id FROM messages WHERE from_id = " + str(current_user["id"]) + "and to_id = " + str(id) + "or from_id = " + str(id) + "and to_id = " + str(current_user["id"]))
    chat_id = cursor.fetchone()
    if chat_id is not None:
        cursor.execute(
            "INSERT INTO messages (from_id, to_id, chat_id, body) VALUES (%s, %s, %s, %s) RETURNING *",
            (current_user["id"], str(id), chat_id["chat_id"], message.body))
        conn.commit()
    else:
        cursor.execute("SELECT name, surname FROM users WHERE id = " + str(id))
        name2 = cursor.fetchone()
        cursor.execute(
            "INSERT INTO chats (user1_id, user2_id, user1_name, user2_name) VALUES (%s, %s, %s, %s) RETURNING *",
            (str(current_user["id"]), str(id), str(current_user["name"]) + " " + str(current_user["surname"]), str(name2["name"]) + " " + str(name2["surname"])))
        chat_id = cursor.fetchone()
        cursor.execute(
            "INSERT INTO messages (from_id, to_id, chat_id, body) VALUES (%s, %s, %s, %s) RETURNING *",
            (str(current_user["id"]), str(id), chat_id["id"], message.body))
        conn.commit()
    return message.body
