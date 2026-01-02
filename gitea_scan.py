#!/usr/bin/python3
import sys

from app.config import settings
from app.database import get_db_session
from model.model import Pkg
from model.scmpkg_search import select_last_scan_details_for_scmrepo

import asyncio
import threading
import urllib3
import json
import re
import os
from pathlib import PurePath
from typing import Annotated
from fastapi import Depends
from sqlalchemy.sql import text
from sqlalchemy.ext.asyncio import AsyncSession
import base64

http = urllib3.PoolManager()


def process_manifest(txt):
    import yaml

    manifest_yml = yaml.safe_load(txt)
    if not manifest_yml:
        return
    subdirs = []
    if manifest_yml.get("subdirectories"):
        for newsubdir in manifest_yml["subdirectories"]:
            if newsubdir:
                subdirs.append(newsubdir)
    return subdirs


def process_manifest_from_url(url, headers):
    txt = read_file_from_git_trees(url, headers)
    return process_manifest(txt)


def collect_branches_from_gitmodules(txt, subdirs, default_host, default_org):
    from configparser import ConfigParser

    cfg = ConfigParser()
    cfg.read_string(txt)

    res = {}

    for section in cfg.sections():
        if not section.startswith('submodule "'):
            continue
        path = cfg.get(section, "path")
        if not path:
            continue
        path_obj = PurePath(path)
        name = str(path_obj.name)
        if not name:
            continue

        if subdirs:
            parent = str(path_obj.parent)
            found = 0
            for subdir in subdirs:
                if parent == subdir:
                    found = 1
                    break
            if not found:
                continue

        url = cfg.get(section, "url")
        if not url:
            continue

        # match = re.match(r"^(((https?:\/\/)?(.*@)?([^\/]+|..(\/..)?))\/([^\/]+)|..)\/([^\/\#]+?)(\.git)?(\?[^#\/]*)?(\#([^\/#]+))?$", url)
        match = re.match(
            r"^(((https?:\/\/)?(.*@)?([^\/]+|..(\/..)?))\/([^\/]+)|..)\/([^\/\#]+?)(\.git)?$",
            url,
        )
        if not match:
            print(f"Unexpected url format {url}")
            return

        repo = match.group(8)
        org = match.group(7)
        host = match.group(6)
        # branch = match.group(5)

        if not host or host == "/..":
            host = default_host
        if not org:
            org = default_org

        if not repo:
            continue

        branch = ""

        if cfg.has_option(section, "branch"):
            branch = cfg.get(section, "branch")

        res[path] = (host, org, repo, branch)

    return res


def collect_branches_from_gitmodules_url(
    url, headers, subdirs, default_host, default_org
):
    txt = read_file_from_git_trees(url, headers)
    return collect_branches_from_gitmodules(txt, subdirs, default_host, default_org)


def read_file_from_git_trees(url, headers):

    response = http.request("GET", url, headers=headers)
    if response.status > 299 or response.status < 200:
        print(f"request {req_url} failed ({response.status}:{response.reason})")
        return

    body = response.json()

    if not body:
        print(f"Empty response from {url}")
        return

    if body.get("size", -1) == 0:
        return

    content = body.get("content", "")

    if not content:
        print(f"Empty content from {url}")
        return

    encoding = body.get("encoding", "")
    if not encoding:
        print(f"Empty encoding from {url}")
        return

    if encoding != "base64":
        print(f"Unknown encoding '{encoding}' from {url}")
        return

    try:
        return base64.standard_b64decode(content).decode("utf-8")
    except Exception:
        import traceback

        print("Generic exception: " + traceback.format_exc())
        pass
    except:
        print("Unknown error")
        pass


def git_tree_request(url, headers):
    response = http.request("GET", url, headers=headers)

    if response.status > 299 or response.status < 200:
        print(f"request {url} failed ({response.status}:{response.reason})")
        return (None, None, None)

    body = response.json()

    if not body:
        print("Empty response")
        return (None, None, None)

    sha = body.get("sha")
    if not sha:
        print("Empty sha")
        return (None, None, None)

    truncated = body.get("truncated")

    body = body.get("tree")

    if not body:
        print("Empty tree")
        return (None, None, None)

    return (body, sha, truncated)


