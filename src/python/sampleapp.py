import logging, cx_Oracle
from datetime import datetime
from pymongo import MongoClient
import json
from flask import Flask
from faker import Faker

app = Flask(__name__)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
fake=Faker()

ora_db_host_ip = '10.0.1.18'
ora_db_svc_name = 'testdb'
ora_db_user_name = 'system'
ora_db_passwd = 'TESTdb#01'

mongo_db_host_ip = '10.0.1.18'
mongo_db_host_port = 27017
mongo_db_user_name = 'mongo'
mongo_db_passwd = 'mongo'
        
mongo_client = MongoClient(mongo_db_host_ip, mongo_db_host_port, username=mongo_db_user_name, password=mongo_db_passwd)
oradb_conn = cx_Oracle.connect(ora_db_user_name, ora_db_passwd, ora_db_host_ip + '/' + ora_db_svc_name)
oradb_cursor = oradb_conn.cursor()

@app.route('/mongo/insert')
def mongo_insert():
    try:
        mongo_db = mongo_client.test
        mongo_collection = mongo_db.sample
        sample = [{"user_name": fake.name(),"last_conn_date": datetime.now()}]
        mongo_collection.insert_many(sample)
    except Exception as e:
        logger.error(e)
    return "200"

@app.route('/mongo/select')
def mongo_query():
    try:
        mongo_db = mongo_client.test
        mongo_collection = mongo_db.sample
        mongo_objects = mongo_client.test.sample.find().sort("_id",-1).limit(1)
        mongo_result = str(json.dumps({'results': list(mongo_objects)}, default=str, indent=4))
    except Exception as e:
        logger.error(e)
    return str(mongo_result)

@app.route('/oracle/insert')
def oracle_insert():
    try:
        sample_data ={"user_name": fake.name(),"last_conn_date": datetime.now()}
        oradb_sql_val = json.dumps(sample_data, ensure_ascii=False, default=str)
        oradb_sql = "insert into sample(id, json_data) values (sys_guid(), '" + oradb_sql_val +"')" 
        oradb_cursor.execute(oradb_sql)
        oradb_conn.commit()
    except Exception as e:
        logger.error(e)
    return "200"

@app.route('/oracle/select')
def oracle_query():
    try:
        oradb_sql = "select json_object(json_data) from sample order by id desc fetch first 1 rows only"
        oradb_cursor.execute(oradb_sql)
        oradb_results = oradb_cursor.fetchall()
    except Exception as e:
        logger.error(e)
    return str(oradb_results)
