#!/usr/bin/env bash
# b2bsxlj 官网一键更新脚本（在服务器上运行）
# 用法：sudo bash /root/update-site.sh
# 作用：拉取仓库最新内容 → 部署到网站目录 → 重载 Nginx
# 注意：只更新官网，不碰 ERP / 合集后台的反代配置。
set -e
cd /root/b2bsxlj
echo ">> 拉取最新内容..."
git pull
echo ">> 部署到网站目录..."
cp -r site/. /var/www/b2bsxlj/
rm -f /var/www/b2bsxlj/使用说明.txt
chmod -R 755 /var/www/b2bsxlj
echo ">> 重载 Nginx..."
systemctl reload nginx
echo "✅ 官网已更新生效，按 Ctrl+F5 强刷浏览器查看"
