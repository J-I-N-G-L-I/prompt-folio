# Prompt Folio 更新与部署指南

适用仓库：`J-I-N-G-L-I/prompt-folio`。本更新包以原提交 `bb8ec49acf454a207cb63085b1deffa6f88c6f8b` 为基础制作；没有直接修改远程仓库。

## 这次最重要的区别

网站现在由 GitHub Actions 构建：`内容 → 校验与测试 → 同步 README/根页面 → 发布 _site/`。**Pages 的 Source 需要从 Deploy from a branch 改成 GitHub Actions。** 全部真实静态详情路径由工作流生成，无需逐个上传各语言目录。不能仅上传根目录 index.html。

包内保留可直接阅读的完整 README。更新后仍然使用原域名和仓库，中文首页为：

```text
https://j-i-n-g-l-i.github.io/prompt-folio/zh-CN/
```

## 1. 备份

在当前仓库选择 `Code → Download ZIP`，保存为 `prompt-folio-backup-before-v3.zip`。需要可审查的回滚记录时，同时记录当前 main 的提交哈希。不要删除仓库或提交历史。

## 2. 解压新版并检查层级

解压 `prompt-folio-v3.0.0.zip`，进入其中的 `prompt-folio`，应直接看到 README.md、index.html、.github、content、templates、tools、assets、docs 等。

上传这一层里面的内容。不要上传 ZIP 文件本身，也不要在仓库根目录额外创建一层 prompt-folio 文件夹。旧的 LICENSE 版权行已保留。完整覆盖这些同名文件即可；本次不需要清空仓库。

Windows 可以在文件资源管理器的“查看 → 显示”中开启隐藏项目。重点确认 `.github/workflows/publish.yml`。通常以点开头的文件夹也可以拖入浏览器。

## 3. 建一个升级分支（推荐）

回到仓库的 Code 页面，打开显示 main 的分支下拉框，输入 `upgrade-folio-v3`，选择从 main 创建该分支。以后这个分支上的上传尚不会替换线上版本。

确认分支已经切换到 upgrade-folio-v3，选择 `Add file → Upload files`。将新版文件夹内部的全部文件与子文件夹拖入上传区域。列表里的路径应是：

```text
.github/workflows/publish.yml
content/library.json
content/prompts/direct-first.json
content/prompts/paper-mentor.json
templates/app.js
templates/styles.css
tools/build.py
README.md
index.html
```

错误示例为 `prompt-folio/index.html`。发现多套一层时，撤掉待上传内容，重新进入本地文件夹内部选择内容。

提交说明：`Upgrade Prompt Folio: localized titles, mobile UX and verified publishing`。将文件提交到当前升级分支。整个源码包低于 GitHub 网页一次 100 个文件的限制。

若 `.github` 没有上传成功，可在该分支选择 `Add file → Create new file`，输入完整文件名 `.github/workflows/publish.yml`，把更新包中同名文件的全部文本粘贴进去并提交。其余 Issue 模板也可用相同方式补上。

## 4. 创建 Pull Request 并查看检查

选择 `Compare & pull request`，确认 base 为 main、compare 为 upgrade-folio-v3，创建 PR。检查 `Validate, sync and publish` 中的 `Build and test`。该任务会生成网站、验证全部语言和链接，并在本地 HTTP 服务器上运行 Chromium 测试。PR 阶段不写回 main，也不部署。

若页面提示需要批准工作流，在你确认这是自己上传的文件后批准运行。若根本没有检查，先确认 PR 中确实包含 `.github/workflows/publish.yml`，再检查 Settings → Actions → General 是否允许本仓库运行官方 Actions。

等待检查通过再继续。首次安装浏览器依赖可能需要几分钟。失败时查看第一个红色 step 的日志；不要仅看旧的 Pages 任务是否成功。

## 5. 更改 Pages 的发布源

在仓库 `Settings → Pages → Build and deployment` 中：

```text
Source: GitHub Actions
```

本版不选择 main / root 或 docs 目录。新的静态路由只存在于生成的 `_site/` 发布产物中，保持旧的分支发布方式会让详情页刷新或直达出现 404。

工作流已经声明所需权限：构建任务只有读取权限；同步任务需要 contents: write；发布任务需要 pages: write 和 id-token: write。无需创建个人访问令牌或粘贴密钥。

