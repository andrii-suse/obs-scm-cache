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
import base64

http = urllib3.PoolManager()

def collect_branches_from_gitmodules(txt, default_host, default_org):
    from configparser import ConfigParser
    from pathlib import PurePath

    cfg = ConfigParser()
    cfg.read_string(txt)

    res = {}

    for section in cfg.sections():
        if not section.startswith('submodule "'):
            continue
        path = cfg.get(section, "path")
        if not path:
            continue
        name = PurePath(path).name
        if not name:
            continue
        url = cfg.get(section, "url")
        if not url:
            continue

        # match = re.match(r"^(((https?:\/\/)?(.*@)?([^\/]+|..(\/..)?))\/([^\/]+)|..)\/([^\/\#]+?)(\.git)?(\?[^#\/]*)?(\#([^\/#]+))?$", url)
        match = re.match(r"^(((https?:\/\/)?(.*@)?([^\/]+|..(\/..)?))\/([^\/]+)|..)\/([^\/\#]+?)(\.git)?(\?[^#\/]*)?$", url)
        if not match:
            print(f"Unexpected url format {url}")

        repo = match.group(8)
        org  = match.group(7)
        host = match.group(6)
        # branch = match.group(5)
        
        if not host or host == '/..':
            host = default_host
        if not org:
            org = default_org

        if not repo:
            continue

        branch = ""
        
        if cfg.has_option(section, "branch"):
            branch = cfg.get(section, "branch")

        res[name] = (host, org, repo, branch)

    return res



def collect_branches_from_gitmodules_url(url, default_host, default_org):
    response = http.request("GET", url)
    if response.status > 299 or response.status < 200:
        print(f"request {req_url} failed ({response.status}:{response.reason})")
        return

    body = response.json()

    if not body:
        print(f"Empty response from {url}")
        return

    if body.get("size",-1) == 0:
        return

    content = body.get("content", "")

    if not content:
        print(f"Empty content from {url}")
        return

    encoding = body.get("encoding","")
    if not encoding:
        print(f"Empty encoding from {url}")
        return

    if encoding != "base64":
        print(f"Unknown encoding '{encoding}' from {url}")
        return

    try:
        txt = base64.standard_b64decode(content).decode('utf-8')
        return collect_branches_from_gitmodules(txt, default_host, default_org)
    except Exception:
        import traceback

        print("Generic exception: " + traceback.format_exc())
        pass
    except:
        print("Unknown error")
        pass




def git_tree_scan(uri, loop):
    match = re.match(r"^(https?://)?([^/]+)/([^/]+)/([^\/\#\.]+?)(\.git)?(\?[^#\/]*)?(\#([^\/#]+))?$", uri)
    if not match:
        raise ValueError(f"Invalid repo url: {url}")

    proto = match.group(1)
    host = match.group(2)
    org = match.group(3)
    repo = match.group(4)
    branch = match.group(8)
    branch_guessed = 0

    if not branch:
        branch = "main"
        branch_guessed = 1
    if not proto:
        proto = "https://"

    req_url = f"{proto}{host}/api/v1/repos/{org}/{repo}/git/trees/{branch}"
    response = http.request("GET", req_url)

    if response.status > 299 or response.status < 200 and branch_guessed:
        req_url = f"{proto}{host}/api/v1/repos/{org}/{repo}/git/trees/master"
        response = http.request("GET", req_url)

    if response.status > 299 or response.status < 200:
        print(f"request {req_url} failed ({response.status}:{response.reason})")
        return

    body = response.json()

    if not body:
        print("Empty response")
        return

    sha  = body.get("sha")
    if not sha:
        print("Empty sha")
        return

    body = body.get("tree")

    if not body:
        print("Empty tree")
        return

    package_sha = {}
    _manifest_url = ""

    for r in body:
        path = r.get("path", "")
        if not path:
            continue

        if path == ".gitmodules":
            submodule_branches = collect_branches_from_gitmodules_url(r["url"], host, org)

        if r.get("mode", "0") == "160000" and r.get("type","") == "commit":
            package_sha[path] = r.get("sha","")

    if package_sha:
        return asyncio.run_coroutine_threadsafe(
            scm_db_fill(host, org, repo, branch, sha, package_sha, submodule_branches), loop
        ).result()


async def scm_db_fill(host, org, repo, branch, sha, pkgs_sha, branches):

    async for conn in get_db_session():
        # TODO!!!! how to use parameter here to avoid SQL injection???
        await conn.execute(
            text(
                f"insert into scmhost(hostname) select '{host}' on conflict do nothing;"
            )
        )
        await conn.execute(
            text(
                f"insert into scmrepo(scmhost_id, org, repo, branch, sha) select (select id from scmhost where hostname = '{host}'), '{org}', '{repo}', '{branch}', '{sha}' on conflict do nothing"
            )
        )
        for pkg in sorted(pkgs_sha):
            await conn.execute(
                text(f"insert into pkg(name) select '{pkg}' on conflict do nothing")
            )
            tpl = branches[pkg]
            if not tpl:
                print(f"Submodule {pkg} has no details")
                continue

            (pkg_host, pkg_org, pkg_repo, pkg_branch) = tpl
            pkg_sha = pkgs_sha[pkg]
            await conn.execute(
                text(
                    f"insert into scmpkg(scmrepo_id, pkg_id, host, org, repo, branch, sha) select (select id from scmrepo where scmhost_id in (select id from scmhost where hostname = '{host}') and org = '{org}' and repo = '{repo}' and branch = '{branch}' and sha = '{sha}' ), (select id from pkg where name = '{pkg}'), '{pkg_host}', '{pkg_org}', '{pkg_repo}', '{pkg_branch}', '{pkg_sha}' on conflict do nothing"
                )
            )

        await conn.commit()
        break

    return 0


def main(url):
    def thr(loop):
        asyncio.set_event_loop(loop)
        loop.run_forever()

    loop = asyncio.new_event_loop()
    t = threading.Thread(target=thr, args=(loop,), daemon=True)
    t.start()

    ret = git_tree_scan(url, loop)


if __name__ == "__main__":
    url = sys.argv[1]
    err = 0
    try:
        err = main(url)
    except Exception:
        import traceback
        print("Generic exception: " + traceback.format_exc())
        err = 1
    except:
        print("Not an exception")
        err = 1

    exit(err)

print("gitea_scan done")
