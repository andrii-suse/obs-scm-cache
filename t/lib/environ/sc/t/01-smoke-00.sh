set -euo pipefail
gt=$(environ gt)

$gt/start
$gt/status

$gt/curl -Is / | grep 200
curl -Is $($gt/print_address) | grep 200

$gt/stop

rc=0
$gt/status 2>/dev/null || rc=$?

test $rc -gt 0
echo PASS $0