个人无保护分支仓库通常可以直接使用这些声明。遇到同步时 403 或策略限制，再查看 `Settings → Actions → General → Workflow permissions`，确认允许所需写入。组织策略或受保护分支可能限制机器人推送；不要盲目关闭分支保护，参阅本指南的替代方式。

## 6. 合并并等待发布

回到 PR，合并到 main。主分支会运行相同工作流，依次完成：

```text
Build and test
Sync generated files
Deploy Pages
```

首次更新时，包内生成文件已经匹配，同步任务可能显示“already current”。以后只编辑内容源时，机器人可能产生一次 `chore: synchronize generated handbook files` 提交，这是正常的同步步骤。它只更新 index.html、README.md、docs/PAPER-MENTOR.zh-CN.md，不修改你的提示词源文件。

GITHUB_TOKEN 的自动推送不会再递归触发同类 push 工作流；当前工作流会继续发布已通过测试的产物。看到机器人提交没有第二次 Pages 运行，并不意味着部署缺失。

全部任务成功后，在 Settings → Pages 查看实际发布地址。若第一次发布发生在你切换 Source 之前而失败，完成设置后到 Actions 打开工作流，选择 `Run workflow`（分支 main）重新运行。

## 7. 验收新版

分别打开这些地址并按 F5 刷新，确认静态详情路由可直达：

```text
英文首页：https://j-i-n-g-l-i.github.io/prompt-folio/en/
中文首页：https://j-i-n-g-l-i.github.io/prompt-folio/zh-CN/
先说重点：https://j-i-n-g-l-i.github.io/prompt-folio/zh-CN/user/direct-first/
论文研读：https://j-i-n-g-l-i.github.io/prompt-folio/zh-CN/project/paper-mentor/
组合示例：https://j-i-n-g-l-i.github.io/prompt-folio/zh-CN/project/paper-mentor/?with=direct-first
```

检查首页品牌为 Prompt Folio，中文条目显示“先说重点”。切换到其他语言后，条目标题、组合开关及复制内容一起改变。正文没有因为名称本地化被改写。

在中文界面搜索 `Paper Mentor`、`文献` 和 `Direct First`；切换语言后旧搜索词应清空。“返回手册目录”应显示全部条目。手机首屏可直接看到实际提示词，“如何使用”在详情页正文之前。

复制单条、复制组合、下载 .md、复制链接后，将正文粘贴到本地记事本检查。旧的 `#prompt=...&lang=...` 链接仍可用，只有 `#lang=zh-CN` 的链接现在进入中文目录。

再点击顶部 GitHub、页脚 README 和仓库 README 的链接，确认目标均为新仓库。实际系统剪贴板、手机触摸、屏幕阅读器和 GitHub 原生 README 折叠效果需要在你自己的设备上验收。

## 8. 更新仓库分享图

`Settings → General → Social preview → Edit → Upload an image`，选择 `assets/social-preview.png`。这是仓库分享图的单独设置；提交图片文件本身不会替换此设置。网页的 Open Graph 图片地址已自动更新。

About 的 Description 和 Website 可继续保留目前的内容。无需再改仓库名。

## 9. 日后编辑

只改名称、正文：编辑 `content/prompts/<id>.json`。网站品牌、服务指南、UI：编辑 `content/library.json`。修改模板：编辑 templates 下文件。成功的 main 工作流会重新构建并同步 README。

直接改生成的 index.html 或 README.md 会在下次同步时被源文件生成的内容覆盖。详情见 MAINTAIN.zh-CN.md。

## 10. 故障定位与回滚

| 现象 | 先检查 |
|---|---|
| 首页变了，详情页刷新 404 | Pages Source 是否是 GitHub Actions，Deploy Pages 是否成功 |
| 页面还是旧版 | 查看本次 main 的运行状态，重新打开 /zh-CN/；必要时无痕窗口 |
| 构建报 repository mismatch | content/library.json 的 site.repository 与 site.url 是否对应本仓库 |
| 同步步骤 403 | Actions 权限、组织策略、main 分支保护 |
| 有新 main 提交，旧同步任务主动退出 | 这是防止覆盖较新提交的保护；查看最新那次运行 |
| 文件上传后不触发工作流 | .github 是否在根目录，文件是否已合并到 main，Actions 是否被禁用 |
| 文本修改没有显示 | 是否改了生成文件，或工作流测试失败尚未发布 |

