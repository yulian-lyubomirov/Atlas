import queries as queries
from fastapi import APIRouter, HTTPException, Depends
from dependencies import get_db
router = APIRouter(prefix="/asset_types", tags=["Asset Types"])

@router.get("/")
async def get_asset_types(db = Depends(get_db)):
    try:
        rows = db.fetch(queries.FETCH_ALL_ASSET_TYPES)
        return [{"id": r[0], "name": r[1]} for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/")
async def create_asset_type(name: str, db = Depends(get_db)):
    try:
        db.execute("INSERT INTO asset_type (name) VALUES (%(name)s)", {"name": name})
        return {"status": "success", "name": name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
