#!lib/test-in-container-environ.sh
set -e

sc=$(environ sc $PWD)

$sc/gitea_scan https://src.opensuse.org/cockpit/_ObsPrj#master

$sc/sql "select name from pkg"

$sc/sql "select
-- obsproj.name,
scmpkg.host as appliance, 
scmrepo.org as project_org, scmrepo.repo as project_repo, scmrepo.branch as project_branch,
scmpkg.org as package_org, scmpkg.repo as package_repo, scmpkg.branch as package_branch, scmpkg.sha as package_sha
from
pkg
join scmpkg on pkg_id = pkg.id
join scmrepo on scmrepo_id = scmrepo.id
-- join obsproj on obsproj.scmsync like concat('%',scmrepo.org,'/',scmrepo.repo,'%','#',scmrepo.branch)
where pkg.name = 'cockpit'
"

$sc/sql "insert into obsproj(name,scmsync) select 'systemsmanagement:cockpit','https://src.opensuse.org/cockpit/_ObsPrj.git#master'"

$sc/sql "select
obsproj.name,
scmpkg.host as appliance, 
scmrepo.org as project_org, scmrepo.repo as project_repo, scmrepo.branch as project_branch,
scmpkg.org as package_org, scmpkg.repo as package_repo, scmpkg.branch as package_branch, scmpkg.sha as package_sha
from
pkg
join scmpkg on pkg_id = pkg.id
join scmrepo on scmrepo_id = scmrepo.id
join obsproj on obsproj.scmsync like concat('%',scmrepo.org,'/',scmrepo.repo,'%','#',scmrepo.branch)
where pkg.name = 'cockpit'
"



$sc/start

$sc/sql_test 1 == "select count(*) from scmhost"
$sc/sql_test src.opensuse.org == "select hostname from scmhost"


$sc/sql_test 1 == "select count(*) from scmhost"
$sc/sql_test src.opensuse.org == "select hostname from scmhost"

$sc/sql_test 1 == "select count(*) from scmrepo"
$sc/sql_test cockpit/_ObsPrj == "select concat(org,'/',repo) from scmrepo"


$sc/sql "select name from pkg"

$sc/sql_test 11 == "select count(*) from scmpkg"

$sc/sql_test abrooks == "select min(maintainer) from scmrepo_maintainer"

sleep 3
$sc/curl /rest/package/search?q=cockpit


echo success
