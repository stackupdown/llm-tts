# reference: https://huggingface.co/spaces/qingxu98/gpt-academic/commit/e3d763acff3c7c248f4cefb6d78034f73a237d49

# hostip=$(powershell.exe -Command "(ipconfig)" | grep -a  IPv4 | grep -a 172 | awk '{print $16}')
# echo $hostip
hostip=$(grep -oP  "(\d+\.)+(\d+)" /etc/resolv.conf)
# export http_proxy=http://172.25.64.1:7890
# export https_proxy=http://172.25.64.1:7890
export http_proxy=http://${hostip}:7890
export https_proxy=http://${hostip}:7890
