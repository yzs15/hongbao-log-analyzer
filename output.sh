source venv/bin/activate

FILE_NAME=an_ua_eu_en_entropy_v7
DISK_PREFIX='/mnt/g'
DISK_PREFIX='/Volumes/Elements'
DISK_PREFIX='/Users/jian/logs'
DISK_PREFIX='/mnt/e/zsj/logs'

ROOTS=( \
"logs-june-6-29-valid-linear" \
"logs-june-6-29-valid-burst" \
"logs-june-7-1-valid-spb-linear" \
"logs-june-7-2-valid-all-burst" \
"logs-june-7-2-valid-all-linear" \
"logs-june-7-3-valid-all-burst" \
"logs-june-7-5-valid-spb-moreload" \
"logs-copy-3-27-vaild-acc-yield-spb" \
"logs-yuzishu-4-29-valid-acc-yield" \
"logs-copy-vaild-burst" \
"logs-yuzishu-5-4-k8s-peak-50-speed-1" \
)

# "logs-june-7-4-valid-spb-moreload" \

cat /dev/null > $DISK_PREFIX/$FILE_NAME.csv
for root in ${ROOTS[@]}
do
    root_dir="$DISK_PREFIX/$root"
    if ! [ -d $root_dir ]; then
        continue
    fi

    # check which directories are valid
    bash check_valid.sh $root_dir
    # python3 check_parent_valid.py $root_dir

    # WARN: generating this file is very time consuming
    # rm -rf $root_dir/comp_ranges.json

    # remove old output files
    rm -rf $root_dir/$FILE_NAME*
    
    python3 calculate_need_usage_alloc.py $root_dir
    cat $root_dir/$FILE_NAME* >> $DISK_PREFIX/$FILE_NAME.csv
done

# "logs-yuzishu-5-1-valid-spb-resort"
resort_root_dir="$DISK_PREFIX/logs-yuzishu-5-1-valid-spb-resort"
bash check_valid.sh $resort_root_dir
rm -rf $resort_root_dir/$FILE_NAME*
python3 calculate_need_usage_alloc.py  $resort_root_dir
cat $resort_root_dir/$FILE_NAME* > $DISK_PREFIX/$FILE_NAME-resort.csv