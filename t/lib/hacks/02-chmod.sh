# permissions are overtuned - there should be no sensitive options
chmod 755 /usr/share/gitea
chmod 755 /usr/share/gitea/*
chmod 755 /usr/share/gitea/public/
chmod 755 /usr/share/gitea/public/assets/
chmod 755 /usr/share/gitea/public/assets/img/
chmod 755 /usr/share/gitea/public/assets/img/svg
chmod 664 /usr/share/gitea/public/assets/img/svg/*.svg
chmod 755 /usr/share/gitea/options/
chmod -R a+rX /usr/share/gitea/templates/
chmod -R a+rX /usr/share/gitea/options/
