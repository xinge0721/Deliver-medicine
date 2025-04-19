#!/bin/bash

# NFS服务器配置脚本
# 此脚本自动配置NFS服务器并设置共享目录

# 设置颜色变量
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # 无颜色

# 错误处理函数
handle_error() {
    echo -e "${RED}错误: $1${NC}"
    exit 1
}

echo -e "${GREEN}开始配置NFS服务器...${NC}"

# 1. 更新系统并安装NFS服务器
echo -e "${GREEN}更新系统并安装NFS服务器...${NC}"
apt update || handle_error "系统更新失败"
apt install -y nfs-kernel-server || handle_error "NFS服务器安装失败"

# 2. 创建共享目录
echo -e "${GREEN}创建共享目录...${NC}"
mkdir -p /home/xinge/chengxu || handle_error "创建共享目录失败"

# 3. 设置目录权限
echo -e "${GREEN}设置目录权限...${NC}"
chmod -R 777 /home/xinge/chengxu || handle_error "设置目录权限失败"

# 4. 配置/etc/exports文件
echo -e "${GREEN}配置exports文件...${NC}"
# 检查是否已存在该配置
if grep -q "^/home/xinge/chengxu" /etc/exports; then
    echo "共享目录已在exports中配置，跳过..."
else
    echo "/home/xinge/chengxu *(rw,sync,no_subtree_check)" >> /etc/exports || handle_error "配置exports文件失败"
fi

# 5. 更新导出表并重启NFS服务
echo -e "${GREEN}更新导出表并重启NFS服务...${NC}"
exportfs -ra || handle_error "更新导出表失败"
systemctl restart nfs-kernel-server || handle_error "重启NFS服务失败"

# 6. 配置防火墙
echo -e "${GREEN}配置防火墙...${NC}"
if command -v ufw >/dev/null 2>&1; then
    ufw allow 2049/tcp || handle_error "开放NFS主端口失败"
    # 为NFS服务开放其他必要端口
    ufw allow 111/tcp || handle_error "开放portmapper端口失败"
    ufw allow 111/udp || handle_error "开放portmapper UDP端口失败"
    ufw allow 32767:32769/tcp || handle_error "开放NFS额外TCP端口失败"
    ufw allow 32767:32769/udp || handle_error "开放NFS额外UDP端口失败"
else
    echo "未检测到ufw防火墙，跳过防火墙配置..."
fi

echo -e "${GREEN}NFS服务器配置完成!${NC}"
echo -e "${GREEN}共享目录: /home/xinge/chengxu${NC}"
echo -e "${GREEN}客户端可以使用以下命令挂载此共享:${NC}"
echo -e "${GREEN}sudo mount -t nfs [服务器IP]:/home/xinge/chengxu [本地挂载点]${NC}"

exit 0 