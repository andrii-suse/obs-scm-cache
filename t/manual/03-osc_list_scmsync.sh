#!lib/test-in-container-environ.sh
set -e

test -n "${OBS_SCM_CACHE_GITEA_TOKEN}" || exit 1

sc=$(environ sc $PWD)
$sc/start

$sc/osc_list_scmsync | $sc/obs_scan 

echo success
