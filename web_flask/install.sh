#!/usr/bin/env bash
# mysql Install

apt-get install mysql-server
vi /etc/mysql/mysql.conf.d/mysqld.cnf
# bind-address              = 127.0.0.1

service mysql stop
usermod -d /var/lib/mysql/ mysql
service mysql start

mysql -u root -p
mysql> GRANT ALL PRIVILEGES ON *.* TO root@'%' IDENTIFIED BY 'password' WITH GRANT OPTION;
mysql> FLUSH PRIVILEGES;
mysql> quit
servcie mysql restart


# python install

apt-get update
apt-get install python3-pip -y
pip3 install virtualenv

mkdir /env
cd /env
virtualenv sanic
echo "function env(){ source /env/\$1/bin/activate; }" >> ~/.bashrc


# scrapy
apt-get install libssl-dev -y
source /env/scrapy/bin/activate
pip install scrapy peewee pymysql wechatpy


# flask
pip install falsk
pip install peewee pymysql requests xmltodict qrcode Pillow
pip install uwsgi









# docker install

apt-get install docker.io
docker pull ubuntu:16.10

docker run -dit --name=python35 ubuntu16.10
docker attach python35

# docker save

docker commit python35 python35:sanic
docker save -o docker_python35.tar python35:sanic


# zb123
docker run -dit --name=zb123 --net=host -v /prj:/prj zb123:3.3.5

# mysql
docker run -dit --name=r_mysql --restart=always -p 3306:3306 zb123:3.3.1
docker exec r_mysql service mysql start

# fetch
docker run -dit --name=r_fetch --net=host -v /prj:/prj zb123:3.3.6 ~/fetch.sh

# flask
docker run -dit --name=r_flask --net=host -v /prj:/prj zb123:3.3.6 ~/flask.sh
# uwsgi
docker run -dit --name=r_uwsgi --restart=always --net=host -v /prj:/prj zb123:3.3.6 ~/uwsgi.sh
