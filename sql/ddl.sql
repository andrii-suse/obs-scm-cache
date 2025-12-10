create table if not exists scmhost (
    id serial NOT NULL PRIMARY KEY,
    name      varchar(512),
    hostname  varchar(512) unique
);

create table if not exists scmrepo (
    id serial NOT NULL PRIMARY KEY,    
    scmhost_id int references scmhost,
    uri varchar(512) not null,
    last_scan_at timestamp,
    deleted_at   timestamp,
    unique(scmhost_id, uri)
);

create table if not exists pkg (
    id serial NOT NULL PRIMARY KEY,    
    name        varchar(256) unique
);

create table if not exists scmpkg (
    id serial NOT NULL PRIMARY KEY,    
    scmrepo_id   int references scmrepo,
    pkg_id       int references pkg,
    last_seen_at timestamp,
    deleted_at   timestamp
);
