
python3 calculate_need_usage_alloc.py /Volumes/Elements/logs-copy-3-27-vaild-acc-yield-spb
python3 calculate_need_usage_alloc.py /Volumes/Elements/logs-yuzishu-4-29-valid-acc-yield
python3 calculate_need_usage_alloc.py /Volumes/Elements/logs-copy-vaild-burst
python3 calculate_need_usage_alloc.py /Volumes/Elements/logs-yuzishu-5-1-valid-spb-resort
python3 calculate_need_usage_alloc.py /Volumes/Elements/logs-yuzishu-5-4-k8s-peak-50-speed-1
FILE_NAME=an_ua_eu_en_entropy_v7
cat /Volumes/Elements/logs-copy-3-27-vaild-acc-yield-spb/$FILE_NAME* > /Volumes/Elements/$FILE_NAME.csv
cat /Volumes/Elements/logs-yuzishu-4-29-valid-acc-yield/$FILE_NAME* >> /Volumes/Elements/$FILE_NAME.csv
cat /Volumes/Elements/logs-copy-vaild-burst/$FILE_NAME* >> /Volumes/Elements/$FILE_NAME.csv
cat /Volumes/Elements/logs-yuzishu-5-4-k8s-peak-50-speed-1/$FILE_NAME* >> /Volumes/Elements/$FILE_NAME.csv