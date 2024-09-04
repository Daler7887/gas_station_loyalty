#!/bin/bash

mkdir logs

echo "Project title:"
read project_title
echo "User: "
read user
echo "Secret key: "
read secret_key
echo "Database user: "
read db_user
echo "Database password"
read db_password
echo "Bot token: "
read bot_token
echo "Project port"
read port
echo "Project domain"
read domain

cp conf/env .env
sed -i "s/<secret_key>/$secret_key/g" ".env"
sed -i "s/<db_name>/$project_title/g" ".env"
sed -i "s/<db_user>/$db_user/g" ".env"
sed -i "s/<db_password>/$db_password/g" ".env"
sed -i "s/<bot_token>/$bot_token/g" ".env"
sed -i "s/<domain>/$domain/g" ".env"

createdb $project_title

pip3 install -r requirements.txt
python3 manage.py migrate
python3 manage.py makemigrations app
python3 manage.py makemigrations bot
python3 manage.py migrate app
python3 manage.py migrate bot
python3 manage.py collectstatic
python3 manage.py createsuperuser

touch $project_title
sed -i "s/<title>/$project_title/g" "conf/supervisor.conf"
sed -i "s/<folder>/$project_title/g" "conf/supervisor.conf"
sed -i "s/<port>/$port/g" "conf/supervisor.conf"
sed -i "s/<user>/$user/g" "conf/supervisor.conf"
sudo cp conf/supervisor.conf /etc/supervisor/conf.d/$project_title.conf
sudo supervisorctl reread
sudo supervisorctl update

sed -i "s/<domain>/$domain/g" "conf/nginx.conf"
sed -i "s/<user>/$user/g" "conf/nginx.conf"
sed -i "s/<folder>/$project_title/g" "conf/nginx.conf"
sed -i "s/<port>/$port/g" "conf/nginx.conf"
sudo cp conf/nginx.conf /etc/nginx/sites-enabled/$project_title.conf
sudo nginx -t
echo "Continue?"
read qwerty

sudo certbot --nginx

sudo service nginx reload

curl "https://api.telegram.org/bot$bot_token/setWebhook?url=https://$domain/$bot_token"


echo "Installation complete"

