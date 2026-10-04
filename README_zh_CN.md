# Shape Key Helper / 形态键一键镜像大师

Shape Key Helper 是一个 Blender 形态键辅助扩展，用于左右镜像、对称修复，
以及在保留现有形态键的情况下应用修改器。

![Shape Key Helper 形态键对称修复前后对比](media/shape-key-helper-feature-1920x1080.png)

上图展示了单侧被误调的面部形态键沿网格 X 轴完成对称修复；原模型与 UV 保持不变。

## 插件界面

![Shape Key Helper 在 Blender 5.1 中的界面](media/shape-key-helper-zh-cn.png)

## 主要功能

- 自动识别当前形态键的左右命名并镜像到对侧
- 手动选择来源和目标形态键
- 批量处理多个已选网格中的同名形态键
- 不删半边、不改拓扑、不破坏 UV 地修复模型基础对称
- 只修复当前形态键自身对称，或把当前形态键恢复到基础形态
- 应用指定修改器并保留相对或绝对形态键
- 保留形态键名称、顺序、值、静音状态、顶点组、相对键关系、动画 Action 和驱动
- 补齐与修复 ARKit 52 形态键
- 辅助设置 VRM0 默认表情与 Blend Shape Proxy

## 环境要求

1.14.4 已修复保留形态键应用修改器时的多选与编辑锁状态丢失。鼠标拖拽问题尚未复现，不包含在已修复声明中。

- Blender 4.2 LTS 或更高版本
- 已在 Blender 4.2.9、4.3.2、4.4.3、4.5.12 LTS、5.0.1、5.1.2
  与 5.2.2 LTS 完成逐次版本回归验证
- 对称与修改器工具需要网格对象
- 镜像、恢复和当前形态修复需要模型已经存在形态键

## 安装

可以从 [Blender Extensions 官方页面](https://extensions.blender.org/add-ons/shape-key-helper/)
安装 Shape Key Helper，也可以在 Blender 的“获取扩展”中搜索 `Shape Key Helper`。

如需手动安装发布包：

1. 下载发布页中的扩展 ZIP。
2. 打开 Blender 偏好设置 > 获取扩展。
3. 打开右上角菜单，选择“从磁盘安装”。
4. 选择 ZIP，并启用 Shape Key Helper。

## 快速使用

1. 选择网格，打开“对象数据属性 > 形态键”。
2. 在 Blender 原生形态键面板下展开“形态键一键镜像大师”。
3. “镜像形态键”包含自动镜像、手动镜像和批量镜像。
4. “实用功能”包含模型对称修复、当前形态修复、恢复默认和保留形态键应用修改器。

## 修改器安全说明

插件会让基础形态和每个形态键分别经过同一个指定修改器，并临时关闭其他可见
修改器。如果不同形态键得到的顶点数量不一致，操作会在替换原网格前取消。

正式文件在改变拓扑前仍建议备份。当前不重建形态键 NLA 轨道；带 NLA 的模型
请先移除或烘焙对应轨道，再使用修改器功能。

## 隐私与权限

插件不申请网络、文件、剪贴板、摄像头或麦克风权限。

## 维护者与开源方向

- **维护者：** [Feng Ji Shi](https://github.com/qw424886884)
- **相关项目：** [Rig Bridge](https://github.com/qw424886884/rig-bridge)

我是一名以三维制作为业的自由职业者，不是职业软件工程师。过去学过一些代码，
也一直想把日常制作中遇到的问题做成工具。经过数月高强度使用 Codex，我把这些
实践经验转化成了 Rig Bridge 和 Shape Key Helper 两款开源 Blender 扩展。

Codex 帮助我把三维经验落实为代码；测试、审核和发布仍由我负责。
我希望继续维护这两款工具，并把经过实际验证的 Blender 工作方法分享给其他创作者。

### 公开发布状态｜2026 年 9 月 16 日

- 上述日期的公开版本：**1.14.3**
- [Blender Extensions](https://extensions.blender.org/add-ons/shape-key-helper/) 累计下载：**544 次**
- [GitHub](https://github.com/qw424886884/shape-key-helper/releases) 公开发布：**3 个版本**

下载数据是上述日期读取的累计次数，不代表月下载量、独立用户数或活跃用户数。
最新数字请查看所链接的平台页面。

## 许可证

Shape Key Helper 使用 GNU GPL v3.0 或更高版本许可证，详见 [LICENSE](LICENSE)。
