from fastapi import FastAPI


from routes import base 

app = FastAPI()

app.include_router(base.BaseRouter)