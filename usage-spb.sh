root='/mnt/g/logs-june-7-2-valid-all-burst'

parents=(`ls $root`)

source ./venv/bin/activate

for parent in ${parents[@]}
do
    DIR_PATH="$root/$parent"
    if [ -f $DIR_PATH ]; then
        continue
    fi
    if ! [ -d $DIR_PATH'/ts-cpu' ]; then
        continue
    fi

    if [ -f $DIR_PATH'/ts_cpu_alloc_100ms.csv' ] && [ -f $DIR_PATH'/ts_cpu_usage_100ms.csv' ]; then
        continue
    fi

    LOG_DIR=$DIR_PATH/$(ls -l $DIR_PATH | grep 2022 | awk '{print $9}')
    echo $DIR_PATH
    echo $LOG_DIR
    python3 ./src/ts_cpu_alloc.py $LOG_DIR &
    python3 ./src/ts_cpu_usage.py $DIR_PATH"/ts-cpu" 1
    python3 ./src/ts_cpu_usage.py $DIR_PATH"/ts-cpu" 100
done
wait