# 面板 UI、CSS 与 portal 隔离

> scope：插件 frontend-panel 和复用此页的嵌入 UI。owner：UI/宿主集成维护者。status：规范；PLG-STAB-003 revision 1 的 UI 分支。applies_when：布局、样式、焦点、portal 或交互变化。related：[宿主兼容](host-compat.md)、[生命周期](lifecycle.md)、[验证](verify.md)。

先读实际组件契约和宿主布局/主题/挂载点。样式采用可证明的隔离边界；全局 reset、通配符和不受控 portal 不得污染宿主/邻插件。记录层叠上下文、滚动所有者、定位锚点和 theme/token 来源；不能只在空白独立页调正确。

portal 挂载/卸载归属明确，覆盖失效锚点、窗口缩放、窄视口、遮挡、主题切换与多面板；焦点可进入/返回，键盘可关闭/操作，ARIA/读屏语义及系统导航符合项目契约。避免两个同语义容器形成双滚动，布局不得依赖无约束固定宽度。

真实宿主页复现修改前问题并复验修改后行为，记录操作、目标版本/页面、视口/缩放与截图/录像；对照宿主和相邻面板未改变，卸载后无 style/portal/listener 残留。只截图无法证明权限、取消或完整可访问性，需相应行为断言。
