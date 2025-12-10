set -e
[ -e __workdir/conf.env ] || (

    echo export OBS_SCM_CACHE_DB_URL=postgresql+asyncpg://mytest?host=__workdir/db/dt/
    echo export OBS_SCM_CACHE_PORT=__port

    for i in "$@"; do
        [ -z "$i" ] || echo "export $i" >> __workdir/conf.env
    done
) > __workdir/conf.env
