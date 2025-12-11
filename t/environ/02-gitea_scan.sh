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
$gt/admin/create_repo bobshome myrepo
##############

echo setup homes repo
(
git clone http://$(cat $gt/bob/token.txt)@$($gt/print_address)/bobshome/myrepo $sc/dt/myrepo
cd $sc/dt/myrepo
git checkout -b main
echo README > README.txt
git add README.txt
git config user.name "Geeko Packager"
git config user.email "email@example.com"

git commit -m 'Add README.txt'
git push origin main
)
echo setup product
(
git clone http://$(cat $gt/bob/token.txt)@$($gt/print_address)/products/myproduct1 $sc/dt/myproduct1
cd $sc/dt/myproduct1
git branch -m mybranch
git submodule add http://$(cat $gt/bob/token.txt)@$($gt/print_address)/bobshome/myrepo
git add *
git config user.name "Geeko Packager"
git config user.email "email@example.com"
git commit -m 'Add myrepo'
git push origin mybranch
)



$sc/status
sleep 3 # not sure why we need it

$sc/gitea_scan http://$($gt/print_address)/products/myproduct1#mybranch

set -x

$sc/sql_test 1 == "select count(*) from scmhost"
$sc/sql_test $($gt/print_address) == "select hostname from scmhost"

$sc/sql_test 1 == "select count(*) from scmrepo"
$sc/sql_test products/myproduct1 == "select concat(org,'/',repo) from scmrepo"

$sc/sql_test 1 == "select count(*) from scmpkg"
$sc/sql_test myrepo == "select name from pkg"

echo success
