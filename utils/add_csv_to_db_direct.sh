#!/bin/bash

# Adds a CSV file to our Django DB.

if [ $# -lt 2 ]
then 
    echo "Usage : $0 csv_file_path db_path"
    exit
fi
csv_path=$1
db_path=$2
fname=$(basename $csv_path)

if [ -e ${csv_fname} ]
then
    scp ${csv_path} yiannis@mg-xen2.stanford.edu:/tmp/
    ssh yiannis@mg-xen2.stanford.edu << EOF
cd /home/yiannis/behop_dashboard
echo "Inserting $db_path!"
./custom_import.py /tmp/${fname} ${db_path}
#python manage.py csvimport --mappings='' --model='${db_path}' /tmp/${fname}
rm /tmp/${fname}
EOF
fi
