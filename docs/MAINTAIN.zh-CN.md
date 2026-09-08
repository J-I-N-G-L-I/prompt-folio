# Prompt Folio 3.1：维护与扩展

## 1. 内容源与生成文件

新版采用“一条 Prompt 一个 JSON 文件”。日常维护不用直接编辑 HTML：

| 要修改什么 | 编辑哪里 |
|---|---|
| 提示词名称、简介、正文、开场提问 | `content/prompts/<id>.json` |
| 品牌、站点地址、界面译文、平台指南 | `content/library.json` |
| 网页结构、布局、交互 | `templates/index.html`、`templates/styles.css`、`templates/app.js` |
| 图标 | `assets/icons/*.svg` |
| 分享图 | `assets/social-preview.svg` 和对应 PNG |
| 发布与验证流程 | `.github/workflows/publish.yml` |

`index.html`、`README.md`、`docs/PAPER-MENTOR.zh-CN.md` 是生成文件；工作流会同步它们。不要仅手改生成文件，因为下一次构建会覆盖修改。`_site/` 是完整静态网站产物，不需要上传或提交到源码仓库。

## 2. 通过 GitHub 网页修改已有条目

先打开对应 JSON 文件，点击编辑。只修改你需要的 `locales` 中 `title`、`description`、`body`、`starter` 等字段。JSON 字符串的换行使用 `\n`，英文双引号需要写成 `\"`，最后一个属性后不能多加逗号。

建议创建分支、提交 PR，等待 Build and test 通过。合并 main 后，工作流依次构建、同步 README、发布网站。内容校验失败时，不会继续发布该版本；应查看 Actions 中第一个失败步骤。

名称本地化和稳定标识分开。例如 `id: direct-first` 保持不变，中文 `title` 为“先说重点”，英文为“Direct First”。修改 title 会同步显示在目录、详情、组合开关、README 和浏览器标签。旧的显式 `#prompt=direct-first` 链接继续有效。

## 3. 新增提示词与使用级别

目前有三个级别：用户级（`user`）用于长期偏好，项目级（`project`）用于持续工作流程，对话级（`chat`）用于直接在当前聊天中启用的任务和游戏。对话级可以在同一聊天中连续互动；新聊天需重新提供提示词和必要记录。

对话级首个条目为 `dnd-dungeon-master`（D&D 地下城主）。正文保留用户提供的完整简体中文运行提示词，并提供全部 16 个语言版本；各译文的默认叙事语言随版本调整，规则数值和存档字段保持一致。译文由 AI 完成，未使用谷歌翻译，也未标记为独立母语校审。两个既有条目的 16 种正文保持不变。

正文超过 8,000 字符的条目在 README 中链接至完整静态 Markdown 导出，避免超过 GitHub 的 500 KiB 显示限制；网站详情、复制和下载仍包含全文。生成器和回归检查会验证正文导出完整、D&D 的 16 个版本齐全，以及 README 文件大小。

翻译篇幅要求时直接使用目标语言自然的计数单位，不保留“相当于多少汉字／中文字符”的说明。D&D 的普通叙事参考范围为 400–900，首条回复约 300 以内：简繁中文使用汉字，日语使用字／文字，韩语使用 자，其余现有译文使用各自语言的“词”。这些数值是语言版本各自的写作指引，不表示跨语言等长换算；到达玩家决策点即停的约束继续优先。

复制一份现有条目 JSON，另存为 `content/prompts/new-id.json`。ID 使用小写英文、数字与连字符，并保持唯一。修改：

```text
id                 稳定标识，发布后尽量不改
level              user、project 或 chat
icon               assets/icons 中已有 SVG 的文件名，不含 .svg
version            例如 1.0.0
sourceLanguage     例如 zh-CN
updated            实际内容更新日期
aliases            中英文名称、常用同义词
recommendedWith    可选的用户级条目 ID 数组
locales            实际已经完成的文本与翻译状态
```

每个实际存在的语言至少需要 title、description、body、translation。starter 和 starterTitle 是可选项。项目级可配置 `recommendedWith: ["direct-first"]`；不需要组合时使用空数组。对话级条目使用空数组，直接复制全文到当前聊天；用户级条目不组合项目级条目。

然后在 `content/library.json` 的 `promptFiles` 中增加：

```json
"prompts/new-id.json"
```

