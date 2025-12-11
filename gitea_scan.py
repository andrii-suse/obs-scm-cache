#!/usr/bin/python3
import sys

from app.config import settings
from app.database import get_db_session
from model.model import Pkg

import asyncio
import threading
import urllib3
import json
import re
from typing import Annotated
from fastapi import Depends
from sqlalchemy.sql import text
from sqlalchemy.ext.asyncio import AsyncSession


http = urllib3.PoolManager()


def git_tree_scan(uri, loop):
    match = re.match(r"^(https?://)?([^/]+)/([^/]+)/([^\/\#\.]+?)(\.git)?(\?[^#\/]*)?(\#([^\/#]+))?$", uri)
    if not match:
        raise ValueError(f"Invalid repo url: {url}")

    proto = match.group(1)
    host = match.group(2)
    owner = match.group(3)
    repo = match.group(4)
    sha = match.group(8)
    sha_guessed = 0

    if not sha:
        sha = "main"
        sha_guessed = 1
    if not proto:
        proto = "https://"

    req_url = f"{proto}{host}/api/v1/repos/{owner}/{repo}/git/trees/{sha}"
    response = http.request("GET", req_url)

    if response.status > 299 or response.status < 200 and sha_guessed:
        req_url = f"{proto}{host}/api/v1/repos/{owner}/{repo}/git/trees/master"
        response = http.request("GET", req_url)

    if response.status > 299 or response.status < 200:
        print(f"request {req_url} failed ({response.status}:{response.reason})")
        return

    body = response.json()

    if not body:
        print("Empty response")
        return

    body = body.get("tree")

    if not body:
        print("Empty tree")
        return

    packages = []
    _manifest_url = ""

    for r in body:
        path = r.get("path", "")
        if not path:
            continue
        # if path == "_manifest":
        if r.get("mode", "0") == "160000":
            packages.append(path)

    if packages:
        asyncio.run_coroutine_threadsafe(
            scm_db_fill(host, owner, repo, sha, packages), loop
        ).result()


async def scm_db_fill(host, owner, repo, sha, pkgs):

    async for conn in get_db_session():
        # TODO!!!! how to use parameter here to avoid SQL injection???
        await conn.execute(
            text(
                f"insert into scmhost(hostname) select '{host}' on conflict do nothing;"
            )
        )
        await conn.execute(
            text(
                f"insert into scmrepo(scmhost_id, org, repo, branch) select (select id from scmhost where hostname = '{host}'), '{owner}', '{repo}', '{sha}' on conflict do nothing"
            )
        )  # , $host, f"{owner}/{repo}")
        for pkg in pkgs:
            await conn.execute(
                text(f"insert into pkg(name) select '{pkg}' on conflict do nothing")
            )  # , $host, f"{owner}/{repo}")
            await conn.execute(
                text(
                    f"insert into scmpkg(scmrepo_id, pkg_id) select (select id from scmrepo where scmhost_id in (select id from scmhost where hostname = '{host}') and org = '{owner}' and repo = '{repo}' and branch = '{sha}' ), (select id from pkg where name = '{pkg}') on conflict do nothing"
                )
            )

        await conn.commit()
        break


def main(url):
    def thr(loop):
        asyncio.set_event_loop(loop)
        loop.run_forever()

    loop = asyncio.new_event_loop()
    t = threading.Thread(target=thr, args=(loop,), daemon=True)
    t.start()

    git_tree_scan(url, loop)


if __name__ == "__main__":
    url = sys.argv[1]
    try:
        main(url)
    except Exception:
        import traceback

        print("Generic exception: " + traceback.format_exc())
    except:
        print("Not an exception")

print("gitea_scan done")
