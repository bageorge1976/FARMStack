from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from motor import motor_asyncio
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


from fastapi.encoders import jsonable_encoder

from collections import defaultdict

from config import BaseConfig
from routers.cars import router as cars_router
from routers.users import router as users_router

settings = BaseConfig()

# define origins
origins = ["*"]


async def lifespan(app: FastAPI):
    app.client = motor_asyncio.AsyncIOMotorClient(settings.DB_URL)
    app.db = app.client[settings.DB_NAME]

    try:
        app.client.admin.command("ping")
        print("Pinged your deployment. You have successfully connected to MongoDB!")
        print("Mongo address:", settings.DB_URL)
    except Exception as e:
        print(e)
    yield
    app.client.close()


app = FastAPI(lifespan=lifespan)


# add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def custom_form_validation_error(request, exc):
    reformatted_message = defaultdict(list)
    for pydantic_error in exc.errors():
        loc, msg = pydantic_error["loc"], pydantic_error["msg"]
        filtered_loc = loc[1:] if loc[0] in ("body", "query", "path") else loc
        field_string = ".".join(filtered_loc)  # nested fields with dot-notation
        reformatted_message[field_string].append(msg)

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=jsonable_encoder(
            {"detail": "Invalid request", "errors": reformatted_message}
        ),
    )


app.include_router(cars_router, prefix="/cars", tags=["cars"])
app.include_router(users_router, prefix="/users", tags=["users"])


@app.get("/")
async def get_root():
    return {"Message": "Root working"}


"""Testing the user login via HTTPie
(.farm-venv) bageorgescu@bageorgescu-Z590-AORUS-ELITE-AX:~/FastAPIProjects/Full-Stack-FastAPI-React-and-MongoDB-2nd-Edition/Chapter07/backend$ http POST http://127.0.0.1:8000/users/login username="bogdan" password="bogdan123"
HTTP/1.1 200 OK
content-length: 247
content-type: application/json
date: Sun, 09 Nov 2025 18:54:42 GMT
server: uvicorn

{
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NjI3MTYyODMsImlhdCI6MTc2MjcxNDQ4Mywic3ViIjp7InVzZXJfaWQiOiI2OTEwZDk0OThiMjgwOTFiODMyNDY0ZWEiLCJ1c2VybmFtZSI6ImJvZ2RhbiJ9fQ.U6R2Lhe7CFWlYKljkL4QqIJf6CtLj03DBnIIdEfgBPg",
    "username": "bogdan"
}
"""

""" Testing the car creation with image upload via HTTPie

(.farm-venv) bageorgescu@bageorgescu-Z590-AORUS-ELITE-AX:~/FastAPIProjects/Full-Stack-FastAPI-React-and-MongoDB-2nd-Edition/Chapter07/backend$ http --form POST http://127.0.0.1:8000/cars/   "Authorization:Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NjI3MTYyODMsImlhdCI6MTc2MjcxNDQ4Mywic3ViIjp7InVzZXJfaWQiOiI2OTEwZDk0OThiMjgwOTFiODMyNDY0ZWEiLCJ1c2VybmFtZSI6ImJvZ2RhbiJ9fQ.U6R2Lhe7CFWlYKljkL4QqIJf6CtLj03DBnIIdEfgBPg"   brand="KIA"   make="Ceed"   year=2015   price=2000   km=100000   cm3=1500   picture@ASSETA.png
HTTP/1.1 201 Created
content-length: 255
content-type: application/json
date: Sun, 09 Nov 2025 19:06:39 GMT
server: uvicorn

{
    "_id": "6910e641b0cf9398ac60c5f1",
    "brand": "Kia",
    "cm3": 1500,
    "km": 100000,
    "make": "Ceed",
    "picture_url": "http://res.cloudinary.com/dokdilwfr/image/upload/v1762715200/FARM2/qk4u34rvtxqlbtl5rg1s.png",
    "price": 2000,
    "user_id": "6910d9498b28091b832464ea",
    "year": 2015
}
"""

""" Testing the get all cars via HTTPie
http GET http://127.0.0.1:8000/users/me   "Authorization:Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6Ikp
XVCJ9.eyJleHAiOjE3NjI3MjIzNzgsImlhdCI6MTc2MjcyMDU3OCwic3ViIjp7InVzZXJfaWQiOiI2OTEwZDk0OThiMjgwOTFiODMyNDY0ZWEiLCJ1c2Vyb
mFtZSI6ImJvZ2RhbiJ9fQ.jelFnBet7Dx4izKwZvE2U6HjqXcw7wiM8A_WCpsCVN4"
HTTP/1.1 200 OK
content-length: 54
content-type: application/json
date: Sun, 09 Nov 2025 20:50:20 GMT
server: uvicorn

{
    "_id": "6910d9498b28091b832464ea",
    "username": "bogdan"
}
"""