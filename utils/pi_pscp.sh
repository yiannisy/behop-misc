parallel-scp -h $1 -l root -o /tmp/pssh-out -e /tmp/pssh-err -x "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null" $2 $3