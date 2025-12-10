# AppArmor profile is overtuned and doesn't allow gitea to run as normal user
aa-disable /etc/apparmor.d/usr.bin.gitea