需要回滚时，在已合并的升级 PR 使用 Revert 创建回滚 PR，并确认生成文件也回到旧版。若回到 v2，再将 Pages Source 恢复为 `Deploy from a branch → main → /(root)`。也可从备份恢复原文件，但保留版本历史通常更清晰。暂时失败的升级发布不会自动抹掉已经部署成功的旧网站。

### 受保护分支的同步替代方式

坚持人工审查时，在本地先运行 `python tools/build.py`，把内容源和三个生成文件一起提交到 PR。此时 Sync generated files 会检测到没有差异，不会推送；可以把同步 job 的 contents 权限改为 read。后续必须继续把生成文件一并提交。若内容源和生成文件不同，该只读方案会阻止发布，避免网站与 README 不一致。

## 11. 同一次提交出现两个发布工作流

`Validate, sync and publish` 是本项目的自定义工作流；`pages build and deployment` 是 GitHub 的 Pages 工作流。这两个名称分别出现，通常表示推送时旧的分支发布仍生效，或旧任务已经在切换发布源之前触发。仅凭运行列表截图，不能确认当前 Pages 设置。

打开 `Settings → Pages → Build and deployment → Source`，选择 **GitHub Actions**，使用仓库现有的 `.github/workflows/publish.yml`。若需要重新发布，在 Actions 中打开 `Validate, sync and publish`，选择 `Run workflow`，分支选 main。之前的运行记录会保留。

本项目需要发布生成的 `_site/`，其中包含语言和条目的真实目录。旧的 `main / (root)` 分支发布只使用仓库根目录，无法发布这些生成目录。

`Sync generated files` 是自定义工作流内的一个任务。官方文档说明，使用 `GITHUB_TOKEN` 推送的提交不会触发新的 Pages 构建，因此不应仅凭两条记录判断发生了机器人递归发布。参见 [Pages 发布源说明](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)。

## 12. 修改网站地址与绑定自定义域名

当前地址的组成是 `https://j-i-n-g-l-i.github.io/prompt-folio/`：域名部分由 GitHub 账号决定，`prompt-folio` 是项目仓库名。Custom domain 用于绑定自己拥有或获授权使用的域名，不是任意修改这两个字段的入口。[GitHub Pages 地址规则](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages)。

如果只想修改 `/prompt-folio/`，需要更改仓库名，再同步 `content/library.json` 的 `site.repository`、`site.url` 以及本地 Git 的 origin 地址，重新构建并推送。仓库名未确定时，保留当前配置。

若拥有 `example.com`，并希望本仓库使用 `https://prompts.example.com/`，按以下步骤配置（example.com 是示例，请替换为自己的域名）：

1. 在 GitHub 的 `Settings → Pages → Custom domain` 填入 `prompts.example.com` 并保存。这里只填写域名。
2. 在域名的 DNS 管理中添加 CNAME：名称为 `prompts`，目标为 `j-i-n-g-l-i.github.io`。目标不带 `https://`，也不带 `/prompt-folio/`。
3. 将 `content/library.json` 中的 `site.url` 改为 `https://prompts.example.com/`，保留末尾斜杠；`site.repository` 仍指向实际 GitHub 仓库。这样 README、canonical、sitemap 和分享元数据才会使用新地址。
4. 运行 `python tools/build.py` 与 `python tools/build.py --check --repository J-I-N-G-L-I/prompt-folio`，提交生成文件和配置并推送。DNS 检查和证书就绪后，在 Pages 中启用 `Enforce HTTPS`。

以 Actions 发布时，自定义域名由 Pages 设置管理，不需要 CNAME 文件。DNS 生效和 HTTPS 选项可用可能需要最多 24 小时。这里的步骤使用子域名；若使用裸域名（如 example.com），需按 [GitHub 官方域名指南](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site) 配置对应的 A 或 ALIAS/ANAME 记录。

## 官方参考（2026-09-08 查阅）

- [GitHub 网页上传文件](https://docs.github.com/en/repositories/working-with-files/managing-files/adding-a-file-to-a-repository)
- [Pages 发布源](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)
- [Pages 自定义 Actions 工作流](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
- [GITHUB_TOKEN 与递归触发](https://docs.github.com/en/actions/concepts/security/github_token)
- [仓库分享预览](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/customizing-your-repositorys-social-media-preview)
