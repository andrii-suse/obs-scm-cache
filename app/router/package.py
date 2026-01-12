from app.dependency.db import DBSessionDep
from model.model import Scmpkg
from model.scmpkg_search import search as pkg_search, owner as pkg_owner
from fastapi import APIRouter, Depends

router = APIRouter(
    prefix="/rest/package",
    tags=["package"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/search",
)
async def do_search(
    q: str,
    db_session: DBSessionDep,
):
    pkgs = await pkg_search(db_session, q)
    return pkgs

@router.get(
    "/owner",
)
async def do_search(
    q: str,
    db_session: DBSessionDep,
):
    pkgs = await pkg_owner(db_session, q)
    return pkgs
