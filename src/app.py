from fastapi import FastAPI
from inserter import DB
from controllers import asset_types  # your asset_types.py router
from controllers import users 
from pathlib import Path

app = FastAPI(title="Atlas API")
PROJECT_ROOT = Path.cwd().parent # make env var
CONFIG_PATH = PROJECT_ROOT / "src" / "dbconfig" # make env var
# initialize DB
db = DB()
db.connect(config_file=str(CONFIG_PATH))  # or from env

# make DB available to routers
app.state.db = db

# include routers
app.include_router(asset_types.router)
app.include_router(users.router)
