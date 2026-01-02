create table if not exists scmhost (
    id serial NOT NULL PRIMARY KEY,
    name      varchar(512),
    hostname  varchar(512) unique
);

create table if not exists scmrepo (
    id serial NOT NULL PRIMARY KEY,    
    scmhost_id int references scmhost,
    org varchar(512) not null,
    repo varchar(512) not null,
    branch varchar(512) not null,
    sha char(64)     not null,
    last_scan_at timestamp,
    deleted_at   timestamp,
    unique(scmhost_id, org, repo, branch)
);

create table if not exists pkg (
    id serial NOT NULL PRIMARY KEY,    
    name        varchar(256) unique
);

create table if not exists scmpkg (
    id serial NOT NULL PRIMARY KEY,    
    scmrepo_id   int references scmrepo,
    pkg_id       int references pkg,
    host   varchar(512) not null,
    org    varchar(512) not null,
    repo   varchar(512) not null,
    branch varchar(512) not null,
    sha    varchar(64)  not null,
    last_seen_at timestamp,
    deleted_at   timestamp,
    unique(scmrepo_id, pkg_id)
);

create table if not exists obsproj (
    name  varchar(512) PRIMARY KEY,
    scmsync varchar(512) not null
);
