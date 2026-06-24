# Hermes China Services

[English](#english) | [中文](#中文)

---

## 中文

让 AI Agent（Hermes、Claude Code、Codex、Cursor 等）接入中国日常生活服务的开源技能集合。

### 为什么

西方的 AI Agent 生态有 Uber Eats、DoorDash、Google Maps 的 MCP Server。中文世界里，Agent 能写代码，但不能订外卖、查公交、挂号、查快递。

这个项目填补这个空白 —— **用公开 API 把中国服务变成 Agent 可调用的 Skill。**

### 已完成的 Skills

| Skill | 功能 | 数据源 | API Key |
|-------|------|--------|---------|
| [amap](./skills/amap/) | 周边搜索、地理编码、路线规划（驾车/步行/公交）、天气查询、会话位置记忆 | 高德地图 Web API | 免费（5000次/天） |

### 计划中的 Skills

- 快递查询（快递100 API）
- 空气质量（和风天气 API）
- 火车票查询（12306 接口）
- 个税/社保查询
- 医院挂号

### 使用

每个 skill 独立配置。进入对应目录查看 README 或 SKILL.md 了解具体设置步骤。

通用步骤：

```bash
# 1. Clone 仓库
git clone https://github.com/key-one1/hermes-china-services.git

# 2. 将 skill 链接到 Hermes（或复制到 ~/.hermes/skills/）
ln -s $(pwd)/hermes-china-services/skills/amap ~/.hermes/skills/china-services/amap

# 3. 配置 API Key
echo 'AMAP_KEY=你的key' >> ~/.hermes/.env

# 4. 重启 Hermes 会话
```

### 兼容性

- **Hermes Agent** — 原生支持
- **Claude Code** / **Codex** / **Cursor** — 通过 MCP Server 桥接（计划中）

### License

MIT

---

## English

Open-source skill collection enabling AI agents (Hermes, Claude Code, Codex, Cursor) to interact with Chinese daily-life services.

### Skills

| Skill | Capabilities | Source | Key |
|-------|-------------|--------|-----|
| [amap](./skills/amap/) | Nearby search, geocoding, route planning (driving/walking/transit), weather, session location memory | Amap Web API | Free (5000 calls/day) |
