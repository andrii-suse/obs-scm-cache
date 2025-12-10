mkdir -p __workdir/dt
__workdir/gen_env
set -a
source __workdir/conf.env
set +a

test ! -z "$USER" || export USER=$(id -u)

test 1 != "${ENVIRON_SC_DB_AUTOSTART-1}" || __workdir/db/status >& /dev/null || __workdir/db/start

[ -e __workdir/db/sql_$USER ] || { 
	__workdir/db/create_db $USER
	__workdir/db/sql -f __srcdir/sql/ddl.sql # TBD deployment probably will be moved to app
}

(
    cd __srcdir

    python3 main.py >> __workdir/.cout 2>> __workdir/.cerr &
    pid=$!
    echo $pid > __workdir/.pid
)
sleep 0.1
__workdir/status || sleep 0.1
__workdir/status || sleep 0.2
__workdir/status || sleep 0.3
__workdir/status || sleep 0.4
__workdir/status || sleep 0.5
