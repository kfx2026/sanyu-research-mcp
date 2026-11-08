#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 server.json 发布到 MCP 官方 Registry —— 不依赖 mcp-publisher 二进制。

为什么不用官方 CLI（2026-11-08）
--------------------------------
mcp-publisher 的 release 资产 `mcp-publisher_linux_amd64.tar.gz` 在
objects.githubusercontent.com 上**连续 7 次返回 504**（run 42469128974 / 42469250965 /
42469309767），加 --retry 也没用；`releases/latest/download/...` 直连还返回过 92 字节的错误页。
而 Registry 本身是 HTTP API，CLI 只是它的壳 —— 直接调 API，少一个外部二进制依赖。

协议（读上游源码确认，不猜）
--------------------------
1) GitHub Actions 提供短期 OIDC token：
   GET  ${ACTIONS_ID_TOKEN_REQUEST_URL}&audience=<registry 的 scheme://host>
        Authorization: Bearer ${ACTIONS_ID_TOKEN_REQUEST_TOKEN}
        → {"value": "<jwt>"}
2) 换 Registry token：
   POST {registry}/v0/auth/github-oidc   {"oidc_token": "<jwt>"}
        → 含 registry token 的 JSON（字段名上游会变，这里做容错解析）
3) 发布：
   POST {registry}/v0/publish   body = server.json   Authorization: Bearer <token>

用法：在 `permissions: id-token: write` 的 job 里直接 `python3 publish_registry.py`。
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

REGISTRY = os.environ.get("MCP_REGISTRY_URL", "https://registry.modelcontextprotocol.io")
SERVER_JSON = os.environ.get("MCP_SERVER_JSON", "server.json")
TIMEOUT = 60


def _post(url, payload=None, token=None, raw_body=None):
    data = raw_body if raw_body is not None else json.dumps(payload or {}).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    req.add_header("User-Agent", "sanyu-publish/1.2")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


def _pick_token(doc):
    """从交换响应里找出 token。

    不硬编码字段名：上游改过一次命名，硬编码就会在别人升级时静默失效。
    判据：字符串、长度 > 40、不是描述性字段。找不到就报错，绝不返回空串。
    """
    if isinstance(doc, str):
        return doc if len(doc) > 40 else ""
    if isinstance(doc, dict):
        # 优先常见字段名
        for k in ("registry_token", "token", "access_token", "jwt", "value"):
            v = doc.get(k)
            if isinstance(v, str) and len(v) > 40:
                return v
        # 兜底：任意足够长的字符串值
        for v in doc.values():
            if isinstance(v, str) and len(v) > 40:
                return v
        for v in doc.values():
            if isinstance(v, dict):
                got = _pick_token(v)
                if got:
                    return got
    return ""


def main():
    url = os.environ.get("ACTIONS_ID_TOKEN_REQUEST_URL", "")
    tok = os.environ.get("ACTIONS_ID_TOKEN_REQUEST_TOKEN", "")
    if not url or not tok:
        print("::error::ACTIONS_ID_TOKEN_REQUEST_URL/TOKEN 缺失 —— "
              "job 必须声明 permissions: id-token: write")
        return 2

    # 1) 拿 GitHub OIDC token（audience 必须是 registry 的 scheme://host）
    from urllib.parse import urlparse
    u = urlparse(REGISTRY)
    audience = "%s://%s" % (u.scheme, (u.netloc or "").lower())
    req = urllib.request.Request(url + "&audience=" + urllib.parse.quote(audience, safe=""))
    req.add_header("Authorization", "Bearer " + tok)
    req.add_header("Accept", "application/json")
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        body = json.loads(r.read().decode())
    id_token = body.get("value") or ""
    if len(id_token) < 40:
        print("::error::GitHub 没返回 OIDC token: %s" % json.dumps(body)[:200])
        return 3
    print("1/3 got GitHub OIDC token (%d chars), audience=%s" % (len(id_token), audience))

    # 2) 换 registry token
    st, txt = _post(REGISTRY + "/v0/auth/github-oidc", {"oidc_token": id_token})
    print("2/3 auth -> HTTP %d %s" % (st, txt[:300]))
    if st != 200:
        print("::error::OIDC 换 token 失败（HTTP %d）" % st)
        return 4
    reg_token = _pick_token(json.loads(txt))
    if not reg_token:
        print("::error::响应里找不到 token，原文：%s" % txt[:400])
        return 5
    print("    registry token acquired (%d chars)" % len(reg_token))

    # 3) 发布
    raw = open(SERVER_JSON, "rb").read()
    doc = json.loads(raw.decode("utf-8"))
    print("3/3 publishing %s@%s" % (doc.get("name"), doc.get("version")))
    st, txt = _post(REGISTRY + "/v0/publish", token=reg_token, raw_body=raw)
    print("    publish -> HTTP %d %s" % (st, txt[:600]))
    if st not in (200, 201):
        print("::error::发布失败（HTTP %d）" % st)
        return 6
    print("PUBLISHED %s@%s" % (doc.get("name"), doc.get("version")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
