mkdir -p __workdir/dt
__workdir/gen_env
set -a
source __workdir/conf.env
set +a

test 1 != "${ENVIRON_SC_DB_AUTOSTART-1}" || __workdir/db/status >& /dev/null || __workdir/db/start

test ! -z "$USER" || export USER=$(id -u)
[ -e __workdir/db/sql_$USER ] || { 
	__workdir/db/create_db $USER
	__workdir/db/sql -f __srcdir/sql/ddl.sql # TBD deployment probably will be moved to app
}

python3 __srcdir/gitea_scan.py "$@"
