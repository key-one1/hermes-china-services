# MCP Server 配置指南

## 前置条件

```bash
pip install -r requirements.txt
export AMAP_KEY=your_key_here   # 免费申请: https://console.amap.com/dev/key/app
```

---

## Claude Code

编辑 `~/.claude.json`（或项目级 `.claude/settings.json`）：

```json
{
  "mcpServers": {
    "amap": {
      "command": "python3",
      "args": ["/path/to/hermes-china-services/mcp-server/server.py"],
      "env": {
        "AMAP_KEY": "你的高德key"
      }
    }
  }
}
```

重启 Claude Code 后，`/mcp` 可看到 6 个工具。

---

## Codex CLI (OpenAI)

编辑 `~/.codex/config.toml`：

```toml
[mcp_servers.amap]
command = "python3"
args = ["/path/to/hermes-china-services/mcp-server/server.py"]

[mcp_servers.amap.env]
AMAP_KEY = "你的高德key"
```

---

## Cursor

在 Cursor 设置 → MCP → Add new MCP server：

- **Name:** amap
- **Type:** stdio
- **Command:** `python3 /path/to/hermes-china-services/mcp-server/server.py`
- **Environment Variables:** `AMAP_KEY=你的高德key`

---

## Hermes Agent

Hermes 原生支持 MCP。编辑 `~/.hermes/config.yaml`：

```yaml
mcp_servers:
  amap:
    command: python3
    args:
      - /path/to/hermes-china-services/mcp-server/server.py
    env:
      AMAP_KEY: "${AMAP_KEY}"
```

或者在 `~/.hermes/.env` 中设置 `AMAP_KEY`，Hermes 自动注入。

---

## 验证

任意 MCP 客户端连接后调用 `amap_geocode`：

```
address: "杭州西湖"
```

预期返回：
```json
{
  "status": "1",
  "geocodes": [{
    "location": "120.147,30.260",
    "formatted_address": "浙江省杭州市西湖区西湖",
    "adcode": "330106"
  }]
}
```
