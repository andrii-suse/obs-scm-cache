#!lib/test-in-container-environ.sh
set -ex

test -n "${OBS_SCM_CACHE_GITEA_TOKEN}" || { echo OBS_SCM_CACHE_GITEA_TOKEN is not set; exit; }

sc=$(environ sc $PWD)
$sc/start

$sc/osc_list_scmsync | $sc/obs_scan 

echo success
