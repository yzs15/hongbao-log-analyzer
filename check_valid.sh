source venv/bin/activate

# DISK_PREFIX='/mnt/g'
# DISK_PREFIX='/Volumes/Elements'

root_dir=$1

# ROOTS=( \
# "logs-copy-vaild-burst" \
# "logs-yuzishu-5-4-k8s-peak-50-speed-1" \
# "logs-copy-3-27-vaild-acc-yield-spb" \
# "logs-yuzishu-4-29-valid-acc-yield" \
# "logs-june-6-29-valid-linear" \
# "logs-june-6-29-valid-burst" \
# "logs-june-7-1-valid-spb-linear" \
# "logs-june-7-2-valid-all-burst" \
# "logs-june-7-2-valid-all-linear" \
# "logs-yuzishu-5-1-valid-spb-resort" \
# )

# for root in ${ROOTS[@]}
# do
    # root_dir="$DISK_PREFIX/$root"
    if ! [ -d $root_dir ]; then
        continue
    fi
    echo $root_dir
    # python3 check_time_valid.py $root_dir

    for parent in $(ls $root_dir)
    do
        if [[ ${parent: 0-3} = "not" ]]; then
            continue
        fi

        DIR_PATH="$root_dir/$parent"
        if ! [ -d $DIR_PATH ]; then
            continue
        fi
        LOG_DIR=$DIR_PATH/$(ls -l $DIR_PATH | grep 2022 | awk '{print $9}')
        TS_CPU=$DIR_PATH"/ts-cpu"
        KS_CPU="${DIR_PATH}/k8s-cpu"
        
        if ! [[ -e "$LOG_DIR/spb.jpg" || -e "$LOG_DIR/net.jpb" ]]; then
            mv $DIR_PATH "${DIR_PATH}not"
            continue
        fi

        if ! [[ -e "$KS_CPU" || -e "$TS_CPU" ]]; then
            mv $DIR_PATH "${DIR_PATH}not"
            continue
        fi

        if [[ -e $KS_CPU ]]; then
            continue
        fi

        if ! [ -f "$DIR_PATH/ts_cpu_alloc_100ms.csv" ]; then
            echo $DIR_PATH "ts_cpu_alloc"
            python3 ./src/ts_cpu_alloc.py $LOG_DIR
        fi
        if ! [ -f "$DIR_PATH/ts_cpu_usage_100ms.csv" ]; then
            echo $DIR_PATH "ts_cpu_usage"
            python3 ./src/ts_cpu_usage.py $TS_CPU 100
        fi

        if ! [[ -f "$DIR_PATH/ts_cpu_alloc_100ms.csv" \
                || -f "$DIR_PATH/ts_cpu_usage_100ms.csv" ]]; then
            mv $DIR_PATH "${DIR_PATH}not"
        fi
    done
# done