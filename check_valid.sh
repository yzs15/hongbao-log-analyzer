source venv/bin/activate

FILE_NAME=an_ua_eu_en_entropy_v7
DISK_PREFIX='/mnt/g'

ROOTS=( \
"logs-copy-vaild-burst" \
"logs-yuzishu-5-4-k8s-peak-50-speed-1" \
"logs-copy-3-27-vaild-acc-yield-spb" \
"logs-yuzishu-4-29-valid-acc-yield" \
"logs-june-6-29-valid-linear" \
"logs-june-6-29-valid-burst" \
"logs-june-7-1-valid-spb-linear" \
"logs-june-7-2-valid-all-burst" \
"logs-june-7-2-valid-all-linear" \
)

# "logs-yuzishu-5-1-valid-spb-resort" \

for root in ${ROOTS[@]}
do
    root_dir="$DISK_PREFIX/$root"
    echo $root_dir
    python3 check_time_valid.py $root_dir
done