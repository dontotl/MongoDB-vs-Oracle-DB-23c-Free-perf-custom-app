sudo firewall-cmd --zone=public --permanent --add-port=1521/tcp
sudo firewall-cmd --zone=public --permanent --add-port=27017/tcp
sudo firewall-cmd --reload
