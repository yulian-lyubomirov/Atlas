from fastapi import FastAPI
from inserter import DB
from controllers import asset_types  # your asset_types.py router
from controllers import users 
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Atlas API")
PROJECT_ROOT = Path.cwd().parent # make env var
CONFIG_PATH = PROJECT_ROOT / "src" / "dbconfig" # make env var
# initialize DB
db = DB()
db.connect(config_file=str(CONFIG_PATH))  # or from env

origins = [
    "http://localhost:5173",  # Vite dev server
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# make DB available to routers
app.state.db = db

# include routers
app.include_router(asset_types.router)
app.include_router(users.router)
