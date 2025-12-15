#!lib/test-in-container-environ.sh
set -ex

sc=$(environ sc $PWD)

$sc/start || ( cat $sc/.cout ; cat $sc/.cerr )
$sc/status

$sc/sql "insert into pkg(name) select 'vim' union select 'emacs'"
$sc/sql "insert into scmhost(hostname) select 'src.mytest.org'"
$sc/sql "insert into scmrepo(scmhost_id, org, repo, branch, sha) select 1, 'myorg', 'myproj', 'master', '0ab'"
$sc/sql "insert into scmpkg(scmrepo_id, pkg_id, host, org, repo, branch, sha) select 1, 1, 'host', 'org', 'repo', 'branch', 'sha' union select 1, 2, 'host', 'org', 'repo', 'branch', 'sha'"

$sc/sql "insert into obsproj(name,scmsync) select 'myhomeproject','src.mytest.org/myorg/myproj#master'"

$sc/status
sleep 3 # not sure why we need it
$sc/curl "/rest/package/search?q=vim" || rc=$?
echo RC=$rc

$sc/curl "/rest/package/search?q=vim" | grep 'myorg' # | grep src.mytest.org

echo success
