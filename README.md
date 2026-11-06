# SanYu Research Engine — MCP Server

**Real-algorithm medical research engines. 100+ deterministic tools. No LLM guessing.**

一个跑在公网上的 MCP 服务器，把**确定性算法**（统计检验、生存分析、生信算子、引物设计、文献检索）
暴露给任何支持 MCP 的智能体（Claude、ChatGPT、Cursor、Cline、Dify、Coze、自研脚本）。

---

## 它和"大模型套壳"的区别

| 别人的科研 agent | 这个 |
|---|---|
| LLM 生成数字，看起来像真的 | SciPy / statsmodels / 自研算子**真算** |
| 你没法判断真假 | 每个响应强制带 `engine_status` = `real` / `unavailable` / `error` |
| 出错难追溯 | 每次调用落审计（参数只存 SHA-256，患者数据不进日志） |
| 缺参数就瞎猜 | 返回 `hint_fields`，智能体可自我修正，且**不扣分** |
| 算不出也硬给 | 引擎不可用时如实返回 `unavailable`，**不编造** |

## 连接

```
https://sanyu.wentangkeji.com/api/mcp
```

- 传输：Streamable HTTP（协议 `2025-06-18` / `2025-03-26` / `2024-11-05` 自动协商）
- 认证：`Authorization: Bearer sk-sanyu-xxx`
- **看目录不需要密钥**（`tools/list` 公开），**执行才需要**
- 密钥获取：注册后在 https://sanyu.wentangkeji.com 的「API 密钥」页生成（注册送试用积分）

### Claude Code

```bash
claude mcp add --transport http sanyu https://sanyu.wentangkeji.com/api/mcp \
  --header "Authorization: Bearer sk-sanyu-你的密钥"
```

### Cursor / Cline / 任何 `mcp.json`

```json
{
  "mcpServers": {
    "sanyu": {
      "type": "http",
      "url": "https://sanyu.wentangkeji.com/api/mcp",
      "headers": { "Authorization": "Bearer sk-sanyu-你的密钥" }
    }
  }
}
```

### 只支持本地进程的旧客户端

```json
{
  "mcpServers": {
    "sanyu": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://sanyu.wentangkeji.com/api/mcp",
               "--header", "Authorization: Bearer sk-sanyu-你的密钥"]
    }
  }
}
```

### Dify / Coze（导入 OpenAPI）

```
https://sanyu.wentangkeji.com/api/open/v1/openapi.json
```
认证方式选 Bearer，填 `sk-sanyu-xxx`。

## 工具分类（100+）

| 类别 | 代表动作 |
|---|---|
| 统计分析 | ROC/AUC、DeLong、校准曲线、生存分析（KM/Cox）、ANOVA 及两两比较、置换检验、Egger 检验、IPTW、SMD 均衡 |
| 数据采集 | Table 1（基线表）、亚组 Table 1、数据快速画像 |
| 生信解读 | 差异表达、GO/KEGG 富集、PPI 网络、单细胞分析、代谢组 PCA/PLS-DA/火山图/热图 |
| 湿实验与序列 | 引物设计、Tm 计算、序列翻译/ORF/酶切位点、qPCR 2^-ΔΔCt、蛋白理化性质 |
| 建模预测 | 列线图、SHAP、PSI、NCA 药代、PK/PD 模拟 |
| 文献 | PubMed 检索、站内全文检索、引文格式化 |

完整清单：`GET /api/open/v1/actions` 或 MCP 的 `tools/list`。

## 计费

| 类型 | 每次 |
|---|---|
| 统计 / 序列 / 病理 | 1 分 |
| 文献检索 | 2 分 |
| 生信管线 | 5 分 |
| 免费档 | 每 key 每日 100 分封顶，注册送试用积分 |
| 频率 | 60 次/分钟/**每把 key**（不按 IP，防伪造） |

**失败不扣分**：引擎不可用、参数缺失、动作未开放，一律 0 扣分。

## 写权限边界

开放的只有**计算类**动作。写平台、写别人数据、动语料库——**目录里根本没有这些工具**：

- 传 `project_id` / `user_id` 会被**主动剥离**，并在 `warnings` 里说明
- 写作、CRF 建表、保存结果、删项目等动作**不在白名单**

## 响应示例

```json
{
  "success": true,
  "action": "act_roc",
  "engine_status": "real",
  "data_source": "local_computation",
  "result": { "auc": 0.86, "ci": [0.74, 0.95], "n": 120 },
  "cost": 1,
  "audit_id": 88123,
  "credits_balance": 499,
  "warnings": []
}
```

## 服务卡

```
https://sanyu.wentangkeji.com/api/mcp/card
```

## 许可

MIT
