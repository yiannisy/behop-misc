parallel-ssh -h pi-aps.txt -l root -o /tmp/pssh-out -e /tmp/pssh-err -x "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null" $@