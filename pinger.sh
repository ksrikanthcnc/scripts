(
trap "trap - SIGTERM && kill -- -$$" SIGINT SIGTERM EXIT
while true
do
    ping google.com -n 1 &>/dev/null
    if [ "$?" -eq 0 ]
    then
        echo '[✓]'
    else
        echo '[x]'
    fi
done
) &

while true
do
    echo -n '.'
    sleep 0.01
done

