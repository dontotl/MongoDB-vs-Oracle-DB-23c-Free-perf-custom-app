# MongoDB vs Oracle DB 23c Free 성능 부하 (1)

## OVERVIEW

MongoDB 컬렉션과 오라클 DB 23c 의 JSON 타입 컬렉션을 구성하고, Insert, Select 부하에 대한 성능을 비교 합니다. 

테스트 환경의 VM 정보는 다음과 같습니다. 

| VM | 용도 | Shape | Private IP | Public IP |
| --- | --- | --- | --- | --- |
| oci-demo-db | DB 서버 | VM.Standard.E4.Flex 1 OCPU, 16GB Mem | 10.0.1.18 |  |
| oci-demo-app | APP 서버 | VM.Standard.E4.Flex 1 OCPU, 16GB Mem | 10.0.0.70 | 138.2.47.72 |

### DB 구성

MongoDB 를 구성합니다. 

현재시점의 Stable GA인 MongoDB 6.0을 사용하도록 하겠습니다.

 참조 URL : [https://www.mongodb.com/docs/manual/tutorial/install-mongodb-on-red-hat/](https://www.mongodb.com/docs/manual/tutorial/install-mongodb-on-red-hat/)

YUM리파지토리를 생성합니다. 

```jsx
$ sudo vi /etc/yum.repos.d/mongodb-org-6.0.repo
[mongodb-org-6.0]
name=MongoDB Repository
baseurl=https://repo.mongodb.org/yum/redhat/$releasever/mongodb-org/6.0/x86_64/
gpgcheck=1
enabled=1
gpgkey=https://www.mongodb.org/static/pgp/server-6.0.asc
```

YUM으로 MongoDB를 설치합니다. 

```jsx
$ sudo yum install -y mongodb-org

중략..

Complete!
```

MongoDB 를 서비스로 등록합니다. 

```jsx
$ sudo systemctl start mongod
$ sudo systemctl enable mongod
$ sudo systemctl status mongod
```

MongoDB 서비스에 접속해  봅니다. 

```jsx
$ mongosh
Current Mongosh Log ID:	643bbc596bcf4e8ced9c9543
Connecting to:		mongodb://127.0.0.1:27017/?directConnection=true&serverSelectionTimeoutMS=2000&appName=mongosh+1.8.0
Using MongoDB:		6.0.5
Using Mongosh:		1.8.0

For mongosh info see: https://docs.mongodb.com/mongodb-shell/

To help improve our products, anonymous usage data is collected and sent to MongoDB periodically (https://www.mongodb.com/legal/privacy-policy).
You can opt-out by running the disableTelemetry() command.

test>
```

admin 유저를 추가해 줍니다.

```jsx
test> use admin
switched to db admin
admin> db.createUser({ user: 'mongo', pwd: 'mongo', roles: ['root'] })
{ ok: 1 }
admin> exit
```

외부 접속을 위한 설정을 해줍니다. 

```jsx
$ sudo vi /etc/mongod.conf

#  bindIp: 127.0.0.1  # Enter 0.0.0.0,:: to bind to all IPv4 and IPv6 addresses or, alternatively, use the net.bindIpAll setting.
  bindIp: 0.0.0.0  # Enter 0.0.0.0,:: to bind to all IPv4 and IPv6 addresses or, alternatively, use the net.bindIpAll setting.

```

MongoDB  서비스를 재기동합니다. 

```jsx
$ sudo systemctl restart mongod
```

Oracle DB 23c Free - Developer Release를 설치합니다.

```python
$ sudo yum config-manager --set-enabled ol8_developer

$ sudo yum -y install oracle-database-preinstall-23c

$ sudo wget https://download.oracle.com/otn-pub/otn_software/db-free/oracle-database-free-23c-1.0-1.el8.x86_64.rpm

$ sudo yum -y install oracle-database-free-23c-1.0-1.el8.x86_64.rpm
```

configure를 실행해 DB를 생성합니다. 패스워드는 TESTdb##01을 씁니다.

```python
$ sudo /etc/init.d/oracle-free-23c configure
Specify a password to be used for database accounts. Oracle recommends that the password entered should be at least 8 characters in length, contain at least 1 uppercase character, 1 lower case character and 1 digit [0-9]. Note that the same password will be used for SYS, SYSTEM and PDBADMIN accounts:
Confirm the password:
Configuring Oracle Listener.
Listener configuration succeeded.
Configuring Oracle Database FREE.
Enter SYS user password: 
*********
Enter SYSTEM user password: 
************
Enter PDBADMIN User Password: 
*********
Prepare for db operation
7% complete
Copying database files
29% complete
Creating and starting Oracle instance
30% complete
33% complete
36% complete
39% complete
43% complete
Completing Database Creation
47% complete
49% complete
50% complete
Creating Pluggable Databases
54% complete
71% complete
Executing Post Configuration Actions
93% complete
Running Custom Scripts
100% complete
Database creation complete. For details check the logfiles at:
 /opt/oracle/cfgtoollogs/dbca/FREE.
Database Information:
Global Database Name:FREE
System Identifier(SID):FREE
Look at the log file "/opt/oracle/cfgtoollogs/dbca/FREE/FREE.log" for further details.

Connect to Oracle Database using one of the connect strings:
     Pluggable database: oci-demo-msadb/FREEPDB1
     Multitenant container database: oci-demo-msadb
```

DB에 접속하여 PDB를 만들어 줍니다.

```python
$ sudo su - oracle

[oracle@oci-demo-db ~]$ . oraenv
ORACLE_SID = [oracle] ? FREE
The Oracle base has been set to /opt/oracle

[oracle@oci-demo-db ~]$ sqlplus /nolog

SQL> conn /as sysdba

SQL> CREATE PLUGGABLE DATABASE testdb ADMIN USER useradm IDENTIFIED BY TESTdb#01 PATH_PREFIX = '/opt/oracle/oradata/FREE/testdb/' FILE_NAME_CONVERT=('/opt/oracle/oradata/FREE/pdbseed/', '/opt/oracle/oradata/FREE/testdb') ;

SQL> alter pluggable database testdb open read write;

SQL> alter pluggable database testdb save state;

SQL> exit
```

Linux방화벽에 TCP 1521, 27017 포트를 추가합니다.

```python
$ sudo firewall-cmd --zone=public --permanent --add-port=1521/tcp

$ sudo firewall-cmd --zone=public --permanent --add-port=27017/tcp

$ sudo firewall-cmd --reload
```

 OCI Security List 등록을 합니다. 1521, 27017 TCP 포트를 오픈합니다.

### 테스트APP 환경 구성

파이썬 환경을 구성합니다. 버전은 Python 3을 사용합니다. 

```jsx
$ python -V
Python 3.6.8
```

파이썬 가상환경을 만들어 줍니다. 

```jsx
$ mkdir venvs
$ cd venvs
$ python -m venv oravsmongo
```

가상환경에 진입합니다. 

```jsx
$ cd oravsmongo/bin/
$ source activate
(oravsmongo) [opc@oci-demo-app bin]$
```

Flask, pymongo설치 및 pip를 업그레이드 합니다. 

```jsx
(oravsmongo) [opc@oci-demo-app bin]$ pip install flask
(oravsmongo) [opc@oci-demo-app bin]$ pip install pymongo
(oravsmongo) [opc@oci-demo-app bin]$ python -m pip install --upgrade pip
```

 

oci-demo-app 터미널을 하나 더 열어서, Linux 방화벽에도 TCP 5000 포트를 추가하고, OCI Security List에도 추가해 줍니다. 

```jsx
$ sudo firewall-cmd --zone=public --permanent --add-port=5000/tcp

$ sudo firewall-cmd --reload
```

oci-demp-app 서버에 DB 접속용 클라이언트를 셋업해 줍니다. 

YUM리파지토리를 생성합니다. 

```jsx
$ sudo vi /etc/yum.repos.d/mongodb-org-6.0.repo
[mongodb-org-6.0]
name=MongoDB Repository
baseurl=https://repo.mongodb.org/yum/redhat/$releasever/mongodb-org/6.0/x86_64/
gpgcheck=1
enabled=1
gpgkey=https://www.mongodb.org/static/pgp/server-6.0.asc
```

YUM으로 MongoDB Client 를 설치합니다. 

```jsx
$ sudo yum install mongodb-mongosh

중략..                                                                                         

Complete!
```

MongoDB에 접속해 봅니다. 

```jsx
$ mongosh mongodb://10.0.1.18:27017 -u mongo -p
Enter password: *****
Current Mongosh Log ID:	643d166436853fefdbe957b9
Connecting to:		mongodb://<credentials>@10.0.1.135:27017/?directConnection=true&appName=mongosh+1.8.0
Using MongoDB:		6.0.5
Using Mongosh:		1.8.0

For mongosh info see: https://docs.mongodb.com/mongodb-shell/

To help improve our products, anonymous usage data is collected and sent to MongoDB periodically (https://www.mongodb.com/legal/privacy-policy).
You can opt-out by running the disableTelemetry() command.

test> exit
```

오라클 DB클라이언트를 셋업하고 DB접속을 확인 합니다. 

```python
$ sudo yum install -y oracle-instantclient-release-el8

중략..

Complete!

$ sudo yum install -y oracle-instantclient-basic

중략..                                                                                                   

Complete!

$ sudo yum install -y oracle-instantclient-sqlplus

중략..                                                                                                   

Complete!

$ sqlplus system@10.0.1.18:1521/testdb

Connected to:
Oracle Database 23c Free, Release 23.0.0.0.0 - Developer-Release
Version 23.2.0.0.0

SQL> exit
```

오라클 DB 테이블 생성

testdb에 sample.sql을 만들고 테이블을 생성합니다.

```python
$ vi sample.sql
create tablespace user_tbs datafile '/opt/oracle/oradata/FREE/testdb/usertbs.dbf' size 100M autoextend on;
CREATE TABLE sample
(
	id varchar2(32) not null primary key,
	json_data json
) tablespace user_tbs;

$ sqlplus system@//10.0.1.18/testdb @sample.sql

Table created.

SQL> exit 
```

### 테스트 APP 작성

간단하게 각 DB에  JSON 다큐먼트 스토어를 만들고, 1건을 Insert하고 1건을 Select 하는 앱을 만듭니다.

Flask [sampleapp.py](http://sample-monolith.py) 을 만듭니다. 

```jsx
(oravsmongo) [opc@oci-demo-app oravsmongo]$ vi sampleapp.py
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
        sample = [
            {
            "user_name": fake.name(),
            "last_conn_date": datetime.now()
            }
        ]
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
        sample_data ={}
        sample_data['user_name'] = fake.name()
        sample_data['last_conn_date'] = datetime.now()
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
```

oci-demo-app 터미널을 하나 더 열어서, Linux 방화벽에도 TCP 5000 포트를 추가하고, OCI Security List에도 추가해 줍니다. 

```jsx
$ sudo firewall-cmd --zone=public --permanent --add-port=5000/tcp

$ sudo firewall-cmd --reload
```

### 부하테스트 수행

부하테스트를 위해 운영용 WSGI인 gunicorn을 설치합니다. flask개발 모드는 기본적으로 싱글 쓰레드로 동작하므로 부하테스트에 적합하지 않습니다. 

```python
(oravsmongo) [opc@oci-demo-app oravsmongo]$ pip install gunicorn
```

부하테스트 도구인 locust를 설치합니다. 

```python
(oravsmongo) [opc@oci-demo-app oravsmongo]$ pip install locust
```

부하 테스트용 스크립트를 작성합니다.  테스트할 시나리오만 주석해제 하고 수행합니다. 

```python
(oravsmongo) [opc@oci-demo-app oravsmongo]$ vi locustfile.py
from locust import HttpUser, task

class User(HttpUser):
    @task
    def index(self):
#        self.client.get("/oracle/select")
        self.client.get("/oracle/insert")
#        self.client.get("/mongo/insert")
#        self.client.get("/mongo/select")

```

gunicorn을 백그라운로 수행합니다. 

```python
(oravsmongo) [opc@oci-demo-app oravsmongo]$ gunicorn --workers=2 sampleapp:app -b 0.0.0.0:5000 &
```

locust로 부하를 수행합니다.

```python
(oravsmongo) [opc@oci-demo-app oravsmongo]$ sudo ulimit -n 2048
(oravsmongo) [opc@oci-demo-app oravsmongo]$ locust
```

oci-demo-app 터미널을 하나 더 열어서, Linux 방화벽에도 TCP 8089 포트를 추가하고, OCI Security List에도 추가해 줍니다. 

```jsx
$ sudo firewall-cmd --zone=public --permanent --add-port=8089/tcp

$ sudo firewall-cmd --reload
```

유저 50으로 1초간격으로 부하를 줍니다. 

![Untitled](MongoDB%20vs%20Oracle%20DB%2023c%20Free%20%EC%84%B1%EB%8A%A5%20%EB%B6%80%ED%95%98%20(1)%2000aa57d206ff4f4ebef5f32cce4fc898/Untitled.png)

Oracle Insert 부하결과 입니다. 

![Untitled](MongoDB%20vs%20Oracle%20DB%2023c%20Free%20%EC%84%B1%EB%8A%A5%20%EB%B6%80%ED%95%98%20(1)%2000aa57d206ff4f4ebef5f32cce4fc898/Untitled%201.png)

부하 테스트용 스크립트를 작성합니다.  테스트할 시나리오만 주석해제 하고 수행합니다. 

```python
(ocisamplerest) [opc@oci-demo-appdev ocisamplerest]$ vi locustfile.py
from locust import HttpUser, task

class User(HttpUser):
    @task
    def index(self):
#        self.client.get("/oracle/select")
#        self.client.get("/oracle/insert")
        self.client.get("/mongo/insert")
#        self.client.get("/mongo/select")

ocisampleweb) [opc@oci-demo-app ocisampleweb]$ locust
```

유저 50으로 1초간격으로 부하를 줍니다. 

![Untitled](MongoDB vs Oracle DB 23c Free perf custom app/Untitled.png)

MongoDB Insert 부하결과 입니다.

![Untitled](MongoDB vs Oracle DB 23c Free perf custom app/Untitled%202.png)

Oracle Select 부하입니다.

![Untitled](MongoDB vs Oracle DB 23c Free perf custom app/Untitled%203.png)

MongoDB Select 부하입니다. 

![Untitled](MongoDB vs Oracle DB 23c Free perf custom app/Untitled%204.png)

기본 설치 환경에서 Insert 부하는 오라클 RPS (request per second) 429 vs MongoDB RPS 433으로 유사했으며, Select 부하는 Oracle DB이 509, Mongo가 430으로 OracleDB가 빨랐습니다. 

대량 부하 환경에서는 오라클 JSON성능이 다음과 같이 좋습니다. 

[https://www.oracle.com/a/ocom/docs/oracle-autonomous-json-takes-on-document-dbs.pdf](https://www.oracle.com/a/ocom/docs/oracle-autonomous-json-takes-on-document-dbs.pdf)

<끝>
