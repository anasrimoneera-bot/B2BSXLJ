# b2bsxlj 官网

专注美国与欧盟市场的海外仓本土发货分销平台官网（纯静态站点：HTML + CSS + JS + 图片）。

## 目录结构

```
.
├── site/                     # 网站本体（部署时作为网站根目录）
│   ├── index.html            # 首页
│   ├── about.html            # 关于我们
│   ├── join.html             # 入驻申请（含表单）
│   ├── 使用说明.txt          # 内容修改 / 可视化编辑说明
│   └── assets/               # 样式、脚本、图片
│       ├── style.css
│       ├── edit.js
│       ├── map.png
│       └── p1.jpg ~ p10.jpg
└── deploy/
    ├── deploy.sh             # 一键部署脚本（在服务器上运行）
    └── nginx-b2bsxlj.conf    # Nginx 站点配置
```

## 部署到火山引擎云服务器（推荐：Nginx）

> 目标服务器：公网 IP `101.126.155.252`，安全组已放行 80 / 443 / 22 端口。

### 方式 A：一键脚本（最省事）

1. 把整个项目上传到服务器（任选其一）：
   - **scp**（在你本地电脑执行）：
     ```bash
     scp -r ./ root@101.126.155.252:/root/b2bsxlj
     ```
   - 或用 **宝塔面板 / FileZilla** 把项目文件夹上传到 `/root/b2bsxlj`。

2. SSH 登录服务器并运行脚本：
   ```bash
   ssh root@101.126.155.252
   cd /root/b2bsxlj
   sudo bash deploy/deploy.sh
   ```

3. 浏览器访问 **http://101.126.155.252/** 即可看到官网。

脚本会自动：安装 Nginx → 把 `site/` 复制到 `/var/www/b2bsxlj` → 配置站点 → 重载 Nginx，
并兼容 Ubuntu/Debian（apt）与 CentOS/Anolis（yum/dnf）。

### 方式 B：手动部署

```bash
# 1. 安装 Nginx
sudo apt update && sudo apt install -y nginx        # Ubuntu/Debian
# sudo yum install -y nginx                          # CentOS/Anolis

# 2. 复制网站文件到根目录
sudo mkdir -p /var/www/b2bsxlj
sudo cp -r site/. /var/www/b2bsxlj/
sudo rm -f /var/www/b2bsxlj/使用说明.txt

# 3. 放置站点配置
sudo cp deploy/nginx-b2bsxlj.conf /etc/nginx/conf.d/b2bsxlj.conf   # CentOS/Anolis
# 或 Ubuntu/Debian：放到 sites-available 并软链到 sites-enabled，关闭 default

# 4. 校验并重载
sudo nginx -t && sudo systemctl restart nginx
```

### 绑定域名 b2bsxlj.com + 免费 HTTPS

站点配置 `deploy/nginx-b2bsxlj.conf` 的 `server_name` 已设为
`b2bsxlj.com www.b2bsxlj.com 101.126.155.252`（域名与 IP 均可访问）。

1. **ICP 备案**：国内服务器，`b2bsxlj.com` 需先完成备案才能正常提供网页服务。
2. **DNS 解析**：把 `b2bsxlj.com` 与 `www` 的 A 记录解析到 `101.126.155.252`。
3. **申请免费证书**（certbot 会自动改好 443 与 HTTP→HTTPS 跳转）：
   ```bash
   sudo apt install -y certbot python3-certbot-nginx
   sudo certbot --nginx -d b2bsxlj.com -d www.b2bsxlj.com
   ```

## 备选方案：对象存储 TOS 静态托管（免运维）

火山引擎对象存储 TOS 开启「静态网站托管」，把 `site/` 下所有文件（含 `assets/`）上传，
再接 CDN 即可，无需自己维护服务器。

## 修改网站内容

详见 `site/使用说明.txt`：支持在网址后加 `?edit=1` 进行可视化编辑，或直接修改 HTML。
入驻表单接收邮箱在 `site/join.html` 中（搜索 `your-email@example.com` 替换为真实邮箱）。
