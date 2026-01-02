import subprocess
import re
import sys
from os import environ

# OBS_SCM_CACHE_OSC_COMMAND='osc -A https://api.suse.de' OBS_SCM_CACHE_GIT_OBS_COMMAND='git-obs -G https://src.suse.de' python3 osc_list_scmsync.py

OSC_COMMAND = environ.get("OBS_SCM_CACHE_OSC_COMMAND", "osc")
GIT_OBS_COMMAND = environ.get("OBS_SCM_CACHE_GIT_OBS_COMMAND", "git-obs")

CMD_LIST_PROJECTS = f"""
{OSC_COMMAND} api '/search/project?match=scmsync' | grep -oE 'project name="[^"]+"' | grep -v home: | grep -v Pull | grep -v PR | grep -v PTF | grep -oE '".*"' | grep -oE '[^\"]+'
"""

prj_res = subprocess.run(
    CMD_LIST_PROJECTS, stdout=subprocess.PIPE, shell=True, check=True
)

err = 0

for prj in prj_res.stdout.decode("utf-8").splitlines():
    try:
        scmsync_cmd = (
            f"{OSC_COMMAND} meta prj {prj} | grep scmsync | grep -oE 'http[^\\<]*'"
        )
        url = (
            subprocess.run(scmsync_cmd, stdout=subprocess.PIPE, shell=True, check=True)
            .stdout.decode("utf-8")
            .splitlines()[0]
        )

        match = re.match(
            r"^(https?://)?([^/]+)/([^/]+)/([^\/\#\.]+?)(\.git)?(\?[^#\/]*)?(\#([^\/#]+))?$",
            url,
        )

        if match:
            org = match.group(3)
            repo = match.group(4)
            branch = match.group(8)
            # scan if default branch is present. We better to specify it
            if org and repo and not branch:
                branch_cmd = f"""
{GIT_OBS_COMMAND} -q api /repos/{org}/{repo} 2>/dev/null | grep default_branch | head -n 1 | grep -oE ': ".*"' | grep -oE '[^\\ :\\"]+'
"""
                branch = (
                    subprocess.run(
                        branch_cmd, stdout=subprocess.PIPE, shell=True, check=True
                    )
                    .stdout.decode("utf-8")
                    .splitlines()[0]
                )
                url = f"{url}#{branch}"
    except Exception:
        import traceback

        print(f"Error parsing {prj}:", file=sys.stderr)
        print("Generic exception: " + traceback.format_exc(), file=sys.stderr)
        err = 1

    print(f"{prj},{url}")

exit(err)
