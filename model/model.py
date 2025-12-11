from typing import Optional
import datetime

from sqlalchemy import DateTime, ForeignKeyConstraint, Integer, PrimaryKeyConstraint, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Pkg(Base):
    __tablename__ = 'pkg'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='pkg_pkey'),
        UniqueConstraint('name', name='pkg_name_key')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(String(256))

    scmpkg: Mapped[list['Scmpkg']] = relationship('Scmpkg', back_populates='pkg')


class Scmhost(Base):
    __tablename__ = 'scmhost'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='scmhost_pkey'),
        UniqueConstraint('hostname', name='scmhost_hostname_key')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(String(512))
    hostname: Mapped[Optional[str]] = mapped_column(String(512))

    scmrepo: Mapped[list['Scmrepo']] = relationship('Scmrepo', back_populates='scmhost')


class Scmrepo(Base):
    __tablename__ = 'scmrepo'
    __table_args__ = (
        ForeignKeyConstraint(['scmhost_id'], ['scmhost.id'], name='scmrepo_scmhost_id_fkey'),
        PrimaryKeyConstraint('id', name='scmrepo_pkey'),
        UniqueConstraint('scmhost_id', 'org', 'repo', 'branch', name='scmrepo_scmhost_id_org_repo_branch_key')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    org: Mapped[str] = mapped_column(String(512), nullable=False)
    repo: Mapped[str] = mapped_column(String(512), nullable=False)
    branch: Mapped[str] = mapped_column(String(512), nullable=False)
    scmhost_id: Mapped[Optional[int]] = mapped_column(Integer)
    last_scan_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    deleted_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)

    scmhost: Mapped[Optional['Scmhost']] = relationship('Scmhost', back_populates='scmrepo')
    scmpkg: Mapped[list['Scmpkg']] = relationship('Scmpkg', back_populates='scmrepo')


class Scmpkg(Base):
    __tablename__ = 'scmpkg'
    __table_args__ = (
        ForeignKeyConstraint(['pkg_id'], ['pkg.id'], name='scmpkg_pkg_id_fkey'),
        ForeignKeyConstraint(['scmrepo_id'], ['scmrepo.id'], name='scmpkg_scmrepo_id_fkey'),
        PrimaryKeyConstraint('id', name='scmpkg_pkey')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scmrepo_id: Mapped[Optional[int]] = mapped_column(Integer)
    pkg_id: Mapped[Optional[int]] = mapped_column(Integer)
    last_seen_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    deleted_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)

    pkg: Mapped[Optional['Pkg']] = relationship('Pkg', back_populates='scmpkg')
    scmrepo: Mapped[Optional['Scmrepo']] = relationship('Scmrepo', back_populates='scmpkg')


class Obsproj(Base):
    __tablename__ = 'obsproj'
    __table_args__ = (
        PrimaryKeyConstraint('name', name='obsproj_pkey'),
    )

    name: Mapped[Optional[str]] = mapped_column(String(256))
    scmsync: Mapped[Optional[str]] = mapped_column(String(256))

