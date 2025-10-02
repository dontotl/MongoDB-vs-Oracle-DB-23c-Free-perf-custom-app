CREATE PLUGGABLE DATABASE testdb 
ADMIN USER useradm IDENTIFIED BY TESTdb#01 
PATH_PREFIX = '/opt/oracle/oradata/FREE/testdb/' 
FILE_NAME_CONVERT=('/opt/oracle/oradata/FREE/pdbseed/', '/opt/oracle/oradata/FREE/testdb');

alter pluggable database testdb open read write;
alter pluggable database testdb save state;