新条目允许只有源语言。其他界面语言访问时，会明确显示“当前无该语言版本”并展示源文；不会伪装为已翻译。默认目录和测试的计数由内容计算，无需修改固定条目数量。某些针对已公开条目的专门回归用例会继续保留其 ID，这是验证兼容性的需要。

网站生成器会创建每条条目、各语言的独立 HTML 入口。缺少译文的页面会标注回退，canonical 指向实际源语言，正文的 lang/dir 和下载文件名也使用实际语言。独立 Markdown 导出只为确实存在的版本生成。README 的缺译条目链接到原文段落，避免在每种界面语言下重复长篇原文；展开对应的原文语言和条目即可复制全文。

## 4. 翻译版本与审校

`sourceVersion` 与源版本一致，`sourceHash` 是源正文 SHA-256。若源正文或版本更新而译文尚未同步，生成器会把它标为 stale，网页显示“需要与原文同步”，不会悄悄宣布已完成。

源文修改：更新正文、version 和 updated。随后真正修订译文，再记录新的版本与哈希。辅助命令：

```bash
python tools/translation.py paper-mentor --locales en,fr
```

这个命令只记录你已经完成修订的声明，**不会生成译文，也不会验证译文准确性**。不能用它清除尚未实际完成的过期状态。

经过真实母语者审校后才可以使用：

```bash
python tools/translation.py paper-mentor --locales fr --status reviewed --reviewer "公开署名" --date YYYY-MM-DD
```

没有母语者审校的版本继续标为 `ai-assisted`。翻译完整性、界面测试和模型使用效果分别记录，不能互相替代。

## 5. 平台指南的更新

`services` 使用稳定 ID，包含名称、英文路径、官方文档链接、checked 日期。`guides.user` 和 `guides.project` 指定显示顺序。每种语言的 `routes` 使用相同服务 ID 对应说明。`guides.chat` 为空数组，对话级使用各语言的 `chatUse` 说明，不要求用户配置账号或项目。

调整显示顺序只需调整 guides 中的 ID 列表，译文不会随数组位置错配。新增服务要同时补充所有 UI 语言的 route 文本；实际未核查的入口使用对话内粘贴方法，并注明未核查，不填写虚假的实测结果。

## 6. 本地维护（可选）

Python 3.10+ 可以运行生成器和内容单元测试，均只用标准库。CI 固定使用 Python 3.12、Node.js 22，并安装浏览器测试依赖。

```bash
python tools/build.py
python tools/build.py --check --repository J-I-N-G-L-I/prompt-folio
python tools/test_unit.py
node --check templates/app.js
node tools/test_routes.cjs
```

浏览器检查：

```bash
python -m pip install -r requirements-dev.txt
python -m playwright install chromium
python tools/test_browser.py
```

Linux CI 通过 `python -m playwright install --with-deps chromium` 安装系统依赖。脚本默认使用真实本地 HTTP，并保留 `/prompt-folio/` 项目路径前缀。限制环境下可以明确使用 `--memory` 检查页面逻辑，不能把该模式的结果当作 HTTP 或线上部署测试。

构建后的本地预览：

```bash
python -m http.server 8000 --directory _site
```

在浏览器打开 `http://localhost:8000/zh-CN/`。预览服务以站点内容为根目录，而回归测试服务器另行验证项目路径前缀。

修改 `assets/social-preview.svg` 后，可选择安装 `cairosvg`，再运行 `python tools/render_social.py`；此依赖只用于维护图片，不是构建、部署或网页运行依赖。

## 7. 工作流与分支保护

`build` 只读取源码，执行校验与 Chromium 测试。PR 阶段不会写回或部署。`sync` 只允许更新三个生成文件，推送前检查 main 是否出现更新；禁止强制推送。`deploy` 等待 build 与 sync 都成功后发布已经测试的 `_site`。

机器人更新 README 需要 `contents: write`。采用受保护分支时，优先在本地生成并把三个输出随源文件一起提交，这样同步任务没有差异，不会尝试推送；可以使用只读权限。无需为此关闭既有保护规则。

## 8. 更新质量记录

[评测协议](EVALUATION.md) 提供模型使用观察的记录字段；没有记录前保持未系统评测。网站测试范围在 [TESTING.md](TESTING.md)，当次报告保存在 Actions 的 browser-report artifact。仓库内的 test-report.json 是本发布包的核验快照，不会自动冒充每次 CI 的最新结果。
