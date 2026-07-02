> 🌐 [English](README.md) · [简体中文](README.zh-CN.md)

# ProseForge Agent

面向长篇小说创作的智能体编排层。它在权威的 **ProseForge 引擎**
（`$PROSEFORGE_ROOT`）之上，包裹了规划、检索、起草、评审、修订、深度记忆、
多模型提供方路由、每日工作簿、报告、扩展、智能体运行时、对话、自主目标循环、
MCP 集成、执行环境、技能、托管 cron、可观测性、中间件，以及真实的
发布/二进制/安装包链路。

ProseForge Agent **不**重新实现写作引擎。位于 `$PROSEFORGE_ROOT` 的引擎仍是
项目槽位、流水线动作、护栏、报告和导出的唯一事实源。本包只负责编排：
模型调用、提供方路由、调度、证据包、智能体记忆、工作流状态、对话式智能体
循环，以及后台事件处理。

## Status

在 Python 3.10/3.11、Windows/macOS/Linux 上**全部测试通过**。实现覆盖项目
计划的任务卡 **1–185** —— 完整的核心栈、智能体运行时、对话、原生安装、
加固、自主运行时、智能体工具、引导式安装、小说操作、设定与故事智能、编辑
系统、MCP 集成、提供方/工具韧性、RAG、网关、执行环境、技能、托管 cron、
可观测性、中间件，以及真实发布链路。

### Core stack (1–17)

可移植配置、工作区布局、ProseForge 引擎适配器、提供方契约 + fake provider、
OpenAI 兼容传输、原生/本地提供方档案、记忆 schema/store 及摄取与压实、检索
路由与证据包、阶段计划生成器、每日工作簿引擎、工作流状态与恢复、章节生命
周期（起草 → 评审 → 重写 → 接受）、CLI 命令与报告、扩展，以及带发布检查的
端到端演示。

### Provider registry (18–30)

十个原生提供方档案 —— **OpenAI、Anthropic、Gemini、xAI/Grok、DeepSeek、
Qwen、GLM、Mimo、MiniMax、Doubao** —— 外加能力探测、提供方回退路由、以及
提供方认证流程。所有提供方经由共享的 `HttpTransport`（生产用 `urllib`，测试
用 `FakeHttpTransport`），因此没有测试会触网。

### Agent runtime & chat (33–40)

依赖注入 provider、tools、session store、retrieval、intent router 的
`AgentKernel`；对话模式；权限策略；带能力访问控制的工具注册表；对话 session
store、prompt 协议、带引用证据的检索、对话到工作流的移交，以及后台任务的
智能体事件总线（含进度跟踪）。

### Native install & distribution (41–58)

跨平台应用目录、安装诊断器、首次运行引导、原生密钥存储、提供方安装向导、
pip/pipx/源码与独立二进制打包清单、Windows/macOS/Linux 原生支持检查、shell
补全、升级/迁移/备份、卸载、离线本地模型安装、本地智能体服务 API、智能体
档案，以及跨平台原生 QA 矩阵。

### Hardening & release gates (61–67)

提供方用量计量 + 预算、智能体安全 / 提示注入护栏、流式响应、跨平台 CI 流水
线、并发 + 建议式文件锁、能力开关与安全模式启动，以及基于权威 fake 的
契约/黄金回归层。

### Autonomous runtime & agent tooling (68–75)

有界自主循环（规划 → 行动 → 校验 → 反思 → 重复）、依赖感知的任务规划器与
TODO、带有界反思的自校验（可插拔领域校验器，如 ProseForge 评审门）、通用工具
框架（`fs.read/write/edit`、`web.fetch/search`）、工具执行沙箱、子智能体委派、
可中断与转向，以及智能体评测框架。

### Guided setup & novel operations (76–87)

引导式 `pf-agent setup` 向导、多种安装模式、配置生成器、安装恢复、首次运行
bootstrap、小说项目清单、工件图、批量导入、场景级工作流、章节重组、
导出/编译流水线，以及出版元数据。

### Canon & story intelligence (88–94)

