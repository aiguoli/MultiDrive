echo "Guess what? Shell script is so difficult for me that I can' t work it out"
echo "This is a unfinished script!"

sudo apt update
sudo apt upgrade -y

sudo apt install supervisor nginx mysql-server -y
sudo apt-get install python-dev default-libmysqlclient-dev

echo "接下来设置MySQL密码"

sudo mysql_secure_installation

sed 's/[mysql]/[mysqld]
character-set-server=utf8mb4
collation-server=utf8mb4_unicode_ci

[client]
default-character-set = utf8mb4

[mysql]
default-character-set = utf8mb4/g' /etc/mysql/conf.d/mysql.cnf >/etc/mysql/conf.d/mysql.cnf

cd /
sudo mkdir www && cd www && mkdir wwwroot && cd wwwroot || exit
git clone git@github.com:aiguoli/MultiDrive.git
cd MultiDrive && sudo chmod 777 /www/wwwroot/MultiDrive || exit

python3 -m venv multi-venv
source multi-venv/bin/activate
pip3 install -Ur requirements.txt
