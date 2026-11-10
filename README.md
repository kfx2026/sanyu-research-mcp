# 三域医研 · 科研算法引擎 (SanYu Research Engine) — MCP Server

> 正式中文名：**三域医研 · 科研算法引擎**；英文检索名 SanYu Research Engine。平台站：https://sanyu.wentangkeji.com

**145 个动作 = 106 个确定性算法 + 39 个大模型生成类；对外暴露为 147 个 MCP 工具**
（145 个动作 + 2 个元工具 `sanyu_list_actions` / `sanyu_job_status`）。
**档位**：当前生产为 L2 档（`SANYU_OPEN_L2=1`），即上表的 145/147；关闭该开关则为默认档 —— 106 个确定性动作 / 108 个 MCP 工具 / 0 个生成类，全部 `readOnlyHint=true`、不写库。

**Medical research engines: 106 deterministic actions + 39 AI writers (L2 profile).**

> 106 个是**确定性算法**（SciPy / statsmodels / 自研算子），结果可复现，可以当结论用；
> 39 个是**大模型生成**（选题 / 方案 / 写作 / 审稿 / 润色），结果**不可复现**。
> 每个工具在 `_meta.sanyu/api_class` 里标了 `compute` / `data` / `gen` ——
> 转述给用户时必须说清是哪一类，别把生成草稿说成算出来的结果。

> **调用需要自备密钥**：目录和工具列表免费查看，执行需在
> [sanyu.wentangkeji.com/api-keys](https://sanyu.wentangkeji.com/api-keys) 免费领取一把 key，
> 填进 `Authorization: Bearer sk-sanyu-xxx`（注册送试用积分，执行失败不扣分）。
>
> **只想先试试效果？** `dna_translate`、`orf_find`、`roc_auc`
> 这三个工具**无需密钥**，每 IP 每天可试 20 次，返回体带 `demo:true` 与剩余次数。

一个跑在公网上的 MCP 服务器，把**确定性算法**（统计检验、生存分析、生信算子、引物设计、文献检索）
暴露给任何支持 MCP 的智能体（Claude、ChatGPT、Cursor、Cline、Dify、Coze、魔搭、自研脚本）。

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

### ModelScope（魔搭）/ 通用 MCP 配置

> ⚠️ 这一段必须排在其他配置之前：魔搭**只取第一个 `mcpServers` 块**做部署检测，
> 且 `type` 只认 `streamable_http`（下划线）。写成 `http` 会导致"基础信息解析失败"。

```json
{
  "mcpServers": {
    "sanyu-research": {
      "type": "streamable_http",
      "url": "https://sanyu.wentangkeji.com/api/mcp",
      "headers": {
        "Authorization": "Bearer sk-sanyu-REPLACE-WITH-YOUR-OWN-KEY"
      }
    }
  }
}
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

### Claude Code

```bash
claude mcp add --transport http sanyu https://sanyu.wentangkeji.com/api/mcp \
  --header "Authorization: Bearer sk-sanyu-你的密钥"
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
若觉得 145 个工具太多、Agent 选不准，可改用精选 24 个的 schema 导入。

## 动作分类（145 = 106 确定性 + 39 生成）｜MCP 工具 147 = 145 + 2 元工具

| 类别 | 代表动作 |
|---|---|
| 统计分析 | ROC/AUC、DeLong、校准曲线、生存分析（KM/Cox）、ANOVA 及两两比较、置换检验、Egger 检验、IPTW、SMD 均衡 |
| 数据采集 | Table 1（基线表）、亚组 Table 1、数据快速画像 |
| 研究设计 | 样本量计算、随机化分组（固定种子可复现）、倾向性评分匹配 PSM |
| 生信解读 | 差异表达、GO/KEGG 富集、PPI 网络、单细胞分析、代谢组 PCA/PLS-DA/火山图/热图 |
| 湿实验与序列 | 引物设计、Tm 计算、序列翻译/ORF/酶切位点、qPCR 2^-ΔΔCt、蛋白理化性质 |
| 建模预测 | 列线图、SHAP、PSI、NCA 药代、PK/PD 模拟 |
| 图表与规范 | 森林图、CONSORT 流程图、PRISMA 流程图、报告规范清单核对 |
| 文献 | PubMed 检索、站内全文检索、引文格式化 |
| **生成类（不可复现）** | 选题、研究方案、论文初稿、单章写作、润色、六智能体审稿、投稿信、汇报 PPT |

完整清单：`GET /api/open/v1/actions` 或 MCP 的 `tools/list`。

## 计费

| 类型 | 每次 |
|---|---|
| 统计 / 序列 / 病理 / 图表 | 1 分 |
| 文献检索 | 2 分 |
| 生信管线 | 5 分 |
| 免费档 | 每 key 每日 100 分封顶，注册送试用积分 |
| 频率 | 60 次/分钟/**每把 key**（不按 IP，防伪造） |

**失败不扣分**：引擎不可用、参数缺失、动作未开放，一律 0 扣分。

## 写权限边界

默认**只算不落**：传 `project_id` / `user_id` 会被**主动剥离**，并在 `warnings` 里说明。
受试者数据类动作（CRF 建表、数据导入、脱敏、建模训练）**不在白名单**——目录里没有这些工具。

**唯一例外**：`paper_draft_one_click` 会在后台建一个写作任务并落库，它的
`annotations.readOnlyHint = false`。调用前请先跟用户确认；表里其它生成类都不写库。

## 生成类怎么取结果（异步）

39 个生成类动作是**异步**的：返回 `success: true` + `job_id` + `engine_status: queued`，
**这不是结果，是已受理**。要用 `sanyu_job_status` 轮询：

```json
{ "name": "sanyu_job_status", "arguments": { "job_id": "job_xxxxxxxx" } }
```

每 3 秒一次，最多等 300 秒。`status=succeeded` 取 `result`；`failed` 读 `error`（失败不扣分）。
**拿到 succeeded 之前不要向用户报告任何结果。**

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
