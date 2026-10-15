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

首屏直接说明 iPhone 代理服务器的用途、同一局域网的接入条件，并突出共用端口、多协议、设备与流量可见、一次购买无订阅和无需注册。Mac 区域先展示六组痛点与解决方式：手填地址与自动发现、反复代理认证与钥匙串凭据复用、不遵循系统代理的应用与透明模式、连接失败难定位与连接记录及诊断、可用性需要手动确认与自动链路检测、失效后重选代理与自动故障切换。顶部独立突出自动扫描、可用性检测和自动故障切换。可用性检查覆盖连接前验证与已连接链路监测；连接失败时尝试符合条件的同模式备用配置，兼容模式支持运行中故障切换，透明模式运行中异常则先阻止代理流量并重试当前上游。连接步骤与认证说明保留在可展开引导中。以上内容同步五种语言；没有承诺自动发现始终成功、所有应用均可代理，或消除网站登录与 macOS 权限提示。

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

## 2.9.3 更新说明的对比依据

以 iOS 发布源码 `54a36159ade5957b9cbde107f760d50a73f8b9d7`（2.8.3 / build 16）对比当前 2.9.3 / build 23。该历史提交的工程版本与旧发布文档相符，原本没有同名本地 tag，本轮在 App 仓库补齐。完整变更证据和验证结果保存在 App 仓库的 `mono_docs/APP_STORE_RELEASE_2.9.3.md`、`docs/ios-release-2.9.3-comparison.json`。官网更新区介绍新增/增强的设备管理、会话分析、诊断、配置库和运行恢复，不把旧版本已经具备的长按停止、皮肤或基础诊断写成新增。

结构化数据中的已发布版本同步为用户确认的 2.8.3；更新区单独标注 2.9.3 预览，不表示新版本已经上架。
