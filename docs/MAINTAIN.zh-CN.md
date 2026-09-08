# 维护与扩展

## 一个内容源，两个阅读入口

`content/library.json` 保存所有完整提示词、界面译文、分类信息、条目版本、官方设置链接与翻译说明。`templates/index.html` 和 `templates/app.js` 定义界面与交互；`tools/build.py` 将内容编译为自包含的 `index.html` 和完整 `README.md`。

部署不需要构建环境。只有编辑源文件后，才需要在本地运行 Python 3.10 或更新版本的生成脚本；该脚本只使用 Python 标准库。

```bash
python tools/build.py
python tools/build.py --check
```

第二条命令只校验，遇到生成文件过期或必需译文缺失时返回非零退出码。不要分别手改生成后的 HTML 和 README，它们会在下次生成时被覆盖。

## 内容结构

```text
site
  title / repository / url / version / checked
levels
  user / project
locales
  en / zh-CN / zh-TW / es / fr / de / pt-BR / it
  ja / ko / ar / hi / ru / id / tr / az
prompts
  direct-first
    id / level / icon / version / locales
  paper-mentor
    id / level / icon / version / locales
guides
  user / project
```

每条提示词的每种语言都有 `title`、`description`、`body`。项目提示词还可以提供 `starter` 和 `starterTitle`，用于显示可复制的起始提问示例。`body` 是纯文本，使用 `\n` 表示换行；无需加入外层代码框。

`level` 当前使用 `user` 或 `project`。这些值定义浏览分类，和模型 API 的 `system`、`developer`、`user` 角色没有映射关系。

## 修改现有提示词

在 `prompts` 数组中按 `id` 找到条目，修改 `locales[语言代码].body`。涉及语义变更时同步检查其他译文，调整条目 `version` 并记录变更，再生成文件。界面、复制、下载和 README 将读取同一版本。

Direct First 的当前内容保留了用户最后确认的版本。不要把旧版英文示例重新添加到中文正文。项目组合器引用该条目的完整正文，不维护另一份副本。

## 新增一条提示词

在 `prompts` 中添加一个对象，使用新的小写连字符 ID，如 `code-review`。设置 `level`、现有或新图标名、版本号，并提供全部 16 个语言版本。下面展示字段形状；只填两种语言不能通过当前校验。

```json
{
  "id": "code-review",
  "level": "project",
  "icon": "project",
  "version": "1.0.0",
  "locales": {
    "en": {
      "title": "Code Review",
      "description": "A focused code-review workflow.",
      "body": "Your complete, reviewed prompt goes here."
    },
    "zh-CN": {
      "title": "代码审查",
      "description": "围绕代码质量的专用审查流程。",
      "body": "在这里填写完整、经过检查的提示词。"
    }
  }
}
```

生成后，分类条目、计数、搜索、详情链接和 README 中的全文会自动更新。新建项目条目也会提供可选的 Direct First 组合复制；未设置 `starter` 时不显示起始提问卡片。

保留 `direct-first` ID：它被组合功能和历史链接使用。`paper-mentor` 目前还用于生成独立的中文文案文档，删除或改名需要同步修改 `tools/build.py`。当前测试脚本含两条初始条目的回归断言；新增条目时需要更新这些断言及对应计数，测试不会自动把新条目视为已验证。

## 分类和图标

目前只支持用户级与项目级，不需要提前增加第三类。图标放在 `assets/icons/`，文件名和条目 `icon` 一致；生成器会将 SVG 嵌入页面，运行时无需请求独立图标文件。保持 64×64 viewBox，与现有圆角、笔画宽度和配色一致。

图标与代码属于受信任的维护源。站点没有用户提交或远程上传入口；新增 SVG 前仍应移除脚本、外部资源和无关元数据。

修改 favicon 时需要重新导出 `.ico` 和 Apple PNG，并更新 HTML 模板中的图标版本参数；`build.py` 不自动生成位图。网页分享图在 `assets/social-preview.png`；图标说明图在 `docs/icon-system.png`。它们是独立设计资产，变更品牌时也应同步检查。

## 修改站点地址或品牌

Fork 后修改 `site.repository` 与 `site.url`，后者必须以 `/` 结束，然后运行生成脚本。HTML 中的分享元数据、README 的完整链接与离线分享链接会同步更新；实际 HTTP(S) 页面上的分享功能采用当前部署地址。

`site.title` 控制主品牌文字。副标题、英文描述、分享图片以及文档中的项目介绍仍属于编辑内容，改名时需要一并检查；当前无需给原仓库改名。

## 更新平台设置指南

`guides` 保存官方链接及英文菜单路径；每个语言的 `userRoutes` / `projectRoutes` 保存对应说明，两者顺序需要一致。核查官方文档后再更改说明和 `checked` 日期，避免把实际未核查的路径标成“已验证”。

界面、套餐和帐号类型可能影响入口。保持“找不到持久设置时在当前对话开头粘贴”的通用方法；不承诺自动继承或无条件服从。

## 可选浏览器回归测试

运行测试需要另行安装 Playwright 和 Chromium。生成网站本身不依赖它们。

```bash
python -m pip install playwright
python -m playwright install chromium
python tools/test_browser.py --report test-report.json
```

已有 Chromium 时可指定 `--browser /path/to/chromium`。快速开发检查可使用 `--locales en,zh-CN,ar`；该选项仅筛选常规界面循环，其余回归检查仍执行。

测试将 HTML 放进内存中的浏览器文档。剪贴板及语言存储接口使用模拟适配器，不代表实际操作系统或全部浏览器已经验证。见 [测试范围](TESTING.md)。

## 发布检查

生成校验通过后，核对中英文内容及所有修改译文，确认官方来源、许可证和旧链接保持有效。再提交源文件与生成文件。实际 Pages 更新后，复查图标、剪贴板、下载与手机布局。
