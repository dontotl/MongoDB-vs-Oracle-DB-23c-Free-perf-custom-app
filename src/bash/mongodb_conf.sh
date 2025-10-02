sudo vi /etc/mongod.conf
#  bindIp: 127.0.0.1
bindIp: 0.0.0.0

sudo systemctl restart mongod