设定圣经管理器、连续性冲突解决器、时间线引擎、情节线管理器、伏笔追踪器、
人物弧光追踪器，以及关系图。

### Writing quality & editorial (95–108)

写作领域工具注册表、显式写作规则、语气/风格档案编译器、质量门、文学回归
套件、重写策略库（九种可选策略）、读者体验评审、全稿搜索、项目健康诊断器、
带 diff/分支/批准门回滚的草稿版本管理、分阶段编辑流水线（大纲 → … → 定稿）、
人工批准队列、带完成度预测的写作分析，以及带预演还原的校验和备份。

### Agent protocol, prompt, context, audit (109–115)

结构化函数调用适配器、结构化输出修复、带压实的上下文窗口管理、系统提示管理、
提示模板注册表、多模态 / 附件摄取（PDF、DOCX、CSV、Markdown、TXT、图片元数据
+ vision 描述器），以及带确定性重放的审计轨迹。

### MCP integration (116–121)

MCP 客户端基础（`stdio` 与 HTTP/SSE 传输，测试用 `StaticMCPTransport`）、
服务器注册表、安全边界、工具批准门、工具 schema 校验，以及凭据边界。真实
进程/网络传输可在调用时插入；测试套件使用确定性的进程内传输。

### Provider & tool resilience (122–126)

工具超时 / 速率限制 / 熔断器、提供方回退、优雅降级、离线模式，以及请求缓存。

### Sessions & context (127–132)

对话生命周期、跨会话搜索、会话导出/导入、会话分支、会话合并，以及多上下文
切换。

### Retrieval & RAG (133–136, 138–140)

带 fake provider 的嵌入抽象、可插拔向量库、混合检索（BM25 + 向量）、RAG 摄取
流水线、证据包检索，以及 RAG 评测框架。

### Notifications & jobs (137, 141–143)

通知核心、桌面通知、webhook 通知，以及任务状态中心。

### Plugins (144–151)

插件清单规范、发现、安装/更新/移除 CLI、权限模型、沙箱、依赖管理、hooks，
以及插件测试框架。

### TUI & terminal (152–154)

终端 UI 基础、slash 命令注册表、流式工具输出，以及终端会话操作。

### Messaging gateway (155–161)

消息网关核心、平台适配器契约，以及 Telegram、Slack、Discord、Signal、
移动邮件、Email 的适配器和中继鉴权 + 配对流程。适配器随附契约形状的 fake
传输；真实传输接线按适配器进行，凭据在调用时读取。

网关投递可靠性（重试/退避/死信）与媒体 + 语音摄取补全了网关轨道。

### Execution environments (162–168)

执行环境抽象、local / Docker / SSH / Singularity / Modal / Daytona 后端、
远程文件同步与检查点，以及进程注册表 + 终端生命周期。后端当前输出确定性的
预演计划；真实子进程调用可注入并在调用时接线。

### Managed tool gateway (169–174)

托管工具网关基础、网页搜索与 URL 安全工具、云浏览器适配器、媒体生成与转写
工具、工具结果工件 + 输出上限，以及技能规范与注册表。

### Skills (175–178)

技能中心安装与同步、自主技能创建、技能自改进 + 溯源跟踪，以及技能使用分析
+ 安全审计面。

### Long-lived agents (179–180)

用户模型 + 记忆提醒，以及托管 cron + 缩容至零的生命周期支持（带鉴权 + 幂等的
cron 触发、确定性唤醒计划、本地回退）。

### Observability & research (181–182)

只读观察者钩子，覆盖 7 类事件族
（`session / turn / provider_request / tool_call / approval / subagent /
job`）、correlation-id 传播、fail-open 错误处理，以及
`pf-agent telemetry export --format jsonl --redact` 命令。中间件钩子（可改变
行为、opt-in、有序、fail-open），重写后的请求由下游策略重新校验，外加面向
研究的 `pf-agent trajectories export --redact --format jsonl`。

### Real release chain (183–185)

