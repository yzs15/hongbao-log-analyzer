source venv/bin/activate

FILE_NAME=an_ua_eu_en_entropy_v7
DISK_PREFIXS=('/mnt/g' '/mnt/e')

ROOTS=( \
"logs-june-7-8-valid-all" \
"logs-june-7-5-valid-all" \
"logs-june-6-29-valid-linear" \
"logs-june-6-29-valid-burst" \
"logs-june-7-1-valid-spb-linear" \
"logs-june-7-2-valid-all-burst" \
"logs-june-7-2-valid-all-linear" \
"logs-june-7-3-valid-all-burst" \
"logs-june-7-4-valid-spb-moreload" \
"logs-june-7-5-valid-spb-moreload" \
"logs-copy-3-27-vaild-acc-yield-spb" \
"logs-yuzishu-4-29-valid-acc-yield" \
"logs-copy-vaild-burst" \
"logs-yuzishu-5-4-k8s-peak-50-speed-1" \
)

for DISK_PREFIX in ${DISK_PREFIXS[@]}
do
    for root in ${ROOTS[@]}
    do
        root_dir="$DISK_PREFIX/$root"
        if ! [ -d $root_dir ]; then
            continue
        fi

        # check which directories are valid
        bash check_valid.sh $root_dir
        # python3 check_parent_valid.py $root_dir
    done
done

cat /dev/null > ${DISK_PREFIX[0]}/$FILE_NAME.csv
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
        cat $root_dir/$FILE_NAME* >> $DISK_PREFIX/$FILE_NAME.csv
    done
done