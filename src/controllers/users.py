from fastapi import APIRouter, HTTPException, Request, Body
import queries as queries
router = APIRouter(prefix="/users", tags=["users"])

@router.post("/create")
async def create_user(
    request: Request,
    name: str = Body(...),
    password: str = Body(...),
    email: str = Body(...)
):
    db = request.app.state.db
    
    # Hash the password
    import bcrypt
    hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

    try:
        db.execute(
            "INSERT INTO users (name, password_hash) VALUES (%(name)s, %(password_hash)s,%(email)s)",
            {"name": name, "password_hash": hashed_pw.decode("utf-8"),"email":email}
        )
        return {"status": "success", "name": name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
async def get_users(request: Request):
    db = request.app.state.db
    try:
        rows = db.fetch(queries.FETCH_USERS)
        # Convert to list of dicts
        result = [{"id": r[0], "name": r[1], "creation_date": r[2].isoformat()} for r in rows]
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))