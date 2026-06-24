# Hermes China Services

[English](#english) | [中文](#中文)

---

## 中文

让 **任何 AI Agent** 接入中国日常生活服务。基于 MCP（Model Context Protocol，模型上下文协议），一次配置，所有 Agent 通用。

### 支持哪些 Agent

| Agent | 接入方式 | 状态 |
|-------|---------|------|
| Claude Code | MCP（原生） | ✅ |
| Codex CLI | MCP（原生） | ✅ |
| Cursor | MCP（原生） | ✅ |
| Hermes Agent | MCP + 原生 Skill | ✅ |
| 其他 MCP 客户端 | MCP stdio | ✅ |

### 30 秒上手

```bash
# 1. Clone
git clone https://github.com/key-one1/hermes-china-services.git
cd hermes-china-services

# 2. 安装依赖
pip install -r mcp-server/requirements.txt

# 3. 申请高德 API Key（免费，5000次/天）
#    → https://console.amap.com/dev/key/app

# 4. 配置你的 Agent（选一个）
```

**Claude Code：** 编辑 `~/.claude.json`，加入：
```json
{
  "mcpServers": {
    "amap": {
      "command": "python3",
      "args": ["/完整的路径/hermes-china-services/mcp-server/server.py"],
      "env": { "AMAP_KEY": "你的key" }
    }
  }
}
```

**Codex：** 编辑 `~/.codex/config.toml`：
```toml
[mcp_servers.amap]
command = "python3"
args = ["/完整的路径/hermes-china-services/mcp-server/server.py"]
[mcp_servers.amap.env]
AMAP_KEY = "你的key"
```

**Cursor：** 设置 → MCP → Add → stdio → `python3 /完整的路径/hermes-china-services/mcp-server/server.py` → 环境变量 `AMAP_KEY=你的key`

**Hermes（原生）：** `ln -s $(pwd)/skills/amap ~/.hermes/skills/china-services/amap` → 在 `~/.hermes/.env` 加 `AMAP_KEY=你的key`

> 详细配置见 [mcp-server/README.md](./mcp-server/README.md)

### 然后直接在 Agent 里说

```
"附近有什么好吃的"
"查一下这个地址的坐标：杭州市西湖区龙井村"
"从天安门到三里屯怎么坐公交"
"北京明天天气"
```

Agent 自动调用对应的工具，你不需要记命令。

### 已完成的 Tools

| Tool | 功能 | 
|------|------|
| `amap_nearby` | 周边搜索（餐厅/停车场/医院/加油站...） | 
| `amap_text_search` | 全城关键词搜索 POI |
| `amap_geocode` | 地址 → 坐标 |
| `amap_regeo` | 坐标 → 地址 |
| `amap_route` | 路线规划（驾车/步行/公交/骑行） |
| `amap_weather` | 天气查询（当天 + 4天预报） |

### 计划中的 Skills

- 快递查询（快递100 API）
- 空气质量（和风天气 API）
- 火车票查询（12306 接口）
- 医院挂号

### 为什么是 MCP

SKILL.md 是 Hermes 私有格式，别的 Agent 读不懂。MCP 是跨 Agent 的通用协议——就像 USB，不管你用什么 Agent，接口一样就能用。同一个 `server.py`，Claude Code、Codex、Cursor 全都能调。

底层仍然是同一个 `amap.py` 脚本，MCP Server 只是给它挂了一个通用协议壳。

---

## English

Open-source MCP server & skill collection enabling **any AI agent** (Claude Code, Codex, Cursor, Hermes) to interact with Chinese daily-life services. One `pip install`, one config block, works everywhere.

### Quick Start

```bash
git clone https://github.com/key-one1/hermes-china-services.git
cd hermes-china-services
pip install -r mcp-server/requirements.txt
# Get free API key at https://console.amap.com/dev/key/app
# Add to your agent's MCP config — see mcp-server/README.md
```

### Tools

| Tool | Capability |
|------|-----------|
| `amap_nearby` | Search nearby POIs |
| `amap_text_search` | Keyword-based POI search |
| `amap_geocode` | Address → coordinates |
| `amap_regeo` | Coordinates → address |
| `amap_route` | Driving / Walking / Transit / Bicycling directions |
| `amap_weather` | Current + 4-day forecast |

### License

MIT