`PyPIPublisher` —— 面向 TestPyPI / PyPI 的真实 `python -m build` +
`twine upload`，由 Task 47 `PackageChecker` 与重复版本拒绝把关，测试用可注入
runner + `dry_run`；token 绝不出现在计划、报告或日志中。

`BinaryBuilder` —— 由 Task 48 `BinaryManifest` 派生的真实 PyInstaller 调用，
以 `pf-agent --version` 冒烟命令把关；报告仅含可移植路径，测试用 `dry_run`。

`InstallerBuilder` —— 各 OS 安装包（`.msi` 走 `signtool`、`.dmg` 走
`codesign`、`install.sh` 走 `gpg`），安装路径来自 `AppDirs`，签名受凭据把关，
凭据缺失时警告跳过，仍产出未签名但有效的安装包。

## Requirements

- Python **3.10+**（在 3.10 与 3.11 上测试）
- `pyyaml>=6.0`
- 开发与测试运行需要 `pytest>=7.0`

其余全部仅依赖标准库。提供方使用 `urllib`；MCP、网关和执行后端接受注入的
客户端，因此运行测试套件无需任何第三方网络依赖。

## Layout

参见英文 `README.md` 的 Layout 章节，其中列出 `src/proseforge_agent/` 下全部
34 个子包与它们的职责。目录布局在中英文版本之间保持一致。

## Development

运行完整测试套件。无需安装 —— `pythonpath` 已在 `pyproject.toml` 配置：

```powershell
python -m pytest -q
```

直接调用 CLI：

```powershell
python -m proseforge_agent.cli --help
```

可编辑安装后，`pf-agent` 命令即在 PATH 上：

```powershell
python -m pip install -e ".[dev]"
pf-agent --help
```

## CLI Highlights

`pf-agent` 命令暴露若干命令组。每个组共享 `--format`、`--write`、`--dry-run`、
`--out` 输出开关（少数自带 `--format` 的组除外，如输出 JSONL 的 `telemetry`
与 `trajectories`）。

渲染完整命令参考：

```powershell
pf-agent report command-reference --format terminal
```

无参启动即进入对话 REPL（已配置时）或首次运行引导（未配置时）：

```powershell
pf-agent
pf-agent chat --message "写一个开头" --provider fake
```

更多示例（改写策略、小说操作、MCP、技能、托管 cron、可观测性导出等）见英文
`README.md` 的对应章节。

## Provider Profiles

提供方档案位于 `configs/providers/`，适配器与测试位于
`src/proseforge_agent/llm/providers/` 和 `tests/`。当前档案：**OpenAI、
Anthropic、Gemini、xAI/Grok、DeepSeek、Qwen、GLM、Mimo、MiniMax、Doubao**。

请把密钥放在环境变量或本地被忽略的配置文件里。不要把 API key 提交进提供方
YAML。

## What is production-ready and what is contract-only

项目有意区分"契约 + fake"与"真实接线"，以保持测试确定性与离线可跑。

- **今天即可用于生产** —— LLM 提供方（经 `urllib` 的真实 HTTP，10 个档案）、
  记忆（SQLite）、工作区 + 配置、规划 / 每日 / 章节 / 工作流、工具注册表 +
  权限策略、附件摄取、嵌入 + 检索 + RAG、技能、托管 cron 校验、遥测与轨迹
  导出，以及真实发布/二进制/安装包链路（经可注入 runner）。
- **契约完备、传输可插拔** —— MCP `stdio` / HTTP/SSE（测试用进程内
  `StaticMCPTransport`；真实进程/套接字传输可插拔）、执行环境
  （Docker/Modal/Daytona/SSH/Singularity 输出确定性预演计划，可由真实后端
  执行），以及网关平台适配器（Telegram/Slack/Discord/Signal/Email 随附契约
  形状 + fake 传输；真实 HTTP 在调用时接线）。

## ProseForge Engine Boundary

当命令需要发现或调用权威 ProseForge 引擎时，设置 `PROSEFORGE_ROOT`。本仓库
仍是编排层，应避免重复引擎所拥有的项目、流水线、护栏、导出或报告逻辑。

## License

MIT。见 `LICENSE`。
