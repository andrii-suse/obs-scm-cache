#!/usr/bin/python3
import sys

from app.config import settings
from app.database import get_db_session
from model.model import Obsproj

import asyncio
import threading
import urllib3
import json
import re
from typing import Annotated
from fastapi import Depends
from sqlalchemy.sql import text
from sqlalchemy.ext.asyncio import AsyncSession
from gitea_scan import git_tree_scan


http = urllib3.PoolManager()


async def obs_scan(obsproj_dict):
    if not obsproj_dict:
        return

    async for conn in get_db_session():
        await conn.execute(
            text(
                f"delete from obsproj where 1=1"
            )
        )
        # sql = '''insert into obsproj(name, scmsync) select $1,$2;'''
        # await conn.execute_many(sql, obsproj_dict.items())

        await conn.run_sync(lambda session: session.bulk_save_objects(
            [
                Obsproj(
                    name = k,
                    scmsync = obsproj_dict[k],
                )
                for k in sorted(obsproj_dict)
            ],
        ))
        await conn.commit()
        break


def main():
    def thr(loop):
        asyncio.set_event_loop(loop)
        loop.run_forever()

    loop = asyncio.new_event_loop()
    t = threading.Thread(target=thr, args=(loop,), daemon=True)
    t.start()


    obsproj_dict = {}

    for line in sys.stdin:
        line = line.strip().split(",")
        if len(line)>1:
            k = line[0]
            v = line[1]
            obsproj_dict[k] = v

    asyncio.run_coroutine_threadsafe(
        obs_scan(obsproj_dict), loop
    ).result()

    err = 0
    for v in set(obsproj_dict.values()):
        err1 = git_tree_scan(v, loop)
        if err1:
            err = err1

    return err


if __name__ == "__main__":
    err = 0
    try:
        err = main()
    except Exception:
        import traceback
        print("Generic exception: " + traceback.format_exc())
        err = 1
    except:
        print("Not an exception")
        err = 1

    exit(err)

print("obs_scan done")
