from typing import Optional
import datetime

from sqlalchemy import (
    DateTime,
    ForeignKeyConstraint,
    Integer,
    PrimaryKeyConstraint,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from model.model import Scmpkg, Pkg, Scmrepo


async def search(db_session: AsyncSession, q: str):

    sql = """
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
and scmpkg.deleted_at is NULL
"""

    cursor = await db_session.execute(text(sql), {"pkg": q})
    rows = cursor.mappings().all()
    return rows


async def owner(db_session: AsyncSession, q: str):

    sql = """
select
string_agg(scmpkg_maintainer.maintainer,',') as package_maintainers,
concat(scmrepo.org,'/',scmrepo.repo,'#',scmrepo.branch) as repo,
string_agg(scmrepo_maintainer.maintainer,',') as project_maintainers,
string_agg(obsproj.name,',') as obs_projects
from
pkg
join scmpkg on pkg_id = pkg.id
join scmrepo on scmpkg.scmrepo_id = scmrepo.id
join scmhost on scmhost_id = scmhost.id
left join obsproj on obsproj.scmsync like concat('%',scmrepo.org,'/',scmrepo.repo,'%','#',scmrepo.branch)
left join scmrepo_maintainer on scmrepo_maintainer.scmrepo_id = scmrepo.id and scmrepo_maintainer.deleted_at is null
left join scmpkg_maintainer  on scmpkg_maintainer.scmrepo_id = scmrepo.id and scmpkg_maintainer.deleted_at is null and scmpkg_maintainer.pkg = pkg.name
where pkg.name = :pkg
group by scmrepo.id, scmrepo.org, scmrepo.repo
"""

    cursor = await db_session.execute(text(sql), {"pkg": q})
    rows = cursor.mappings().all()
    return rows


async def select_last_scan_details_for_scmrepo(
    db_session: AsyncSession, scmhost: str, org: str, repo: str, branch: str
):

    sql = """
select
scmrepo.id,
scmrepo.last_scan_at,
scmrepo.sha,
max(scmpkg.last_seen_at) as last_seen_package_at
from
scmrepo
left join scmpkg on scmrepo_id = scmrepo.id
where
scmhost_id = (select id from scmhost where hostname = :scmhost)
and scmrepo.org    = :org
and scmrepo.repo   = :repo
and scmrepo.branch = :branch
and scmpkg.deleted_at is NULL
group by scmrepo.id, scmrepo.last_scan_at, scmrepo.sha
"""

    cursor = await db_session.execute(
        text(sql), {"scmhost": scmhost, "org": org, "repo": repo, "branch": branch}
    )
    rows = cursor.mappings().all()
    if not rows:
        return None
    else:
        row = rows[0]
        return row
