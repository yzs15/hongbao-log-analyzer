source venv/bin/activate

FILE_NAME=an_ua_eu_en_entropy_v7
DISK_PREFIXS=('/mnt/g' '/mnt/f' '/mnt/e')


ROOTS=( \
"logs-june-7-16-valid-bu" \
"logs-june-7-13-valid-all" \
"logs-june-7-8-valid-all" \
"logs-june-7-14-valid-all" \
"logs-june-7-12-valid-noise-all" \
"logs-june-7-5-valid-all" \
"logs-june-6-29-valid-linear" \
"logs-june-6-29-valid-burst" \
"logs-june-7-1-valid-spb-linear" \
"logs-june-7-2-valid-all-burst" \
"logs-june-7-2-valid-all-linear" \
"logs-june-7-3-valid-all-burst" \
"logs-june-7-4-valid-spb-moreload" \
"logs-june-7-5-valid-spb-moreload" \
)

# "logs-copy-3-27-vaild-acc-yield-spb" \
# "logs-yuzishu-4-29-valid-acc-yield" \
# "logs-copy-vaild-burst" \
# "logs-yuzishu-5-4-k8s-peak-50-speed-1" \
# "logs-yuzishu-5-1-valid-spb-resort" \
# ROOTS=("logs-june-7-13-valid-all")

for DISK_PREFIX in ${DISK_PREFIXS[@]}
do
    for root in ${ROOTS[@]}
    do
        root_dir="$DISK_PREFIX/$root"
        if ! [ -d $root_dir ]; then
            continue
        fi

        # echo " "
        # echo $root_dir
        # echo "------------------"
        python3 -u extract-task-info.py $root_dir
    done
done