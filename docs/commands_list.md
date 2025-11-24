Command list, more for myself, but if it helps someone.

Create conda environment with Python 3.12
    conda create --name tradingbot312 python=3.12

Install vectorbtpro
   pip install -U "vectorbtpro[all-stable] @ git+https://${GITHUB_TOKEN}@github.com/polakowo/vectorbt.pro.git"

Install redis: 
   apt-get install redis

Install postgresql: apt-get install postgresql
    sudo -u postgres -i
    \psql
    CREATE DATABASE pgtradingbotdb;
    CREATE USER <username> WITH PASSWORD <password>;
    \c pgtradingbotdb
    GRANT ALL PRIVILEGES ON DATABASE pgtradingbotdb TO <username>;
    GRANT ALL PRIVILEGES ON SCHEMA public TO <username>;
    ALTER USER <username> CREATEDB; ###For testing

For jupyter notebook to find the venv:
    python -m ipykernel install --user --name tradingbot312
    
Export the dump:
    python manage.py dumpdata -exclude=auth -exclude=reporting > dump.json
    
Start unit tests:
    python manage.py test


