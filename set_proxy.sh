hostip=$(powershell.exe -Command "(ipconfig)" | grep -a  IPv4 | grep -a 172 | awk '{print $16}')
echo $hostip

export http_proxy=http://172.25.64.1:7890
export https_proxy=http://172.25.64.1:7890
