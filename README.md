# 📚 文献监控工具

自动监控 PubMed 数据库中的最新英文文献，按研究方向分类，每天推送微信通知。

## ✨ 功能特点

- **自动抓取**: 每天自动从 PubMed 检索最新文献
- **智能分类**: 按三个研究方向自动分类
- **微信推送**: 通过 Server酱 推送到个人微信
- **在线报告**: 生成 HTML 报告，任何设备浏览器查看
- **零成本**: 使用 GitHub Actions 免费运行，无需服务器

## 📋 监控的研究方向

1. **生物活性天然产物的发现与结构鉴定**
   - 微生物来源活性天然产物
   - 放线菌/链霉菌
   - 结构鉴定

2. **天然产物的生物合成与合成生物学**
   - 生物合成基因簇
   - 非核糖体肽、聚酮、甾体等
   - 合成生物学方法

3. **酶催化反应的机理和应用**
   - 酶催化机理
   - 选择性催化
   - 药物中间体应用

## 🚀 快速开始（5分钟完成）

### 第一步：创建 GitHub 账号

1. 访问 https://github.com
2. 点击 "Sign up" 注册
3. 按提示完成注册流程

### 第二步：创建仓库

1. 登录 GitHub 后，点击右上角 "+" → "New repository"
2. 填写信息：
   - **Repository name**: `literature-monitor`（或其他名称）
   - **Description**: `文献监控工具`
   - **Public**（公开）或 **Private**（私有）都可以
   - ✅ 勾选 "Add a README file"
3. 点击 "Create repository"

### 第三步：上传项目文件

**方法 A：网页上传（推荐新手）**

1. 在仓库页面，点击 "Add file" → "Upload files"
2. 将本项目的所有文件拖拽上传
3. 点击 "Commit changes"

**方法 B：Git 命令行（适合有经验的用户）**

```bash
git clone https://github.com/你的用户名/literature-monitor.git
cd literature-monitor
# 复制项目文件到这个目录
git add .
git commit -m "Initial commit"
git push
```

### 第四步：配置微信推送

1. **获取 Server酱 SendKey**：
   - 访问 https://sct.ftqq.com
   - 用微信扫码登录
   - 点击 "SendKey" 复制你的密钥（格式如 `SCTxxxxxx`）

2. **添加 GitHub Secret**：
   - 回到 GitHub 仓库页面
   - 点击 "Settings" → "Secrets and variables" → "Actions"
   - 点击 "New repository secret"
   - Name: `SERVERCHAN_SENDKEY`
   - Value: 粘贴你的 SendKey
   - 点击 "Add secret"

### 第五步：启用 GitHub Actions

1. 在仓库页面，点击 "Actions" 标签
2. 如果是第一次使用，点击 "I understand my workflows, go ahead and enable them"
3. 点击左侧的 "每日文献监控"
4. 点击 "Run workflow" → "Run workflow" 手动测试一次

### 第六步：查看结果

- **HTML 报告**: 仓库中的 `reports/` 文件夹，点击 `latest.html` 查看
- **微信通知**: 检查微信是否收到推送消息

## ⚙️ 自定义配置

编辑 `config.json` 文件：

### 修改期刊列表

在 `"journals"` 数组中添加或删除期刊名称：

```json
"journals": [
  "Journal of the American Chemical Society",
  "Nature",
  // 添加新期刊...
  "你的期刊名称"
]
```

### 修改关键词

在 `"keyword_categories"` 中修改各方向的关键词：

```json
"direction_1_natural_product_discovery": {
  "label": "生物活性天然产物的发现与结构鉴定",
  "keywords": [
    "natural product",
    "你的关键词"
  ]
}
```

### 修改抓取频率

编辑 `.github/workflows/daily_fetch.yml`：

```yaml
schedule:
  # 每天北京时间 16:00 运行（UTC 8:00）
  - cron: '0 8 * * *'
```

修改 `0 8` 可以改变运行时间（UTC 时间，北京时间 = UTC + 8）。

## 📱 接收微信通知

### Server酱 使用说明

- **免费版**: 每天 5 条消息，足够使用
- **推送限制**: 单条消息最大 30KB
- **消息格式**: Markdown 格式，支持链接和加粗

### 推送内容

每天推送包含：
- 文献总数统计
- 各研究方向的新文献列表（最多显示 5 篇/方向）
- 文献标题、期刊、日期、DOI 链接
- 完整报告链接

## 🔍 本地运行（可选）

如果想在本地电脑运行测试：

```bash
# 安装依赖
pip install -r requirements.txt

# 运行脚本
python fetch_papers.py
```

## 💡 常见问题

### Q: GitHub Actions 免费吗？

A: 是的。GitHub 免费账户每月有 2000 分钟 Actions 时间。本工具每次运行约 1 分钟，完全够用。

### Q: 换电脑能看报告吗？

A: 可以。报告存储在 GitHub 仓库，任何设备登录 GitHub 即可查看。

### Q: 电脑需要一直开着吗？

A: 不需要。GitHub Actions 在云端运行，你的电脑关机也不影响。

### Q: 如何查看历史报告？

A: 在 GitHub 仓库的 `reports/` 文件夹中，所有历史报告都按日期保存。

### Q: 没有收到微信推送？

A: 检查以下几点：
1. Server酱 SendKey 是否正确配置到 GitHub Secrets
2. GitHub Actions 是否成功运行（查看 Actions 页面日志）
3. Server酱 网站是否显示推送成功

### Q: 如何修改推送时间？

A: 编辑 `.github/workflows/daily_fetch.yml` 中的 `cron` 表达式。注意 GitHub 使用 UTC 时间，北京时间 = UTC + 8。

## 📊 技术架构

```
GitHub Actions (定时任务)
    ↓
PubMed E-utilities API (文献检索)
    ↓
Python 脚本 (数据处理 + 分类)
    ↓
  ├─→ HTML 报告 (保存到仓库)
  └─→ Server酱 API (微信推送)
```

## 🛠️ 技术栈

- **Python 3.11**: 主程序语言
- **PubMed E-utilities**: 文献数据源
- **GitHub Actions**: 定时任务执行
- **Server酱**: 微信推送服务
- **requests**: HTTP 请求库

## 📝 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📧 支持

如有问题，请提交 Issue 或联系开发者。
