from fastapi import FastAPI

from api.routers import analytics, customers


app = FastAPI()

app.include_router(customers.router)
app.include_router(analytics.router)