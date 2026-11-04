# 阿Bu · 浏览器悬浮球插件

Chrome / Edge 扩展：在任意网页右下角显示悬浮球，点开后分支连到主要功能，并跳转到阿Bu Streamlit 网页。

## 安装

1. 打开 `chrome://extensions`（Edge：`edge://extensions`）
2. 打开「开发者模式」
3. 「加载已解压的扩展程序」→ 选本文件夹 `extension/`
4. 详细信息 → 网站访问权限 →「在所有网站上」
5. 改代码后点「重新加载」，再刷新目标网页；或点扩展弹窗「在当前页强制显示悬浮球」
6. 登录态：先在阿Bu 页登录（URL 含 `auth=`），扩展会缓存 token，点悬浮球跳转时带上，避免重登
7. （可选）扩展选项 / 弹窗 → 语言；阿Bu 地址默认长链
   `https://bubu-hkbu-mdic9zba2hqxaqskyfihkn.streamlit.app`（短链冷启动易卡在加载圈）

## 语言

- 弹窗、设置页可切换：简体 / 繁體 / English
- 展开悬浮球后点「语言」分支循环切换（不再使用侧边残缺芯片）
- 跳转阿Bu 时自动带 `lang=`
- **不会**在 `*.streamlit.app` 上注入悬浮球，避免与 Cloud 页面抢 JS 缓存
