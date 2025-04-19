#!/bin/bash

# 树莓派4B 5GHz Wi-Fi配置脚本
echo "开始配置树莓派支持5GHz Wi-Fi..."

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then
  echo "请使用sudo运行此脚本"
  exit 1
fi

# 设置国家代码（以中国为例，CN）
# 您可以根据您所在的国家/地区更改此代码
COUNTRY_CODE="CN"

# 更新系统
echo "正在更新系统..."
apt update && apt upgrade -y

# 设置国家代码
echo "设置国家代码为: $COUNTRY_CODE"
raspi-config nonint do_wifi_country $COUNTRY_CODE

# 修改wpa_supplicant.conf文件
CONFIG_FILE="/etc/wpa_supplicant/wpa_supplicant.conf"
echo "正在更新Wi-Fi配置文件..."

# 检查配置文件是否存在
if [ ! -f "$CONFIG_FILE" ]; then
  echo "创建新的wpa_supplicant.conf文件"
  echo "ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev" > $CONFIG_FILE
  echo "update_config=1" >> $CONFIG_FILE
fi

# 确保country参数存在且正确
if grep -q "country=" $CONFIG_FILE; then
  # 替换现有的country行
  sed -i "s/country=.*/country=$COUNTRY_CODE/g" $CONFIG_FILE
else
  # 添加country行
  sed -i "1s/^/country=$COUNTRY_CODE\n/" $CONFIG_FILE
fi

echo "请输入您的5GHz Wi-Fi名称(SSID):"
read SSID

echo "请输入Wi-Fi密码:"
read -s PASSWORD

# 添加网络配置
cat >> $CONFIG_FILE << EOF

network={
    ssid="$SSID"
    psk="$PASSWORD"
    proto=RSN
    key_mgmt=WPA-PSK
    pairwise=CCMP
    auth_alg=OPEN
    freq_list=5180 5200 5220 5240 5260 5280 5300 5320 5500 5520 5540 5560 5580 5600 5620 5640 5660 5680 5700
}
EOF

# 重启网络服务
echo "重启网络服务..."
systemctl restart wpa_supplicant
systemctl restart dhcpcd

echo "配置完成！树莓派应该现在会尝试连接到5GHz网络。"
echo "如果仍然无法连接，请重启树莓派: sudo reboot"

exit 0 