def git_tree_scan(uri, loop):
    match = re.match(
        r"^(https?://)?([^/]+)/([^/]+)/([^\/\#\.]+?)(\.git)?(\?[^#\/]*)?(\#([^\/#]+))?$",
        uri,
    )
    if not match:
        print(f"Invalid repo url: {uri}", file=sys.stderr)
        return

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

    headers = None
    token = os.environ.get("OBS_SCM_CACHE_GITEA_TOKEN", "")
    if token:
        headers = {"Authorization": f"token {token}"}

    req_url = f"{proto}{host}/api/v1/repos/{org}/{repo}/git/trees/{branch}"
    (body, sha, truncated) = git_tree_request(req_url, headers)

    if not body and branch_guessed:
        req_url = f"{proto}{host}/api/v1/repos/{org}/{repo}/git/trees/master"
        (body, sha, truncated) = git_tree_request(req_url, headers)

    if not body:
        return

    package_sha = {}
    _manifest_url = ""

    # first try to find _manifest
    subdirs = None
    for r in body:
        path = r.get("path", "")
        if path == "_manifest":
            subdirs = process_manifest_from_url(r["url"], headers)

    recursive = 0
    page = 0
    # when we have subdirs we must get trees recursive
    # TODO loop over git tree pages
    if subdirs:
        recursive = 1
        (body, sha, truncated) = git_tree_request(req_url + "?recursive=1", headers)

    while True:
        for r in body:
            path = r.get("path", "")
            if not path:
                continue

            if path == ".gitmodules":
                submodule_branches = collect_branches_from_gitmodules_url(
                    r["url"], headers, subdirs, host, org
                )
                continue

            if subdirs:
                path_obj = PurePath(path)
                parent = str(path_obj.parent)
                found = 0
                for subdir in subdirs:
                    if subdir == parent:
                        found = 1
                        break

                if not found:
                    continue

            if r.get("mode", "0") == "160000" and r.get("type", "") == "commit":
                package_sha[path] = r.get("sha", "")

        if not truncated:
            break
        else:
            page = page + 1
            if recursive:
                (body, sha, truncated) = git_tree_request(
                    f"{req_url}?recursive=1&page={page}", headers
                )
            else:
                (body, sha, truncated) = git_tree_request(
                    f"{req_url}?page={page}", headers
                )

    if package_sha:
        return asyncio.run_coroutine_threadsafe(
            scm_db_fill(host, org, repo, branch, sha, package_sha, submodule_branches),
            loop,
        ).result()


async def scm_db_fill(host, org, repo, branch, sha, pkgs_sha, branches):

    async for conn in get_db_session():
        last_update = ""

        await conn.execute(
            text("insert into scmhost(hostname) select :host on conflict do nothing;"),
            {"host": host},
        )

        scmrepo_id = None
        last_seen_package_at = None

        # get info from last scan
        row = await select_last_scan_details_for_scmrepo(conn, host, org, repo, branch)

        if row:
            if row["sha"] == sha:
                # we already scanned this sha
                continue

            last_seen_package_at = row.last_seen_package_at
            scmrepo_id = row.id
            await conn.execute(
                text(
                    "update scmrepo set sha = :sha, last_scan_at = now() where scmhost_id = :scmrepo_id"
                ),
                {"sha": sha, "scmrepo_id": scmrepo_id},
            )
        else:
            await conn.execute(
                text(
                    "insert into scmrepo(scmhost_id, org, repo, branch, sha) select (select id from scmhost where hostname = :host), :org, :repo, :branch, :sha"
                ),
                {"host": host, "org": org, "repo": repo, "branch": branch, "sha": sha},
            )

        for pkg in sorted(pkgs_sha):
            pkg_obj = PurePath(pkg)
            name = str(pkg_obj.name)

            if name.startswith("."):
                continue

            await conn.execute(
                text("insert into pkg(name) select :name on conflict do nothing"),
                {"name": name},
            )
            tpl = branches.get(pkg)
            if not tpl:
                print(f"Submodule {pkg} of {org}/{repo} has no details")
                continue

            (pkg_host, pkg_org, pkg_repo, pkg_branch) = tpl
            pkg_sha = pkgs_sha[pkg]

            await conn.execute(
                text(
                    "insert into scmpkg(scmrepo_id, pkg_id, host, org, repo, branch, sha, last_seen_at) select (select id from scmrepo where scmhost_id in (select id from scmhost where hostname = :host) and org = :org and repo = :repo and branch = :branch and sha = :sha), (select id from pkg where name = :name), :pkg_host, :pkg_org, :pkg_repo, :pkg_branch, :pkg_sha, now() on conflict(scmrepo_id, pkg_id)  do update set host = :pkg_host, org = :pkg_org, repo = :pkg_repo, branch = :pkg_branch, sha = :pkg_sha, last_seen_at = now(), deleted_at = NULL"
                ),
                {
                    "host": host,
                    "org": org,
                    "repo": repo,
                    "branch": branch,
                    "sha": sha,
                    "name": name,
                    "pkg_host": pkg_host,
                    "pkg_org": pkg_org,
                    "pkg_repo": pkg_repo,
                    "pkg_branch": pkg_branch,
                    "pkg_sha": pkg_sha,
                },
            )

        if last_seen_package_at:
            await conn.execute(
                text(
                    "update scmpkg set deleted_at = now() where scmrepo_id = :scmrepo_id and last_seen_at <= :last_seen_package_at"
                ),
                {
                    "scmrepo_id": scmrepo_id,
                    "last_seen_package_at": last_seen_package_at,
                },
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
