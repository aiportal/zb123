#!/usr/bin/env bash



""" mysql Install """
apt-get update && apt-get upgrade -y
apt-get install mysql-server -y
apt-get install vim -y
vi /etc/mysql/mysql.conf.d/mysqld.cnf
# bind-address              = 127.0.0.1

service mysql stop
usermod -d /var/lib/mysql/ mysql        # change default login directory
service mysql start

mysql -u root -p
mysql> GRANT ALL PRIVILEGES ON *.* TO root@'%' IDENTIFIED BY 'Bayesian@2018' WITH GRANT OPTION;
mysql> FLUSH PRIVILEGES;
mysql> quit
service mysql restart



""" python install """

apt-get update && apt-get upgrade -y
apt-get install python3-pip -y
pip3 install --upgrade pip          # upgrade to 9.0.1
pip3 install virtualenv

mkdir /env
cd /env
virtualenv scrapy
# echo "function ve(){ source /env/\$1/bin/activate; }" >> ~/.bashrc


# scrapy
apt-get install libssl-dev -y
source /env/scrapy/bin/activate
pip install scrapy
pip install peewee pymysql wechatpy


# flask
pip install flask uwsgi gevent peewee pymysql redis
pip install wechatpy flask-wechatpy wechatpy[pycrypto]
pip install jieba qrcode Pillow











# docker install

apt-get install docker.io
docker pull ubuntu:16.04

docker run -dit --name=python35 ubuntu16.10
docker attach python35

# docker save

docker commit python35 python35:sanic
docker save -o docker_python35.tar python35:sanic
tar -zcvf mysql_v11.tar

# mysql
sudo docker run -dit --name=r_mysql --restart=always -p 3306:3306 -v /prj:/prj zb123:3.3.1
sudo docker exec r_mysql service mysql start

# zb123
docker run -dit --name=zb123 --net=host -v /prj:/prj zb123:3.3.6

# fetch
docker run -dit --name=r_fetch --net=host -v /prj:/prj zb123:3.3.6 ~/fetch.sh
# proxy
docker run -dit --name=r_proxy --restart=always -p 8088:8000 proxy:1.1 bash /root/start.sh

# flask
docker run -dit --name=r_flask --net=host -v /prj:/prj zb123:3.3.6 ~/flask.sh
# uwsgi
docker run -dit --name=r_uwsgi --restart=always --net=host -v /prj:/prj zb123:3.3.6 ~/uwsgi.sh



# wordpress
docker run -dit --name=r_wp --restart=always -p 8080:80 wordpress:1.0

apt-get update && apt-get upgrade -y

apt-get install php -y
apt-get install php-mysql -y
service php7.0-fpm start

apt-get install nginx
vi /etc/nginx/sites-avalide/wp

apt-get install mysql-server
mysql -u root -p
mysql> create database wordpress

wget https://cn.wordpress.org/wordpress-4.7.4-zh_CN.tar.gz

# http://localhost:8080/












service mysql stop
usermod -d /var/lib/mysql/ mysql        # change default login directory
service mysql start
