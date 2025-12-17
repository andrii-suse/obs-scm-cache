from typing import Optional
import datetime

from sqlalchemy import DateTime, ForeignKeyConstraint, Integer, PrimaryKeyConstraint, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from model.model import Scmpkg, Pkg, Scmrepo

async def search(db_session: AsyncSession, q: str):

    sql = '''
select
obsproj.name,
scmhost.hostname as appliance,
scmrepo.org as project_org, scmrepo.repo as project_repo, scmrepo.branch as project_branch,
scmpkg.host as package_appliance,
scmpkg.org as package_org, scmpkg.repo as package_repo, scmpkg.branch as package_branch, scmpkg.sha as package_sha
from
pkg
join scmpkg on pkg_id = pkg.id
join scmrepo on scmrepo_id = scmrepo.id
join scmhost on scmhost_id = scmhost.id
join obsproj on obsproj.scmsync like concat('%',scmrepo.org,'/',scmrepo.repo,'%','#',scmrepo.branch)
where pkg.name = :pkg
'''

    cursor = await db_session.execute(text(sql), {"pkg": q})
    rows = cursor.mappings().all()
    return rows
