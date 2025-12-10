#!lib/test-in-container-environ.sh
set -e

sc=$(environ sc $PWD)

$sc/gitea_scan https://src.opensuse.org/cockpit/_ObsPrj#master

$sc/sql_test 1 == "select count(*) from scmhost"
$sc/sql_test src.opensuse.org == "select hostname from scmhost"

$sc/sql_test 1 == "select count(*) from scmrepo"
$sc/sql_test cockpit/_ObsPrj == "select uri from scmrepo"


$sc/sql "select name from pkg"

$sc/sql_test 10 == "select count(*) from scmpkg"

echo success
