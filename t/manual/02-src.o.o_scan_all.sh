#!lib/test-in-container-environ.sh
set -e

sc=$(environ sc $PWD)

echo '
devel:ALP,https://src.opensuse.org/adrianSuSE/Alp#factory
devel:Factory:git-workflow:mold:core:git,https://src.opensuse.org/testing/_ObsPrj.git#master
devel:gcc:prjbuild,https://src.opensuse.org/gcc/_ObsPrj.git#master
devel:languages:clojure,https://src.opensuse.org/clojure/_ObsPrj.git#master
devel:languages:erlang:Factory,https://src.opensuse.org/erlang/_ObsPrj.git?#master
devel:languages:erlang,https://src.opensuse.org/erlang/_ObsPrj.git#master
devel:languages:hare,https://src.opensuse.org/hare/_ObsPrj.git#master
devel:languages:javascript,https://src.opensuse.org/javascript/_ObsPrj.git#master
devel:languages:lua,https://src.opensuse.org/lua/_ObsPrj.git#master
devel:languages:nodejs,https://src.opensuse.org/nodejs/_ObsPrj.git#master
devel:languages:perl,https://src.opensuse.org/perl/_ObsPrj#master
devel:languages:python:Factory,https://src.opensuse.org/python-interpreters/_ObsPrj#main
devel:languages:python:pytest,https://src.opensuse.org/python-pytest/_ObsPrj.git#main
devel:openSUSE:Factory,https://src.opensuse.org/devel-factory/_ObsPrj.git#master
devel:UnifiedCore:Dev,https://github.com/davidcassany/elemental-obs#dev
isv:Rancher:Elemental:Dev,https://github.com/rancher/elemental-obs#dev
isv:Rancher:Elemental:Maintenance:6.1,https://github.com/rancher/elemental-obs#maintenance_6.1
isv:Rancher:Elemental:Staging,https://github.com/rancher/elemental-obs#staging
isv:SUSE:Edge:Factory:Devel,https://src.opensuse.org/suse-edge/Factory#devel
Java:packages,https://src.opensuse.org/java-packages/_ObsPrj#main
Kernel:firmware,https://src.opensuse.org/kernel-firmware/_ObsPrj.git#master
Kernel:kdump,https://src.opensuse.org/kernel-kdump/_ObsPrj#master
network:chromium,https://src.opensuse.org/chromium/_ObsPrj.git#master
network:dhcp,https://src.opensuse.org/dhcp/_ObsPrj.git#master
network:im:whatsapp,https://src.opensuse.org/whatsapp/_ObsPrj.git#master
network:messaging:xmpp,https://src.opensuse.org/xmpp/_ObsPrj.git#master
openSUSE:Backports:SLE-16.0,https://src.opensuse.org/products/PackageHub#leap-16.0
openSUSE:Backports:SLE-16.1,https://src.opensuse.org/products/PackageHub#leap-16.1
openSUSE:Factory:git,https://src.opensuse.org/opensuse/Factory#main
openSUSE:Leap:16.0,https://src.opensuse.org/openSUSE/Leap#leap-16.0
openSUSE:Leap:16.0:Images,https://src.opensuse.org/openSUSE/Leap-Images#leap-16.0
openSUSE:Leap:16.0:NonFree,https://src.opensuse.org/openSUSE/LeapNonFree#leap-16.0-nonfree
openSUSE:Leap:16.1,https://src.opensuse.org/openSUSE/Leap#leap-16.1
openSUSE:Leap:16.1:NonFree,https://src.opensuse.org/openSUSE/LeapNonFree#leap-16.1-nonfree
science:GPU:ROCm:Devel,https://src.opensuse.org/ROCmWork/_ObsPrj#devel
science:GPU:ROCm,https://src.opensuse.org/ROCm/_ObsPrj#master
science:GPU:ROCm:Work,https://src.opensuse.org/ROCmWork/_ObsPrj#master
science:HPC,https://src.opensuse.org/HPC/_ObsPrj#master
server:dns,https://src.opensuse.org/dns/_ObsPrj.git#master
SUSE:ALP:Source:Standard:Core:1.0:Build,https://src.opensuse.org/products/SUSE_ALP_Standard#1.0
SUSE:SLFO:1.1:Build,https://src.opensuse.org/products/SLFO#1.1
SUSE:SLFO:1.2,https://src.opensuse.org/products/SLFO#slfo-1.2
SUSE:SLFO:Kernel:1.0:Build,https://src.opensuse.org/products/SLFO_Kernel#1.0
SUSE:SLFO:Main:Build,https://src.opensuse.org/products/SLFO#main
SUSE:SLFO:Main,https://src.opensuse.org/products/SLFO#slfo-main
systemsmanagement:cockpit,https://src.opensuse.org/cockpit/_ObsPrj.git#master
systemsmanagement:saltstack:bundle:scm,https://src.opensuse.org/saltbundle/_ObsPrj#bundle
systemsmanagement:saltstack:bundle:scm:next,https://src.opensuse.org/saltbundle/_ObsPrj#bundle_next
systemsmanagement:saltstack:bundle:scm:testing,https://src.opensuse.org/saltbundle/_ObsPrj#bundle_testing
Virtualization:Appliances:Images:openSUSE-Leap-16.0,https://src.opensuse.org/lkocman/opensuse-oem-image.git#leap-16.0
Virtualization:SGX,https://src.opensuse.org/SGX/_ObsPrj#master
X11:lxde,https://src.opensuse.org/lxde/_ObsPrj.git#master
' | $sc/obs_scan


$sc/sql "select count(*) from scmrepo"

$sc/sql "select pkg.name, count(*) cnt, string_agg(obsproj.name, ',') from scmpkg join scmrepo on scmrepo_id = scmrepo.id join obsproj on obsproj.scmsync like concat('%',scmrepo.org,'/',scmrepo.repo,'%','#',scmrepo.branch) join pkg on pkg.id = pkg_id group by pkg.id, pkg.name order by cnt desc" | head

$sc/start
sleep 3
$sc/curl /rest/package/search?q=7zip | grep -o '"appliance":"src.opensuse.org"'

echo success
