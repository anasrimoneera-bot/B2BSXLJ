#!/usr/bin/env bash
#
# b2bsxlj 官网一键部署脚本（在火山引擎云服务器上运行）
# -----------------------------------------------------------------------------
# 用法：
#   1. 把整个项目（含 site/ 与 deploy/ 目录）上传到服务器，例如 /root/b2bsxlj
#   2. 登录服务器，进入项目根目录：   cd /root/b2bsxlj
#   3. 执行：                         sudo bash deploy/deploy.sh
#
# 脚本会：安装 Nginx → 复制网站到 /var/www/b2bsxlj → 配置站点 → 重载 Nginx
# 支持 Debian/Ubuntu（apt）与 CentOS/Anolis/RHEL（yum/dnf）。
# -----------------------------------------------------------------------------
set -euo pipefail

WEB_ROOT="/var/www/b2bsxlj"
SITE_NAME="b2bsxlj"

# 定位脚本所在项目根目录（deploy/ 的上一级）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
SITE_SRC="${PROJECT_DIR}/site"

echo ">> 项目目录: ${PROJECT_DIR}"

if [[ "${EUID}" -ne 0 ]]; then
  echo "请用 root 运行： sudo bash deploy/deploy.sh" >&2
  exit 1
fi

if [[ ! -f "${SITE_SRC}/index.html" ]]; then
  echo "找不到 ${SITE_SRC}/index.html，请确认在项目根目录执行本脚本。" >&2
  exit 1
fi

# ---------- 1. 安装 Nginx ----------
if ! command -v nginx >/dev/null 2>&1; then
  echo ">> 正在安装 Nginx ..."
  if command -v apt-get >/dev/null 2>&1; then
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -y
    apt-get install -y nginx
  elif command -v dnf >/dev/null 2>&1; then
    dnf install -y nginx
  elif command -v yum >/dev/null 2>&1; then
    yum install -y nginx
  else
    echo "无法识别的包管理器，请手动安装 Nginx 后重试。" >&2
    exit 1
  fi
else
  echo ">> 已检测到 Nginx，跳过安装。"
fi

# ---------- 2. 复制网站文件 ----------
echo ">> 部署网站到 ${WEB_ROOT} ..."
mkdir -p "${WEB_ROOT}"
# 用 rsync（若可用）否则用 cp；--delete 保证与源一致
if command -v rsync >/dev/null 2>&1; then
  rsync -a --delete "${SITE_SRC}/" "${WEB_ROOT}/"
else
  rm -rf "${WEB_ROOT:?}/"*
  cp -r "${SITE_SRC}/." "${WEB_ROOT}/"
fi
# 使用说明.txt 不需要对外暴露
rm -f "${WEB_ROOT}/使用说明.txt"

# 权限
chown -R root:root "${WEB_ROOT}" 2>/dev/null || true
chmod -R 755 "${WEB_ROOT}"

# ---------- 3. 配置 Nginx 站点 ----------
echo ">> 配置 Nginx 站点 ..."
if [[ -d /etc/nginx/sites-available ]]; then
  # Debian/Ubuntu 风格
  cp "${SCRIPT_DIR}/nginx-${SITE_NAME}.conf" "/etc/nginx/sites-available/${SITE_NAME}.conf"
  ln -sf "/etc/nginx/sites-available/${SITE_NAME}.conf" "/etc/nginx/sites-enabled/${SITE_NAME}.conf"
  # 关掉默认站点，避免抢占 80 端口
  rm -f /etc/nginx/sites-enabled/default
else
  # CentOS/Anolis 风格
  cp "${SCRIPT_DIR}/nginx-${SITE_NAME}.conf" "/etc/nginx/conf.d/${SITE_NAME}.conf"
fi

# ---------- 4. 校验并重载 ----------
echo ">> 校验 Nginx 配置 ..."
nginx -t

echo ">> 启动 / 重载 Nginx ..."
systemctl enable nginx >/dev/null 2>&1 || true
systemctl restart nginx

echo ""
echo "============================================================"
echo " 部署完成！"
echo " 现在用浏览器访问：  http://101.126.155.252/"
echo ""
echo " 提示："
echo "  - 火山引擎控制台 → 安全组 已放行 80/443，无需改动。"
echo "  - 绑定域名前，国内服务器需先完成 ICP 备案。"
echo "  - 申请免费 HTTPS：sudo apt install certbot python3-certbot-nginx"
echo "                    sudo certbot --nginx -d 你的域名"
echo "============================================================"
