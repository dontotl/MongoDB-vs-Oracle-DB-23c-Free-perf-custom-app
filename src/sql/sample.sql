create tablespace user_tbs datafile '/opt/oracle/oradata/FREE/testdb/usertbs.dbf' size 100M autoextend on;

CREATE TABLE sample
(
    id varchar2(32) not null primary key,
    json_data json
) tablespace user_tbs;
