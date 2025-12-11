from typing import Optional
import datetime

from sqlalchemy import DateTime, ForeignKeyConstraint, Integer, PrimaryKeyConstraint, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from model.model import Scmpkg, Pkg, Scmrepo

async def search(db_session: AsyncSession, q: str):
    pkgs = (await db_session.scalars(select(Scmrepo).join(Scmpkg.pkg).join(Scmpkg.scmrepo).where(Pkg.name == q))).all()

    # pkgs = (await db_session.scalars(select(Pkg).where(Pkg.name == q))).first()
    return pkgs
