#!/usr/bin/env python
import os,sys
import csv
import MySQLdb

fname=sys.argv[1]
table=sys.argv[2]

USER='behopap'
PSWD='ofwork'
SERVER='171.64.74.31'

if __name__=='__main__':
    db = MySQLdb.connect(host=SERVER,port=3306,user=USER,passwd=PSWD,db="behopdb",local_infile=1)
    cursor = db.cursor()
    f = open(fname,'r')
    header_line = f.readlines()[0]
    statement = "load data local infile '%s' into table %s character set latin1 fields terminated by ',' lines terminated by '\n' ignore 1 lines (%s);" % (fname,table,header_line)
    print statement
    cursor.execute(statement)
    db.commit()
    f.close()
    db.close()
