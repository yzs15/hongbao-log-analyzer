source venv/bin/activate

FILE_NAME=an_ua_eu_en_entropy_v7
DISK_PREFIXS=('/mnt/g' '/mnt/e')

ROOTS=( \
"logs-june-7-14-valid-all" \
"logs-june-7-13-valid-all" \
"logs-june-7-8-valid-all" \
"logs-june-6-29-valid-linear" \
"logs-june-6-29-valid-burst" \
"logs-june-7-1-valid-spb-linear" \
"logs-june-7-2-valid-all-burst" \   
"logs-june-7-2-valid-all-linear" \
"logs-june-7-3-valid-all-burst" \
"logs-june-7-4-valid-spb-moreload" \
"logs-june-7-5-valid-spb-moreload" \
)

print_header() {
    echo 't_run','env','no_task','no_real_task','config','acc_speed','peak_task',\
'平均使用核数_need','占用/需求_need','使用/占用_need','有效/使用_need','有效/需求_need',\
'占用需求熵_need','占用需求熵_p_need',\
'使用率熵_need','使用率熵_p_need',\
'有效使用熵_need','有效使用熵_p_need',\
'有效需求熵_need','有效需求熵_p_need',\
'平均使用核数_alloc','占用/需求_alloc','使用/占用_alloc','有效/使用_alloc','有效/需求_alloc',\
'占用需求熵_alloc','占用需求熵_p_alloc',\
'使用率熵_alloc','使用率熵_p_alloc',\
'有效使用熵_alloc','有效使用熵_p_alloc',\
'有效需求熵_alloc','有效需求熵_p_alloc',\
'平均使用核数_comp','占用/需求_comp','使用/占用_comp','有效/使用_comp','有效/需求_comp',\
'占用需求熵_comp','占用需求熵_p_comp',\
'使用率熵_comp','使用率熵_p_comp',\
'有效使用熵_comp','有效使用熵_p_comp',\
'有效需求熵_comp','有效需求熵_p_comp',\
'yield','yield_machine','goodput',\
'need_beg','need_len','alloc_len','comp_len' | tee $1
}

# "logs-copy-3-27-vaild-acc-yield-spb" \
# "logs-yuzishu-4-29-valid-acc-yield" \
# "logs-copy-vaild-burst" \
# "logs-yuzishu-5-4-k8s-peak-50-speed-1" \

for DISK_PREFIX in ${DISK_PREFIXS[@]}
do
    for root in ${ROOTS[@]}
    do
        root_dir="$DISK_PREFIX/$root"
        if ! [ -d $root_dir ]; then
            continue
        fi

        python3 recalculate.py $root_dir

        # check which directories are valid
        bash check_valid.sh $root_dir
        # python3 check_parent_valid.py $root_dir
    done
done

print_header ${DISK_PREFIXS[0]}/$FILE_NAME.csv
for DISK_PREFIX in ${DISK_PREFIXS[@]}
do
    for root in ${ROOTS[@]}
    do
        root_dir="$DISK_PREFIX/$root"
        if ! [ -d $root_dir ]; then
            continue
        fi

        # WARN: generating this file is very time consuming
        # rm -rf $root_dir/comp_ranges.json

        # remove old output files
        rm -rf $root_dir/$FILE_NAME*
        
        python3 calculate_need_usage_alloc.py $root_dir
        cat $root_dir/$FILE_NAME* >> ${DISK_PREFIXS[0]}/$FILE_NAME.csv
    done
done

## ====== NOISE =====

ROOTS=( \
"logs-june-7-12-valid-noise-all" \
)

for DISK_PREFIX in ${DISK_PREFIXS[@]}
do
    for root in ${ROOTS[@]}
    do
        root_dir="$DISK_PREFIX/$root"
        if ! [ -d $root_dir ]; then
            continue
        fi

        python3 recalculate.py $root_dir

        # check which directories are valid
        bash check_valid.sh $root_dir
        # python3 check_parent_valid.py $root_dir
    done
done

print_header ${DISK_PREFIXS[0]}/$FILE_NAME-noise.csv
for DISK_PREFIX in ${DISK_PREFIXS[@]}
do
    for root in ${ROOTS[@]}
    do
        root_dir="$DISK_PREFIX/$root"
        if ! [ -d $root_dir ]; then
            continue
        fi

        # WARN: generating this file is very time consuming
        # rm -rf $root_dir/comp_ranges.json

        # remove old output files
        rm -rf $root_dir/$FILE_NAME*
        
        python3 calculate_need_usage_alloc.py $root_dir
        cat $root_dir/$FILE_NAME* >> ${DISK_PREFIXS[0]}/$FILE_NAME-noise.csv
    done
done