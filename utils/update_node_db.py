#!/usr/bin/env python

import sqlite3,csv
conn = sqlite3.connect('nodeDB.sqlite')
c = conn.cursor()
#c.execute('create table probes (addr,channel,band)')
#c.execute('create table nodes (addr,channels,bands)')
with open('/tmp/.probes.log','rb') as fin:
    dr = csv.DictReader(fin,delimiter='|')
    to_db = [(i['addr'],i['channel'],i['band']) for i in dr]

# add to probes and filter out distinct ones.
c.executemany("insert into probes (addr,channel,band) values (?,?,?);", to_db)
c.execute("drop table if exists probes_tmp")
c.execute("create table probes_tmp (addr,channel,band)")
c.execute("insert into probes_tmp (addr,channel,band) select distinct addr,channel,band from probes")

# replace probes (which has duplicates by now, with probes_tmp)
c.execute("drop table probes")
c.execute("create table probes (addr,channel,band)")
c.execute("insert into probes (addr,channel,band) select * from probes_tmp")
c.execute("drop table probes_tmp")

c.execute("drop table if exists nodes")
c.execute("create table nodes (addr,channels,bands)")
c.execute("insert into nodes (addr,channels,bands) select addr,group_concat(channel),group_concat(band) from ( select distinct addr,channel,band from probes) group by addr")
conn.commit()

#c.execute('''select * from nodes''')
#print c.fetchall()
conn.close()
