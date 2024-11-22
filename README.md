Запускать через терминал: \
uvicorn main:app \

Для работы с проектом надо скачать PostgreSQL. Вот инструкция как это сделать.\

Открываем терминал в нашем IDE и пишем следующие команды:\

Скачать на MacOS:\
brew install postgresql\
brew services start postgresql\

Скачать на Ubuntu:\
sudo apt install postgres\

Дальше инструкция для всех одинаковая:\
whoami #получаем имя пользователя\
psql -U 'имя пользователя' -d postgres\
CREATE DATABASE mydatabase; #создаем нашу базу данных, команду обязательно написать с ;\
\l #принтим всем дб, которые созданы на вашем компе\
\q #закрываем\


После установки PostgreSQL надо зайти в файл .env и поменять DB_user на имя пользователя (то, что вывела команда whoami) и так же поменять DB_PASSWORD. Вот команды для изменения пароля:\

sudo -u postgres psql\
\c название_базы_данных\
ALTER USER имя_пользователя WITH PASSWORD 'новый_пароль';\
\q\
