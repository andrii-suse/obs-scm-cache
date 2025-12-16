#!lib/test-in-container-environ.sh
set -e

sc=$(environ sc $PWD)

$sc/start
$sc/status


gt=$(environ gt)

##############
echo setup repos
$gt/start
$gt/bob/create

$gt/admin/create
$gt/admin/create_org bob products
$gt/admin/create_repo products myproduct1
$gt/admin/create_org bob bobshome
$gt/admin/create_repo bobshome myrepo1
$gt/admin/create_repo bobshome myrepo2
##############

echo setup homes repo
(
git clone http://$(cat $gt/bob/token.txt)@$($gt/print_address)/bobshome/myrepo1 $sc/dt/myrepo1
cd $sc/dt/myrepo1
git checkout -b main
echo README > README.txt
git add README.txt
git config user.name "Geeko Packager"
git config user.email "email@example.com"

git commit -m 'Add README.txt'
git push origin main

git checkout -b dev
git push origin dev

)
(
git clone http://$(cat $gt/bob/token.txt)@$($gt/print_address)/bobshome/myrepo2 $sc/dt/myrepo2
cd $sc/dt/myrepo2
git checkout -b main
echo README > README.txt
git add README.txt
git config user.name "Geeko Packager"
git config user.email "email@example.com"

git commit -m 'Add README2.txt'
git push origin main

git checkout -b dev
git push origin dev
git checkout -b tst
git push origin tst
git checkout -b nope
git push origin nope

)
echo setup product
(
git clone http://$(cat $gt/bob/token.txt)@$($gt/print_address)/products/myproduct1 $sc/dt/myproduct1
cd $sc/dt/myproduct1
git branch -m mybranch
# this one is not in the _manifest, should not appear in the DB
git submodule add -b nope http://$(cat $gt/bob/token.txt)@$($gt/print_address)/bobshome/myrepo2
mkdir packs
mkdir deps
git submodule add -b dev http://$(cat $gt/bob/token.txt)@$($gt/print_address)/bobshome/myrepo1 packs/myrepo1
git submodule add -b main http://$(cat $gt/bob/token.txt)@$($gt/print_address)/bobshome/myrepo2 packs/myrepo2
git submodule add -b main http://$(cat $gt/bob/token.txt)@$($gt/print_address)/bobshome/myrepo1 deps/myrepo1
git submodule add -b main http://$(cat $gt/bob/token.txt)@$($gt/print_address)/bobshome/myrepo2 deps/myrepo2-main
git submodule add -b tst http://$(cat $gt/bob/token.txt)@$($gt/print_address)/bobshome/myrepo2 deps/myrepo2-tst

echo '---
packages: []
subdirectories:
  - packs
  - deps

obs_project: "test:mytest"
obs_apiurl: "https://api.myapi.org"' > _manifest

git add *
git config user.name "Geeko Packager"
git config user.email "email@example.com"
git commit -m 'Add myrepo'
git push origin mybranch

ls -la
cat .gitmodules
)


$sc/status
sleep 1 # not sure why we need it

$sc/gitea_scan http://$($gt/print_address)/products/myproduct1#mybranch

set -x

$sc/sql_test 1 == "select count(*) from scmhost"
$sc/sql_test $($gt/print_address) == "select hostname from scmhost"

$sc/sql_test 1 == "select count(*) from scmrepo"
$sc/sql_test products/myproduct1 == "select concat(org,'/',repo) from scmrepo"

$sc/sql "select * from pkg"

$sc/sql "select * from scmpkg"

$sc/sql_test 4 == "select count(*) from scmpkg"
$sc/sql_test 0 == "select count(*) from scmpkg where branch = 'nope'"
$sc/sql_test 4 == "select count(*) from pkg"
echo success
