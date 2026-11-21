# 1.0.0 源码包发布清单

只有主会话明确确认全部分工完成后才运行 `python qa/package.py --build`。默认 `python qa/package.py` 仅输出待打包文件及逐文件 SHA-256，不创建 release。

固定版本 1.0.0，固定 ZIP 时间戳及权限，文件名排序、ZIP_STORED、无当前时间字段；相同输入 bytes 得到相同 ZIP bytes。构建后解包读取每项重算哈希并检查 ZIP 完整性。release 内提供源码 zip、逐文件 SHA256SUMS 与 archive 自身 sha256 sidecar。

包含正式指南／契约／schema／工具／测试／模板／模拟样例／平台 profile、明确列出的最终 QA 脚本和报告。排除 release 自身、git 元数据、Python cache、临时 stdout 与历史中间 QA 报告。旧设计草稿保留在 drafts，仅为历史材料：正式使用从 [README](../README.md) 及 [START-HERE](../docs/START-HERE.md) 开始，不能把草稿当当前字段权威。

验收数据是本包离线工具测试，不是产品真实执行／远端 CI 强制的证明。实际覆盖、skip 及失败修复过程见 [验收报告](REPORT.md) 和独立 [安全审查](SECURITY-REVIEW.md)。版本号表示可交付源码，不表示已安装到任何外部环境。
