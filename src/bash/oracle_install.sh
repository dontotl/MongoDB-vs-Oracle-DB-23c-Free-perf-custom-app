sudo yum config-manager --set-enabled ol8_developer
sudo yum -y install oracle-database-preinstall-23c
sudo wget https://download.oracle.com/otn-pub/otn_software/db-free/oracle-database-free-23c-1.0-1.el8.x86_64.rpm
sudo yum -y install oracle-database-free-23c-1.0-1.el8.x86_64.rpm

sudo /etc/init.d/oracle-free-23c configure
