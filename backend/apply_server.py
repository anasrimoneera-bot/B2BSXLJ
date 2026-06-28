#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
b2bsxlj 入驻申请表单接收后端（零依赖，仅用 Python 标准库）

功能：
  POST /api/apply           接收表单提交，存到 CSV + JSONL，可选发邮件通知
  GET  /api/apply/list?token=...   网页查看所有申请（需口令）
  GET  /api/apply/health    健康检查

配置：全部通过环境变量（见 b2bsxlj-apply.service）。
监听：默认 127.0.0.1:5010（仅本机，由 Nginx 反代对外）。
"""
import os
import re
import csv
import json
import html
import smtplib
import datetime
from email.mime.text import MIMEText
from email.header import Header
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

# ---------------- 配置（环境变量优先） ----------------
HOST = os.environ.get("APPLY_HOST", "127.0.0.1")
PORT = int(os.environ.get("APPLY_PORT", "5010"))
DATA_DIR = os.environ.get("APPLY_DATA_DIR", "/var/www/b2bsxlj-data")
ADMIN_TOKEN = os.environ.get("APPLY_ADMIN_TOKEN", "change-me-please")

# 邮件通知（可选）。留空则不发邮件，只存文件。
SMTP_HOST = os.environ.get("APPLY_SMTP_HOST", "")        # 如 smtp.qq.com
SMTP_PORT = int(os.environ.get("APPLY_SMTP_PORT", "465"))
SMTP_USER = os.environ.get("APPLY_SMTP_USER", "")        # 你的 QQ 邮箱
SMTP_PASS = os.environ.get("APPLY_SMTP_PASS", "")        # QQ 邮箱「授权码」（不是登录密码）
MAIL_TO = os.environ.get("APPLY_MAIL_TO", SMTP_USER)     # 收件邮箱，默认同发件

MAX_BODY = 64 * 1024  # 最大请求体 64KB，防滥用

FIELDS = ["company", "name", "wechat", "phone", "email",
          "platform", "market", "volume", "message"]
LABELS = {"company": "公司/品牌", "name": "联系人", "wechat": "微信", "phone": "电话",
          "email": "邮箱", "platform": "主营平台", "market": "目标市场",
          "volume": "月均订单", "message": "留言"}
REQUIRED = ["company", "name", "wechat", "platform", "market"]

CSV_PATH = os.path.join(DATA_DIR, "applications.csv")
JSONL_PATH = os.path.join(DATA_DIR, "applications.jsonl")


def ensure_store():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(CSV_PATH):
        # utf-8-sig 让 Excel 打开不乱码
        with open(CSV_PATH, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["时间", "IP"] + [LABELS[k] for k in FIELDS])


def save_record(rec, ip):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(JSONL_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps({"time": ts, "ip": ip, **rec}, ensure_ascii=False) + "\n")
    with open(CSV_PATH, "a", newline="", encoding="utf-8-sig") as f:
        csv.writer(f).writerow([ts, ip] + [rec.get(k, "") for k in FIELDS])
    return ts


def send_mail(rec, ts):
    if not (SMTP_HOST and SMTP_USER and SMTP_PASS and MAIL_TO):
        return  # 未配置邮件，跳过
    lines = ["【b2bsxlj 入驻申请】", "时间：" + ts, ""]
    for k in FIELDS:
        if rec.get(k):
            lines.append(LABELS[k] + "：" + rec[k])
    msg = MIMEText("\n".join(lines), "plain", "utf-8")
    msg["Subject"] = Header("入驻申请 - " + (rec.get("company") or "新申请"), "utf-8")
    msg["From"] = SMTP_USER
    msg["To"] = MAIL_TO
    try:
        if SMTP_PORT == 465:
            s = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=15)
        else:
            s = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15)
            s.starttls()
        s.login(SMTP_USER, SMTP_PASS)
        s.sendmail(SMTP_USER, [MAIL_TO], msg.as_string())
        s.quit()
    except Exception as e:
        # 邮件失败不影响存档
        print("[mail] 发送失败:", e, flush=True)


def clean(v):
    return re.sub(r"[\r\n\t]+", " ", str(v)).strip()[:2000]


class Handler(BaseHTTPRequestHandler):
    def _json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _client_ip(self):
        return self.headers.get("X-Real-IP") or self.headers.get(
            "X-Forwarded-For", self.client_address[0]).split(",")[0].strip()

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/api/apply/health":
            return self._json(200, {"ok": True})
        if u.path == "/api/apply/list":
            qs = parse_qs(u.query)
            if qs.get("token", [""])[0] != ADMIN_TOKEN:
                return self._json(403, {"ok": False, "error": "forbidden"})
            return self._render_list()
        self._json(404, {"ok": False, "error": "not found"})

    def _render_list(self):
        rows = []
        if os.path.exists(JSONL_PATH):
            with open(JSONL_PATH, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            rows.append(json.loads(line))
                        except Exception:
                            pass
        rows.reverse()  # 最新在前
        th = "".join("<th>%s</th>" % html.escape(LABELS[k]) for k in FIELDS)
        trs = []
        for r in rows:
            tds = "".join("<td>%s</td>" % html.escape(str(r.get(k, ""))) for k in FIELDS)
            trs.append("<tr><td>%s</td><td>%s</td>%s</tr>" % (
                html.escape(r.get("time", "")), html.escape(r.get("ip", "")), tds))
        page = """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<title>入驻申请列表</title><meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{font-family:-apple-system,"Microsoft YaHei",sans-serif;margin:20px;color:#1f2937}
h2{margin:0 0 12px}table{border-collapse:collapse;width:100%%;font-size:13px}
th,td{border:1px solid #e5e7eb;padding:6px 8px;text-align:left;vertical-align:top}
th{background:#f3f4f6}tr:nth-child(even){background:#fafafa}.n{color:#6b7280}</style></head>
<body><h2>入驻申请（共 %d 条）</h2>
<p class="n">最新在前。CSV 文件：%s</p>
<table><thead><tr><th>时间</th><th>IP</th>%s</tr></thead><tbody>%s</tbody></table>
</body></html>""" % (len(rows), html.escape(CSV_PATH), th,
                     ("".join(trs) or '<tr><td colspan="11" class="n">暂无申请</td></tr>'))
        body = page.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        u = urlparse(self.path)
        if u.path != "/api/apply":
            return self._json(404, {"ok": False, "error": "not found"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        if length <= 0 or length > MAX_BODY:
            return self._json(400, {"ok": False, "error": "bad length"})
        raw = self.rfile.read(length)
        ctype = self.headers.get("Content-Type", "")
        rec = {}
        try:
            if "application/json" in ctype:
                data = json.loads(raw.decode("utf-8"))
                rec = {k: clean(data.get(k, "")) for k in FIELDS if data.get(k)}
            else:  # form-urlencoded 兜底
                data = parse_qs(raw.decode("utf-8"))
                rec = {k: clean(data.get(k, [""])[0]) for k in FIELDS if data.get(k, [""])[0]}
        except Exception:
            return self._json(400, {"ok": False, "error": "parse error"})

        missing = [LABELS[k] for k in REQUIRED if not rec.get(k)]
        if missing:
            return self._json(400, {"ok": False, "error": "缺少必填项: " + "、".join(missing)})

        ts = save_record(rec, self._client_ip())
        send_mail(rec, ts)
        self._json(200, {"ok": True})

    def log_message(self, fmt, *args):
        # 精简日志
        print("%s - %s" % (self._client_ip(), fmt % args), flush=True)


def main():
    ensure_store()
    print("入驻申请后端启动: http://%s:%d  数据目录: %s" % (HOST, PORT, DATA_DIR), flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
