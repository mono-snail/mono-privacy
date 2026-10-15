# MonoProxy iOS 官网

这是 iOS App 内指向的独立站点源码，域名为 `https://proxy.monoware.app/`。

- 仓库：`git@github.com:mono-snail/mono-privacy.git`
- 当前工作分支：`main`；旧发布记录也使用此分支
- 站点入口：仓库根目录 `index.html`，纯静态页面，无构建依赖。
- `CNAME` 保持 `proxy.monoware.app`，不得按父目录旧文档改成 `monoware.app`。
- `../MonoProxyServer/MonoProxyWebsite/` 是 Mac Companion 站点，不能用来替换此站。

## 本地检查与预览

```sh
python3 scripts/check.py
git diff --check
python3 -m http.server 4196 --bind 127.0.0.1
```

打开 `http://127.0.0.1:4196/?lang=zh`。支持英文、简体中文、繁体中文、日文和韩文。原生截图随语言选择切换中英文；日文和韩文说明使用英文 App 截图。截图可点击或用键盘打开，Escape 关闭；手机导航可展开。

## 更新内容与素材

主页保留原有蓝色视觉、皮肤展示、App Store 产品页链接、隐私与支持入口。新增设备详情、会话分析、诊断和单手长按停止介绍，以及 iPhone 服务与 Mac Companion 客户端的三步连接说明。Mac 接入指南提供 Companion 和手动配置两条路径。公开 Mac 安装地址尚未配置，因此当前说明安装包正在准备，不使用占位 App Store ID。

`images/ios/` 为 2026-10-15 的 18 张 iOS 实拍及 2 张 Mac 原生示例图的 WebP 版本，共约 1.3 MiB。`manifest.json` 记录来源、原始截图及发布素材的 SHA-256、尺寸与文件大小。iOS 图片来自新版 Release App / iPhone 17 Pro / iOS 27 模拟器，使用本地测试 HTTP、CONNECT、SOCKS5 会话；不代表实际网速或后台耐久性测试。Mac 图片使用隔离示例数据，不表示与截图中的模拟器建立了真实连接。主页明确标注新版预览，未把它写成 App Store 已发布版本。

从 App 工程的 `MonoProxyWebsiteCapture` scheme 复拍后，导入截图（工具需要 Pillow）：

```sh
python3 scripts/import_ios_captures.py /absolute/path/Capture.xcresult \
  --mac-captures /absolute/path/native-mac-captures
```

Mac 素材目录需包含 `ios-mac-overview-en.png` 和 `ios-mac-overview-zh.png`。网站运行不依赖 App 工程或这些导入工具。

## 提交与上线

在**本仓库**审阅并提交网站改动，再推送 `main`：

```sh
python3 scripts/check.py
git diff --check
git add index.html guide-macos.html homepage.css homepage.js images/ios scripts README.md sitemap.xml
git commit -m "feat: refresh iOS homepage with native previews and Mac setup"
git push origin main
```

上级旧文档记载此仓库由 GitHub Pages 从 `main` 的根目录发布；另一本通用手册介绍 Cloudflare Pages，不能将其他产品的 Pages 项目配置直接套用。正式上线前，需核对当前站点的实际托管配置，等待对应提交的生产部署成功，再访问自定义域名验证页面、图片和指南。Git push 成功不等于部署完成。

本轮环境检查中，读取 GitHub SSH 远端返回 `Permission denied (publickey)`，未推送或部署，也未能读取生产部署记录。需要先恢复此设备对该仓库的 GitHub 认证。不得把 SSH 私钥、访问令牌或 Cloudflare 配置加入仓库。
