# 将 Direct First 升级为 Prompt Handbook

版本：2.0.0 · 资料核查日期：2026-09-08

这份压缩包包含可直接部署的网站及其维护源文件。交付本身没有修改 GitHub 仓库；完成上传后，现有 Pages 流程才会发布新版。建议保留仓库名 `AI-direct-first` 和现有网址。

## 1. 解压并确认目录

进入解压后的 `prompt-handbook` 文件夹。下面这些内容应处于同一层：

```text
index.html                  已生成的完整网站
README.md                   已生成的多语言手册
favicon.svg / favicon.ico   浏览器标签页图标
apple-touch-icon.png        网页快捷方式图标
LICENSE                     保留原 MIT 版权声明
.nojekyll                   保留静态站点配置
assets/                     SVG 图标与分享图片
content/                    唯一的多语言内容源
templates/                 HTML / JavaScript 源模板
tools/                     生成与可选测试脚本
docs/                      发布、维护、设计与核验说明
```

首次部署不需要运行 Python、Node.js、npm 或任何构建命令。生成好的 `index.html` 已内置样式、逻辑和所有译文。

## 2. 备份现有版本

可以先通过仓库 Code 菜单下载旧版 ZIP，或记下当前提交。保留提交历史，出现问题时方便恢复上一版。不要为了升级删除整个仓库。

## 3. 将文件上传到原仓库根目录

目标仓库：

```text
J-I-N-G-L-I/AI-direct-first
```

进入仓库主页，使用 `Add file → Upload files`，上传解压目录中的文件与子文件夹。把子文件夹整体拖入上传区可保留结构；上传列表应出现 `assets/icons/user.svg`、`content/library.json` 等路径。

提交说明建议：

```text
Refactor Direct First into a multilingual prompt handbook
```

将提交放入当前 Pages 发布源分支，通常是 `main`。选择新分支时，合并进入发布源分支后才会更新网站。上传操作的官方说明：[Adding a file to a repository](https://docs.github.com/en/repositories/working-with-files/managing-files/adding-a-file-to-a-repository)。

本次是**完整目录更新**：替换已有 `index.html`、`README.md` 和图标，同时添加四个子目录。不要把 ZIP 文件本身当作网站上传，也不要把整个 `prompt-handbook/` 再套在仓库根目录下面。

隐藏文件 `.nojekyll` 上传不便时，保留仓库原有文件即可。`LICENSE` 保留了原文，内容相同无需重复修改。`.gitignore` 仅用于本地开发，可一并保留。

## 4. 保持 Pages 设置

现有站点已经正常运行，继续使用原配置。分支发布配置通常是：

```text
Settings → Pages
Source: Deploy from a branch
Branch: main
Folder: /(root)
```

推送到发布源会触发更新，在 Actions 中检查 Pages 部署结果，再打开 Settings → Pages 提供的网址。官方说明：[Configuring a publishing source](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)。

公开站点地址保持：

```text
https://j-i-n-g-l-i.github.io/AI-direct-first/
```

## 5. 发布后的验收

打开首页，应显示用户级、项目级两个分类和两条提示词。分别进入条目，切换语言，检查全文；点击复制并在文本编辑器中核对；下载 `.md`，确认内容一致；在 Paper Mentor 中勾选“同时附加 Direct First”，确认预览与复制内容都包含两部分。

在窄屏设备上检查导航与阅读，切换阿拉伯语检查从右向左排版。实际标签页图标、系统剪贴板权限和 Pages 资源路径必须在部署后核对，本地测试没有覆盖这些实际环境。

图标引用包含 `?v=handbook-2` 缓存版本。站点仍显示旧内容时，先确认部署完成，再刷新或重新打开标签页。

### 新旧链接

```text
新版中文首页
https://j-i-n-g-l-i.github.io/AI-direct-first/#view=library&lang=zh-CN

Direct First
https://j-i-n-g-l-i.github.io/AI-direct-first/#prompt=direct-first&lang=zh-CN

论文研读导师
https://j-i-n-g-l-i.github.io/AI-direct-first/#prompt=paper-mentor&lang=zh-CN

论文研读导师 + Direct First
https://j-i-n-g-l-i.github.io/AI-direct-first/#prompt=paper-mentor&with=direct-first&lang=zh-CN
```

不带参数的站点根地址进入新版首页。旧的 `#lang=zh-CN` 继续打开 Direct First，兼容已分享的老链接。分享新版首页请使用明确的 `#view=library`。

## 6. 用户怎样使用两级提示词

分类表示使用范围，不赋予指令更高的权限。用户级适合帐号偏好；项目级适合专用项目、Gem 或对话工作流。具体继承方式由各平台决定。

ChatGPT 官方说明，项目内指令会覆盖全局自定义指令；Gemini 的个人指令目前不适用于 Gems。项目中同时需要 Direct First 时，可勾选组合复制，再把两段一起保存到对应项目。站点不会自动写入任何 AI 帐号。

参考：[ChatGPT Projects](https://help.openai.com/en/articles/10169521) · [Gemini personal instructions](https://support.google.com/gemini/answer/16598625)。

## 7. 后续更新

只改 `content/library.json`，然后运行：

```bash
python tools/build.py
python tools/build.py --check
```

把源文件和生成后的 `index.html`、`README.md`、必要的文档一起提交。详见 [维护指南](MAINTAIN.zh-CN.md)。
