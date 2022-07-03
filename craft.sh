source venv/bin/activate

FILE_NAME=an_ua_eu_en_entropy_v7
DISK_PREFIX='/mnt/g'

ROOTS=( \
"logs-june-6-29-valid-linear" \
"logs-june-6-29-valid-burst" \
"logs-june-7-1-valid-spb-linear" \
"logs-june-7-2-valid-all-burst" \
"logs-june-7-2-valid-all-linear" \
"logs-copy-3-27-vaild-acc-yield-spb" \
"logs-yuzishu-4-29-valid-acc-yield" \
"logs-copy-vaild-burst" \
"logs-yuzishu-5-4-k8s-peak-50-speed-1" \
)

# "logs-yuzishu-5-1-valid-spb-resort" \

echo "" > $DISK_PREFIX/$FILE_NAME.csv
for root in ${ROOTS[@]}
do
    root_dir="$DISK_PREFIX/$root"
    rm -rf $root_dir/$FILE_NAME*
    # rm -rf $root_dir/comp_ranges.json
    
    python3 calculate_need_usage_alloc.py $root_dir
    cat $root_dir/$FILE_NAME* >> $DISK_PREFIX/$FILE_NAME.csv
done

resort_root_dir=$DISK_PREFIX/logs-yuzishu-5-1-valid-spb-resort
python3 calculate_need_usage_alloc.py  $resort_root_dir
cat $resort_root_dir/$FILE_NAME* > $DISK_PREFIX/$FILE_NAME-resort.csv
exit


python3 calculate_need_usage_alloc.py /Volumes/Elements/logs-copy-3-27-vaild-acc-yield-spb
python3 calculate_need_usage_alloc.py /Volumes/Elements/logs-yuzishu-4-29-valid-acc-yield
python3 calculate_need_usage_alloc.py /Volumes/Elements/logs-copy-vaild-burst
python3 calculate_need_usage_alloc.py /Volumes/Elements/logs-yuzishu-5-1-valid-spb-resort
python3 calculate_need_usage_alloc.py /Volumes/Elements/logs-yuzishu-5-4-k8s-peak-50-speed-1

cat /Volumes/Elements/logs-copy-3-27-vaild-acc-yield-spb/$FILE_NAME* > /Volumes/Elements/$FILE_NAME.csv
cat /Volumes/Elements/logs-yuzishu-4-29-valid-acc-yield/$FILE_NAME* >> /Volumes/Elements/$FILE_NAME.csv
cat /Volumes/Elements/logs-copy-vaild-burst/$FILE_NAME* >> /Volumes/Elements/$FILE_NAME.csv
cat /Volumes/Elements/logs-yuzishu-5-4-k8s-peak-50-speed-1/$FILE_NAME* >> /Volumes/Elements/$FILE_NAME.csv