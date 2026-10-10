# Claude Desktop 接非官方模型：文本走 CC Switch，全模态走 OpenRouter

> 面向中国用户。所有步骤都在 Windows 11 + Claude Desktop 上**实测跑通**，踩过的坑都写在文末。
> 截图与版本号会随软件升级变化，以你装到的那版为准。

---

## 一分钟看懂

Claude Desktop 默认只连 Anthropic 官方模型。想用别的，需要**两条互不冲突的通道**：

| 你想干的事 | 用哪个 | 一句话原理 |
|---|---|---|
| 让 Claude **对话/写代码**用 DeepSeek、Kimi、GLM 等 | **CC Switch** | 桌面 App 一键改 Claude 的连接信息，或起本地代理做格式转换 |
| 让 Claude **出图、出视频、配音、转写、算向量** | **OpenRouter + MCP** | 把 OpenRouter 的接口挂成 Claude 的工具 |

**关键**：这两条不抢位置。CC Switch 管的是「Claude 用哪个大脑说话」，OpenRouter 管的是「Claude 手边有哪些工具」。**可以同时开。**

---

## 方案一 · 文本模型：CC Switch

### 它是什么

[CC Switch](https://github.com/farion1231/cc-switch)（MIT，官网 [ccswitch.io](https://ccswitch.io)）是一个桌面端「供应商切换器」，支持 Claude Code、**Claude Desktop**、Codex、Gemini CLI、Grok Build、OpenCode、OpenClaw、Hermes、Pi、MiniMax Code。

它的官方定位是 **All-in-One Manager**：

- **一键切换** API 供应商——点一下预设、填个 key，不用手改 JSON/TOML/YAML
- **只替换连接信息**（endpoint / key / model），**你自己加的插件、hooks、MCP、注释原样保留**
- 改写配置文件前**自动备份**
- **本地路由（Local Routing）**：请求经本机转发，**并做 API 格式转换**
- 集中管理 **MCP / Skills / Prompts**，可选择同步给哪些工具

### 装与用

1. 到 [Releases](https://github.com/farion1231/cc-switch/releases) 下 `CC-Switch-v{版本}-Windows.msi`（或 Portable zip）
2. 首次启动会**自动导入**你已有的 Claude Code / Codex / Gemini CLI 配置，并为每个工具（含 Claude Desktop）加一个官方 provider，**不会丢配置**
3. 在 Claude Desktop 那一页选一个 provider、填 key，点切换

### 三个必须知道的点

1. ⚠️ **Claude Desktop 切换后必须完全重启 App 才生效**（Claude Code 不用重启）
2. ⚠️ **Claude Desktop 只支持两种模式：`Direct` 和 `Model Mapping`**。选 `Model Mapping` 时请求会走它的本地路由
3. ⚠️ 在 Claude Desktop 页面点开的 **MCP / Skills / Prompts 面板，实际作用于 Claude Code**，不是 Claude Desktop——别被界面位置误导

> 官方原话：Claude Desktop 的支持列是「Switch + Model Mapping only」。
> 具体界面以 [用户手册](https://github.com/farion1231/cc-switch/blob/main/docs/user-manual/en/README.md) 为准。

---

## 方案二 · 全模态：OpenRouter + MCP

CC Switch 解决的是**文本**。图 / 视频 / 语音这些，它管不了——那是 OpenRouter 的活。

### OpenRouter 有哪些模态

官方模型目录按 `output_modalities` 分成这些（数字是实测当时的数量，会变）：

| 模态 | 数量 | 接口 |
|---|---|---|
| text | 458 | `/api/v1/chat/completions` |
| image | 61 | `/api/v1/images` |
| video | 30 | `/api/v1/videos` |
| speech（TTS） | 32 | `/api/v1/audio/speech` |
| transcription（STT） | 25 | `/api/v1/audio/transcriptions` |
| embeddings | 37 | `/api/v1/embeddings` |
| rerank | 9 | `/api/v1/rerank` |
| **decisions** | 19 | **`/api/alpha/decisions`**（注意：**不在 `/v1` 下**） |

### 怎么接进 Claude

**第一步：装一个现成的 OpenRouter MCP server**

推荐 [stabgan/openrouter-mcp-multimodal](https://github.com/stabgan/openrouter-mcp-multimodal)（Apache-2.0），19 个工具，覆盖 chat / 图片 / 视频 / 语音 / 转录 / 重排。

```bash
claude mcp add --scope user --transport stdio openrouter -- npx -y @stabgan/openrouter-mcp-multimodal
```

（它需要 `OPENROUTER_API_KEY` 环境变量，见你的 key 页面 <https://openrouter.ai/keys>。）

**第二步：补上它没有的两类（embeddings / decisions）**

上面那个项目**没有** embeddings 和 decisions。用配套插件补齐：

```bash
claude plugin marketplace add Joey1444/openrouter-models-skill
claude plugin install openrouter-models@openrouter-models
```

它还会给你一条 `/openrouter-models:models` 命令，专门用来**挑模型**（见下）。

### 免费模型怎么挑（这是最容易踩坑的地方）

别去官网一个个翻。装完上面的插件后：

```
/openrouter-models:models                 # 每类模态有多少、几个免费
/openrouter-models:models image --free    # 图片里哪些真免费
/openrouter-models:models speech          # 语音全部，便宜在前
```

**「真免费」的判据（实测得出，别简化）**：

- 只有 **id 带 `:free`** 或 **pricing 全部字段为 0** 才算免费
- ⚠️ 只看 `prompt` / `completion` 会把**收费模型误判成免费**——真实计费常在 `image_output` / `image_token`
- ⚠️ **视频类定价压根不在接口里** → 一律标「价格未知」，当收费对待

**免费模型会失效**。本文写作时，多数教程推荐的默认免费 TTS 模型已经 404；可用的换成了 `fish-audio/s2.1-pro-free:free`。**用之前先试一次**。

---

## 两条通道怎么配合

```
Claude Desktop
   ├── 说话用哪个大脑  ←  CC Switch（DeepSeek / Kimi / GLM / 官方…）
   └── 手边有哪些工具  ←  OpenRouter MCP（出图 / 出视频 / 配音 / 向量…）
```

- 想在 Claude 里说「帮我生成一张图」→ 走 OpenRouter
- 想省钱把对话换成国产模型 → 走 CC Switch
- 两个同时开没有冲突

---

## 实测踩坑清单

以下都在 Windows 11 + Claude Desktop 上真实撞过：

1. 🔴 **`decisions` 在 `/api/alpha/`，不在 `/api/v1/`**。OpenAPI 的 `servers` 只声明了 `/api/v1`，但 `/v1/alpha/decisions` 是 404。
2. 🔴 **列模型必须带 `?output_modalities=<模态>`**。不带过滤只返回文本模型（458）；带上才有完整的图/视频/语音等。官方模态名是 **`transcription`**（不是 `speech-to-text`）。
3. 🔴 **Windows GUI 里找不到 `npx`**。Claude Desktop 从系统 PATH 启动，可能拿不到终端里的 `npx`。解法：把命令写成**绝对路径直跑**，例如 `"command": "C:/nvm4w/nodejs/node.exe", "args": [".../dist/index.js"]`，或先用 `cmd /c` 包一层。
4. 🔴 **免费 TTS 的默认模型随时失效**。先验证再依赖。
5. ⚠️ **配置里的反斜杠会被吃掉**。手写 `D:\apps\x` 在某些工具链里会被解释成转义（`\a` = 响铃符）。**写路径统一用正斜杠 `D:/apps/x`**，最省事。
6. ⚠️ **命令行的中文参数在 Windows 上会被 GBK 破坏**。CLI 传中文 state 给 decisions 会报 `Request contains invalid Unicode text`——改走 Claude 的工具调用，或把中文写进文件再传路径。
7. ⚠️ **CC Switch 切完 Claude Desktop 要重启 App**。不重启看着像"没生效"。

---

## 成本

| 项 | 说明 |
|---|---|
| CC Switch | 免费（MIT 开源） |
| OpenRouter 文本 | 按 token 计；**有真免费模型**（如 `google/gemma-4-31b-it:free`），但会限流 |
| OpenRouter 出图 | `inclusionai/ming-image-0.1-design` 实测 **免费**，出 1440×2560 |
| OpenRouter 视频 | **基本都要钱**，且接口不给定价，需去官网核 |
| 真实花费 | 响应里的 `usage.cost` 字段是权威数字，别自己估 |

---

## 许可与出处

- 本指南原创，MIT。
- CC Switch 的事实来自其 README 与官方手册；OpenRouter 的数字与判据来自**本机实测**。
- 提到的第三方项目归各自作者所有：CC Switch（farion1231，MIT）、stabgan/openrouter-mcp-multimodal（Apache-2.0）、OpenRouter（其服务条款适用）。

---

## 常见问题

**Q：只用 OpenRouter，不用 CC Switch 行不行？**
行。OpenRouter 也有文本模型。CC Switch 的价值在于**一键切换 + 本地路由 + 集中管 MCP/Skills**，纯属顺手。

**Q：CC Switch 会不会弄坏我原来的配置？**
它只替换 endpoint / key / model，且改写前自动备份、首次启动自动导入原配置。但仍建议自己再备份一份。

**Q：为什么 Claude Desktop 不像 Claude Code 那样直接支持所有 MCP？**
Claude Desktop 的 MCP 走的是 `claude_desktop_config.json`，Claude Code 走 `~/.claude.json` / 项目 `.mcp.json`。两处都要分别配——CC Switch 里那个 MCP 面板只管 Claude Code 那侧。
