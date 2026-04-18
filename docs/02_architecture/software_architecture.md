# 项目0软件架构设计

---

## 1. 文档定位

本文档在《项目0系统总架构设计》和《项目0计算与通信架构》之下，进一步回答以下问题：

1. **ROS2 软件系统如何组织**
2. **各功能应划分为哪些软件包**
3. **各包之间通过哪些话题 / 服务 / 动作接口交互**
4. **主链路与辅助链路在软件层面如何贯通**
5. **数据流、控制流、状态流如何在软件系统中展开**

本文档属于**软件架构**，因此：

### 1.1 本文档纳入的内容
- ROS2 workspace 总体结构
- 软件包划分
- 包职责边界
- 话题 / 服务 / 动作接口定义
- 数据流、控制流、状态流设计
- 启动组织与模式化运行的软件层关系
- 迭代一到迭代二的软件架构演进边界

### 1.2 本文档不纳入的内容
- 不定义具体源代码实现
- 不定义具体算法内部细节
- 不定义具体参数取值
- 不定义物理接线
- 不定义电源供电方式
- 不定义具体协议字段字节布局
- 不定义模块内部类设计与文件级实现
- 不定义测试用例与验收流程

因此，本文档的角色是：  
**把系统总架构与计算通信架构，进一步落到 ROS2 软件组织、接口关系和运行链路层面。** :contentReference[oaicite:0]{index=0} :contentReference[oaicite:1]{index=1}

---

## 2. 架构输入与前提

本软件架构建立在以下已确定前提之上：

- 项目0采用“执行层—感知层—空间认知层—行动规划层—任务决策层”的五层主链路，以及安全、系统管理、数据记录三条辅助链路。软件架构必须承接这一骨架，而不能重新定义系统分层。:contentReference[oaicite:2]{index=2}
- 项目0采用“Orin NX 为唯一主计算与主控平台、STM32F407 为唯一底层执行控制平台”的主从式计算与通信架构。ROS2 主业务统一运行在 Orin NX，STM32 不运行 ROS2 主业务。:contentReference[oaicite:3]{index=3}
- 传感器接入为：Mid360 与 D435 均接入 Orin NX；编码器和电机控制接入 STM32。:contentReference[oaicite:4]{index=4} :contentReference[oaicite:5]{index=5}
- 当前已锁定：**迭代一阶段的 IMU 正式主路径为 Mid360 内置 IMU，经 Livox 驱动在 Orin NX 上直接发布。** 因此软件架构中，SLAM 正式 IMU 输入来自 Mid360 驱动链路；STM32 上传 IMU 的路径不作为迭代一正式主接口，仅保留为后续兼容扩展说明。
- 迭代一目标是做成最小闭环正式成立的平台；迭代二是在此基础上增强，而非推翻。软件架构必须从一开始就保证可扩展，但不能为了未来扩展把当前结构做得过重。:contentReference[oaicite:6]{index=6} :contentReference[oaicite:7]{index=7}

---

## 3. 软件架构总原则

### 3.1 单一主工作空间
项目0在 Orin NX 上采用**单一主 ROS2 workspace** 承载全部主业务软件。  
其目的是：
- 降低单人开发复杂度
- 保持依赖关系清晰
- 统一构建、部署和版本管理
- 便于后续阶段持续迭代

### 3.2 按系统职责分包，而不是按代码实现技巧分包
软件包划分优先服从：
- 系统总架构边界
- 计算与通信架构边界
- 调试与联调边界
- 未来迭代增强边界

而不是为了代码复用过早做过细拆分。

### 3.3 接口显式化
各软件包之间的主交互必须通过明确的：
- 话题
- 服务
- 动作  
来组织，而不是依赖隐式耦合。

### 3.4 业务链路与辅助链路分离
主链路包与安全/管理/记录类包在逻辑上分离，避免：
- 导航逻辑和安全逻辑耦死
- 任务逻辑和系统管理逻辑混杂
- 数据记录代码侵入业务主干

### 3.5 迭代一先落地，迭代二可扩展
软件架构在迭代一阶段必须：
- 先能跑通主链路
- 先把安全、管理、记录骨架搭起来  
在此基础上，再允许迭代二在包内增强或少量增包，而不推翻整体组织。:contentReference[oaicite:8]{index=8}

---

## 4. ROS2 workspace 结构

项目0推荐采用以下 ROS2 workspace 结构：

```text
project0_ws/
├── src/
│   ├── p0_interfaces/
│   ├── p0_bringup/
│   ├── p0_sensor_drivers/
│   ├── p0_base_bridge/
│   ├── p0_localization/
│   ├── p0_mapping/
│   ├── p0_map_manager/
│   ├── p0_navigation/
│   ├── p0_semantic_nav/
│   ├── p0_task_manager/
│   ├── p0_safety_manager/
│   ├── p0_system_manager/
│   ├── p0_data_tools/
│   ├── third_party/
│   │   ├── livox_ros_driver2/
│   │   ├── realsense2_camera/
│   │   ├── fast_lio2_ros2/
│   │   ├── nav2_related/
│   │   └── behaviortree_cpp_related/
│   └── stm32_firmware_docs/   （文档/协议说明，不参与ROS2构建）
├── config/
│   ├── sensors/
│   ├── base/
│   ├── localization/
│   ├── navigation/
│   ├── semantic/
│   ├── safety/
│   ├── system/
│   └── modes/
├── maps/
├── launch/
├── scripts/
├── bags/
├── logs/
├── docs/
└── README.md
````

---

## 5. workspace 分层说明

### 5.1 src

放置所有 ROS2 软件包与第三方依赖源码。

### 5.2 config

统一存放 YAML 等配置文件，按功能域分目录管理，避免配置散落到各包内部。

### 5.3 maps

存放地图文件、地图版本和语义位置表等地图相关静态资源。

### 5.4 launch

存放按模式组织的启动入口，如：

* 建图模式
* 定位运行模式
* 自主任务模式
* 调试模式

### 5.5 scripts

存放非核心业务脚本，如一键启动、日志整理、bag 管理、地图保存辅助脚本等。

### 5.6 bags / logs

分别存放运行数据包和日志，支撑复盘与实验记录。
这与项目0强调的数据记录与复盘能力一致。

### 5.7 docs

存放协议说明、部署说明、模式说明、接口表、版本说明等文档，与项目总文件夹长期共存。

---

## 6. 软件包划分总览

项目0软件包建议划分为以下 12 个核心包 + 若干第三方包。

| 包名                | 类型       | 角色定位                     |
| ----------------- | -------- | ------------------------ |
| p0_interfaces     | 自定义接口包   | 统一定义项目内部消息、服务、动作         |
| p0_bringup        | 启动组织包    | 统一管理 launch 入口与模式化启动     |
| p0_sensor_drivers | 感知接入整合包  | 组织传感器驱动接入与感知状态监测         |
| p0_base_bridge    | 底盘桥接包    | 管理 Orin NX ↔ STM32 的软件桥接 |
| p0_localization   | 定位包      | 提供定位链路和定位状态输出            |
| p0_mapping        | 建图包      | 提供建图链路                   |
| p0_map_manager    | 地图管理包    | 地图保存、加载、运行地图管理、语义位置表管理   |
| p0_navigation     | 导航包      | 目标管理、导航调度、路径执行、导航异常处理    |
| p0_semantic_nav   | 语义导航包    | 语义目标解析与导航目标转换            |
| p0_task_manager   | 任务管理包    | 任务生命周期与模式协调              |
| p0_safety_manager | 安全管理包    | 安全监测、软件急停、风险约束、保护处置      |
| p0_system_manager | 系统管理包    | 启停、自检、状态管理、配置管理、运行监控     |
| p0_data_tools     | 数据记录与复盘包 | 记录组织、事件记录、回放辅助、复盘支撑      |

第三方包主要包括：

* livox_ros_driver2
* realsense2_camera
* FAST-LIO2 ROS2 版本
* Nav2 相关包
* BehaviorTree.CPP 相关依赖

所有第三方包通过 Git submodule 引入或在 docs/dependencies.md 中记录使用的 commit hash / release tag。后续升级需显式评估兼容性后进行。
---

## 7. 各软件包职责定义

---

## 7.1 p0_interfaces

### 7.1.1 作用

统一定义项目0内部的自定义：

* msg
* srv
* action

### 7.1.2 设计原则

* 凡是跨包通用、且标准消息无法直接表达的结构，放入本包
* 凡是可能在多包间共享的任务状态、安全状态、系统状态、语义目标结构，统一在此定义
* 避免各包私自定义重复数据结构

### 7.1.3 典型接口类型

* BaseState
* SystemState
* SafetyState
* SemanticGoal
* TaskState
* SemanticNav.action
* SystemMode.srv
* SaveMap.srv
* LoadMap.srv

---

## p0_interfaces 初始接口清单（骨架版，后续迭代增补）

### Messages
- ChassisCmd.msg          # 上位机→底盘：速度指令
- ChassisStatus.msg       # 底盘→上位机：底盘状态（通信状态、编码器、电压等）
- SystemStatus.msg        # 系统管理：当前模式、各模块在线状态
- SafetyEvent.msg         # 安全管理：安全事件类型、等级、时间戳
- LocalizationStatus.msg  # 定位模块：定位质量等级（Good/Degraded/Lost）

### Services
- GetSemanticPose.srv     # 查询语义位置 → geometry_msgs/PoseStamped
- SetSystemMode.srv       # 请求切换系统模式
- TriggerEmergencyStop.srv # 触发/解除急停

### Actions
- NavigateToSemantic.action # 语义导航任务（目标名称 → 导航执行 → 结果反馈）

---

## 7.2 p0_bringup

### 7.2.1 作用

统一管理系统启动入口，不承载业务逻辑。

### 7.2.2 主要内容

* 建图模式 launch
* 定位运行模式 launch
* 自主任务模式 launch
* 调试模式 launch
* 仅底盘调试模式 launch
* 仅感知调试模式 launch

### 7.2.3 边界

* 不实现业务节点
* 只负责任务式、模式式启动组织

---

## 7.3 p0_sensor_drivers

### 7.3.1 作用

作为感知接入整合包，对第三方驱动和项目内部感知状态管理做统一组织。

### 7.3.2 主要职责

* 启动 Mid360 驱动
* 启动 D435 驱动
* 感知状态监测
* 感知在线状态汇总
* 感知健康状态发布

### 7.3.3 边界

* 不负责 SLAM 算法
* 不负责导航
* 不负责任务调度
* 只负责感知接入和感知侧基础管理

> 说明：Mid360 内置 IMU 在软件架构中作为正式主路径直接归属于该包组织的驱动链路。D435 在迭代一中只流向记录和可视化相关链路，不作为定位正式输入。

---

## 7.4 p0_base_bridge

### 7.4.1 作用

把 STM32 抽象为 ROS2 世界中的标准底盘接口。

### 7.4.2 主要职责

* 串口通信管理
* 控制指令下发
* 底盘状态接收
* 底盘状态解析
* 里程计相关基础量输出
* 底层异常状态输出
* 协议帧约定:协议帧头中预留 1 字节版本号字段（初始值 0x01）。p0_base_bridge 节点启动时，通过握手帧与 STM32 进行版本校验。若版本不匹配，节点拒绝进入自主模式，发布告警至 /system/diagnostics，并在 system_manager 中显示提示。
### 7.4.3 边界

* 不负责导航决策
* 不负责任务管理
* 不负责底层 PID
* 不负责直接控制硬件驱动板
  这些都在 STM32 固件侧。

---

## 7.5 p0_localization

### 7.5.1 作用

承载定位功能。

### 7.5.2 主要职责

* 运行定位模式
* 输出位姿状态
* 输出定位健康状态
* 支撑重定位
* 与地图管理协同加载运行地图
* p0_localization 负责发布 /localization/status 话题（类型 LocalizationStatus.msg），包含定位质量等级（Good/Degraded/Lost）。判定逻辑基于 FAST-LIO2 内部状态（如协方差、匹配点数等），由 localization 内部完成。

### 7.5.3 输入

* Mid360 点云
* Mid360 IMU
* 底盘桥接提供的里程相关基础反馈（迭代一为辅助输入/独立状态，正式融合增强主要在迭代二）

### 7.5.4 边界

* 不负责建图保存
* 不负责地图版本管理
* 不负责导航调度

---

## 7.6 p0_mapping

### 7.6.1 作用

承载建图功能。

### 7.6.2 主要职责

* 运行建图模式
* 输出建图状态
* 输出实时建图结果
* 与地图管理包协同触发地图保存

### 7.6.3 边界

* 不负责地图文件管理
* 不负责定位运行
* 不负责导航

---

## 7.7 p0_map_manager

### 7.7.1 作用

统一管理地图与语义位置表等静态空间资源。

### 7.7.2 主要职责

* 地图保存
* 地图加载
* 地图版本区分
* 当前运行地图状态维护
* 语义位置表加载
* 语义位置查询服务
* p0_map_manager 是语义位置表（semantic_locations.yaml）的唯一数据持有者与持久化管理者，负责语义位置表的加载、保存、增删改查。对外通过 service 接口（如 GetSemanticPose.srv、SetSemanticPose.srv）提供访问。

### 7.7.3 边界

* 不负责 SLAM 算法
* 不负责导航执行
* 不负责语义解析本身
  只负责“空间静态资源管理”。

---

## 7.8 p0_navigation

### 7.8.1 作用

承载行动规划层的软件实现组织。

### 7.8.2 主要职责

* 导航目标管理
* 调用 Nav2 行动链路
* 监控导航状态
* 输出导航结果
* 导航异常处理
* 与底盘桥接包联动输出底盘控制意图

### 7.8.3 边界

* 不负责语义目标解析
* 不负责任务生命周期
* 不负责安全仲裁
* 不直接管理地图文件

---

## 7.9 p0_semantic_nav

### 7.9.1 作用

承载语义导航成立所需的上层转换逻辑。

### 7.9.2 主要职责

* 接收语义输入
* 调用语义位置表查询
* 将语义目标转换为导航目标
* 输出转换结果与失败原因
* p0_semantic_nav 通过调用 p0_map_manager 提供的 service 接口查询语义位置，自身不直接读写语义位置表文件。

### 7.9.3 边界

* 不负责具体导航执行
* 不负责任务总调度
* 不负责地图存取实现

---

## 7.10 p0_task_manager

### 7.10.1 作用

组织任务生命周期和模式协调。

### 7.10.2 主要职责

* 任务接收
* 任务状态流转
* 导航任务提交
* 导航结果接收
* 任务成功 / 失败 / 中止处理
* 手动 / 自主 / 建图 / 急停模式协调
* p0_task_manager 可向 p0_system_manager 发送模式切换请求（如请求进入语义任务模式），但自身不持有模式状态的仲裁权。

### 7.10.3 边界

* 不负责路径规划
* 不负责传感器驱动
* 不负责底盘桥接
* 不直接做安全检测，只响应安全结果

---

## 7.11 p0_safety_manager

### 7.11.1 作用

承载软件层安全保障链路。

### 7.11.2 主要职责

* 感知异常监测
* 定位异常监测
* 导航异常监测
* 底盘状态异常监测
* 风险区域约束状态接入
* 软件急停触发
* 停车/中止/保护模式切换请求
* p0_safety_manager 订阅 /localization/status，对 Degraded 发出系统警告，对 Lost 触发停车保护。safety_manager 不自行判定定位质量，只对 localization 发布的质量等级做处置决策。

### 7.11.3 边界

* 不直接代替 STM32 的底层保护
* 不直接生成导航路径
* 不负责系统启动组织

> 硬件急停为纯硬件链路，不属于 ROS2 软件链路；软件架构只承接“软件急停”和“安全监测后下发停车意图”的部分。

### 7.11.4 特殊权限

* p0_safety_manager 在检测到安全事件时，可通过 p0_system_manager 的急停接口强制切换至急停模式。此路径具有最高优先级，system_manager 必须无条件执行。

---

## 7.12 p0_system_manager

### 7.12.1 作用

承载系统管理链路。

### 7.12.2 主要职责

* 模式管理状态汇总
* 启停流程协调
* 自检
* 系统状态聚合
* 关键模块在线状态汇总
* 运行准入判断
* 运行监控输出
* p0_system_manager 是系统运行模式（手动/建图/定位导航/语义任务/急停）的唯一事实源（Single Source of Truth）。所有模式切换请求必须经过 system_manager 仲裁后生效。

### 7.12.3 边界

* 不做任务细节执行
* 不做导航执行
* 不做底盘硬实时控制

---

## 7.13 p0_data_tools

### 7.13.1 作用

承载数据记录、事件留痕、回放辅助、复盘支撑。

### 7.13.2 主要职责

* bag 录制组织
* 事件记录
* 关键运行阶段打点
* 复盘辅助脚本组织
* 日志整理辅助

### 7.13.3 边界

* 不侵入主业务逻辑
* 不承担系统控制权
* 以旁路支撑方式存在

### 7.13.4 录制 profile 定义

* p0_data_tools 支持两级录制 profile，通过 launch 参数选择：

* 标准 profile（默认，每次运行必录）：
/cmd_vel, /odom, /tf, /tf_static, /localization/pose, /localization/status, /navigation/status, /safety/*, /system/status, /task/status

* 完整 profile（实验数据采集时显式选择）：
标准 profile + /livox/lidar, /camera/depth/*, /camera/color/image_raw

* 估算：标准 profile 约 10 分钟 < 100MB；完整 profile 约 10 分钟 2-5GB，需确认 Orin NX 存储余量后使用。
---

## 8. 包依赖关系总览

软件包依赖应尽量保持单向、清晰、可替换。

推荐依赖方向如下：

```text
p0_interfaces
   ↑
   ├── p0_base_bridge
   ├── p0_sensor_drivers
   ├── p0_localization
   ├── p0_mapping
   ├── p0_map_manager
   ├── p0_navigation
   ├── p0_semantic_nav
   ├── p0_task_manager
   ├── p0_safety_manager
   ├── p0_system_manager
   └── p0_data_tools

p0_sensor_drivers ──→ p0_localization / p0_mapping / p0_safety_manager / p0_data_tools
p0_base_bridge ────→ p0_localization / p0_navigation / p0_safety_manager / p0_system_manager / p0_data_tools
p0_map_manager ────→ p0_localization / p0_mapping / p0_navigation / p0_semantic_nav
p0_localization ───→ p0_navigation / p0_safety_manager / p0_system_manager / p0_data_tools
p0_mapping ────────→ p0_map_manager / p0_system_manager / p0_data_tools
p0_semantic_nav ───→ p0_task_manager / p0_navigation
p0_navigation ─────→ p0_task_manager / p0_safety_manager / p0_data_tools
p0_safety_manager ─→ p0_system_manager（仅通过急停接口）
p0_task_manager ─→ 订阅 p0_safety_manager 的安全事件话题
p0_system_manager ─→ p0_bringup（通过模式组织，不是代码反向依赖）
```

---

## 9. 接口定义总原则

接口层面采用：

* **话题**：持续数据流、状态流、广播型信息
* **服务**：快速请求-响应型操作
* **动作**：有执行过程、有反馈、有成功/失败结果的长任务

### 9.1 话题适用场景

* 传感器数据
* 位姿数据
* 底盘状态
* 系统状态
* 安全状态
* 任务状态广播

### 9.2 服务适用场景

* 切换模式
* 保存地图
* 加载地图
* 查询语义位置
* 触发自检

### 9.3 动作适用场景

* 语义导航任务
* 点位导航任务
* 长时任务执行过程反馈

---

## 10. 话题接口定义（建议版）

以下为可直接进入项目总文件夹的软件架构级接口定义建议。
命名采用统一前缀 `/p0/...`，后续实现时可按此落地。

---

## 10.1 感知层话题

| 话题名                        | 类型                           | 发布方               | 订阅方                                                       | 作用                |
| -------------------------- | ---------------------------- | ----------------- | --------------------------------------------------------- | ----------------- |
| `/p0/sensors/lidar/points` | 标准点云消息                       | p0_sensor_drivers | p0_localization, p0_mapping, p0_navigation, p0_data_tools | Mid360 点云主输入      |
| `/p0/sensors/imu/data`     | 标准 IMU 消息                    | p0_sensor_drivers | p0_localization, p0_mapping, p0_data_tools                | Mid360 内置 IMU 主输入 |
| `/p0/sensors/camera/color` | 标准图像消息                       | p0_sensor_drivers | p0_data_tools                                             | D435 RGB 输入       |
| `/p0/sensors/camera/depth` | 标准图像/深度消息                    | p0_sensor_drivers | p0_data_tools                                             | D435 深度输入         |
| `/p0/sensors/status`       | `p0_interfaces/SensorStatus` | p0_sensor_drivers | p0_safety_manager, p0_system_manager, p0_data_tools       | 感知健康状态            |

> 说明：迭代一阶段，D435 话题正式流向记录与调试链路；迭代二可再增加其流向定位/增强链路。

---

## 10.2 底盘与执行层话题

| 话题名                      | 类型                            | 发布方                                      | 订阅方                                                 | 作用         |
| ------------------------ | ----------------------------- | ---------------------------------------- | --------------------------------------------------- | ---------- |
| `/p0/base/cmd_vel`       | 标准速度指令                        | p0_navigation, p0_safety_manager（在保护场景下） | p0_base_bridge                                      | 上层底盘控制意图   |
| `/p0/base/odom`          | 标准里程计消息                       | p0_base_bridge                           | p0_localization, p0_navigation, p0_data_tools       | 底盘里程相关基础反馈 |
| `/p0/base/state`         | `p0_interfaces/BaseState`     | p0_base_bridge                           | p0_safety_manager, p0_system_manager, p0_data_tools | 底盘状态与异常状态  |
| `/p0/base/mode_feedback` | `p0_interfaces/BaseModeState` | p0_base_bridge                           | p0_task_manager, p0_system_manager                  | 底盘当前执行模式反馈 |

---

## 10.3 空间认知层话题

| 话题名                       | 类型                                 | 发布方             | 订阅方                                                                | 作用       |
| ------------------------- | ---------------------------------- | --------------- | ------------------------------------------------------------------ | -------- |
| `/p0/localization/pose`   | 标准位姿消息                             | p0_localization | p0_navigation, p0_safety_manager, p0_system_manager, p0_data_tools | 当前定位结果   |
| `/p0/localization/status` | `p0_interfaces/LocalizationStatus` | p0_localization | p0_safety_manager, p0_system_manager, p0_data_tools                | 定位健康状态   |
| `/p0/mapping/status`      | `p0_interfaces/MappingStatus`      | p0_mapping      | p0_system_manager, p0_data_tools                                   | 建图状态     |
| `/p0/map/current_info`    | `p0_interfaces/MapInfo`            | p0_map_manager  | p0_localization, p0_navigation, p0_system_manager                  | 当前运行地图信息 |

---

## 10.4 导航层话题

| 话题名                     | 类型                               | 发布方                              | 订阅方                                                                  | 作用             |
| ----------------------- | -------------------------------- | -------------------------------- | -------------------------------------------------------------------- | -------------- |
| `/p0/navigation/goal`   | 标准位姿目标或自定义目标                     | p0_semantic_nav, p0_task_manager | p0_navigation                                                        | 导航目标输入         |
| `/p0/navigation/status` | `p0_interfaces/NavigationStatus` | p0_navigation                    | p0_task_manager, p0_safety_manager, p0_system_manager, p0_data_tools | 导航执行状态         |
| `/p0/navigation/path`   | 标准路径消息                           | p0_navigation                    | p0_data_tools, 调试工具                                                  | 当前规划路径         |
| `/p0/navigation/event`  | `p0_interfaces/NavigationEvent`  | p0_navigation                    | p0_task_manager, p0_safety_manager, p0_data_tools                    | 导航异常、重规划、到达等事件 |

---

## 10.5 任务与语义层话题

| 话题名                   | 类型                             | 发布方              | 订阅方                              | 作用              |
| --------------------- | ------------------------------ | ---------------- | -------------------------------- | --------------- |
| `/p0/semantic/input`  | `p0_interfaces/SemanticGoal`   | 外部输入适配节点 / 上层调用方 | p0_semantic_nav                  | 语义目标输入          |
| `/p0/semantic/result` | `p0_interfaces/SemanticResult` | p0_semantic_nav  | p0_task_manager, p0_data_tools   | 语义解析结果          |
| `/p0/task/state`      | `p0_interfaces/TaskState`      | p0_task_manager  | p0_system_manager, p0_data_tools | 任务生命周期状态        |
| `/p0/task/event`      | `p0_interfaces/TaskEvent`      | p0_task_manager  | p0_system_manager, p0_data_tools | 任务开始/结束/失败/中止事件 |

---

## 10.6 安全与系统管理层话题

| 话题名                            | 类型                              | 发布方               | 订阅方                                               | 作用        |
| ------------------------------ | ------------------------------- | ----------------- | ------------------------------------------------- | --------- |
| `/p0/safety/state`             | `p0_interfaces/SafetyState`     | p0_safety_manager | p0_task_manager, p0_system_manager, p0_data_tools | 当前安全状态    |
| `/p0/safety/stop_cmd`          | `p0_interfaces/SafetyCommand`   | p0_safety_manager | p0_base_bridge, p0_task_manager                   | 软件急停/保护控制 |
| `/p0/system/state`             | `p0_interfaces/SystemState`     | p0_system_manager | 全系统、p0_data_tools                                 | 系统总状态     |
| `/p0/system/mode`              | `p0_interfaces/SystemModeState` | p0_system_manager | 全系统                                               | 当前系统模式    |
| `/p0/system/self_check_result` | `p0_interfaces/SelfCheckResult` | p0_system_manager | p0_data_tools                                     | 自检结果      |

---

## 11. 服务接口定义（建议版）

---

## 11.1 地图管理服务

| 服务名                           | 类型                                | 服务方            | 调用方                                | 作用           |
| ----------------------------- | --------------------------------- | -------------- | ---------------------------------- | ------------ |
| `/p0/map/save`                | `p0_interfaces/SaveMap`           | p0_map_manager | p0_mapping, p0_system_manager      | 保存当前地图       |
| `/p0/map/load`                | `p0_interfaces/LoadMap`           | p0_map_manager | p0_localization, p0_system_manager | 加载指定地图       |
| `/p0/map/query_semantic_pose` | `p0_interfaces/QuerySemanticPose` | p0_map_manager | p0_semantic_nav                    | 查询语义位置对应空间目标 |

---

## 11.2 系统管理服务

| 服务名                      | 类型                            | 服务方               | 调用方                   | 作用        |
| ------------------------ | ----------------------------- | ----------------- | --------------------- | --------- |
| `/p0/system/set_mode`    | `p0_interfaces/SetSystemMode` | p0_system_manager | p0_task_manager, 运维入口 | 切换系统模式    |
| `/p0/system/self_check`  | `p0_interfaces/RunSelfCheck`  | p0_system_manager | 运维入口、p0_bringup       | 触发自检      |
| `/p0/system/reset_fault` | `p0_interfaces/ResetFault`    | p0_system_manager | 运维入口                  | 清除可恢复故障状态 |

---

## 11.3 底盘桥接服务

| 服务名                         | 类型                          | 服务方            | 调用方                                | 作用        |
| --------------------------- | --------------------------- | -------------- | ---------------------------------- | --------- |
| `/p0/base/reset_bridge`     | `p0_interfaces/ResetBridge` | p0_base_bridge | p0_system_manager                  | 重新初始化底盘桥接 |
| `/p0/base/set_control_mode` | `p0_interfaces/SetBaseMode` | p0_base_bridge | p0_task_manager, p0_system_manager | 切换底盘控制模式  |

---

## 12. 动作接口定义（建议版）

---

## 12.1 导航动作

| 动作名                               | 类型            | 服务方           | 调用方             | 作用       |
| --------------------------------- | ------------- | ------------- | --------------- | -------- |
| `/p0/navigation/go_to_pose`       | 标准导航动作或封装动作   | p0_navigation | p0_task_manager | 执行点位导航   |
| `/p0/navigation/follow_waypoints` | 标准多点导航动作或封装动作 | p0_navigation | p0_task_manager | 执行多目标点导航 |

---

## 12.2 语义导航动作

| 动作名                        | 类型                          | 服务方             | 调用方           | 作用                |
| -------------------------- | --------------------------- | --------------- | ------------- | ----------------- |
| `/p0/semantic_nav/execute` | `p0_interfaces/SemanticNav` | p0_task_manager | 上层任务入口/人工触发入口 | 执行从语义输入到导航完成的完整链路 |

---

## 13. 数据流设计

---

## 13.1 主感知数据流

```text
Mid360 → p0_sensor_drivers → /p0/sensors/lidar/points → p0_localization / p0_mapping / p0_navigation
Mid360 IMU → p0_sensor_drivers → /p0/sensors/imu/data → p0_localization / p0_mapping
D435 → p0_sensor_drivers → /p0/sensors/camera/color, /p0/sensors/camera/depth → p0_data_tools
```

---

## 13.2 底盘反馈数据流

```text
STM32 → p0_base_bridge → /p0/base/odom, /p0/base/state → 
p0_localization / p0_navigation / p0_safety_manager / p0_system_manager / p0_data_tools
```

---

## 13.3 空间认知数据流

```text
p0_localization → /p0/localization/pose, /p0/localization/status →
p0_navigation / p0_safety_manager / p0_system_manager / p0_data_tools

p0_mapping → /p0/mapping/status → p0_system_manager / p0_data_tools
p0_map_manager → /p0/map/current_info → p0_localization / p0_navigation / p0_system_manager
```

---

## 13.4 任务与导航数据流

```text
/p0/semantic/input → p0_semantic_nav → /p0/navigation/goal → p0_navigation
p0_navigation → /p0/navigation/status, /p0/navigation/event → p0_task_manager
p0_task_manager → /p0/task/state, /p0/task/event → p0_system_manager / p0_data_tools
```

---

## 13.5 安全与管理数据流

```text
感知状态 / 定位状态 / 导航状态 / 底盘状态 → p0_safety_manager → /p0/safety/state, /p0/safety/stop_cmd
全系统关键状态 → p0_system_manager → /p0/system/state, /p0/system/mode
```

---

## 14. 控制流设计

---

## 14.1 自主任务控制流

```text
语义输入
→ p0_semantic_nav
→ p0_task_manager
→ p0_navigation
→ /p0/base/cmd_vel
→ p0_base_bridge
→ STM32
→ 电机驱动/底盘执行
```

---

## 14.2 软件急停控制流

```text
异常检测
→ p0_safety_manager
→ /p0/safety/stop_cmd
→ p0_base_bridge
→ STM32
→ 底盘停车
```

---

## 14.3 模式切换控制流

```text
模式切换请求
→ p0_system_manager
→ /p0/system/mode
→ p0_task_manager / p0_navigation / p0_base_bridge / p0_safety_manager
```

---

## 15. 状态流设计

项目0软件架构中，状态流必须形成“可观测、可聚合、可记录”的结构。

### 15.1 局部状态

各核心包分别输出：

* 感知状态
* 底盘状态
* 定位状态
* 建图状态
* 导航状态
* 任务状态
* 安全状态

### 15.2 聚合状态

由 `p0_system_manager` 聚合形成：

* 系统总状态
* 当前系统模式
* 运行准入结果
* 故障等级

### 15.3 留痕状态

由 `p0_data_tools` 对关键状态进行：

* 记录
* 打点
* 回放辅助组织

---

## 16. 模式化启动的软件组织

软件架构必须直接支撑以下模式启动。

---

## 16.1 建图模式

启动包建议：

* p0_sensor_drivers
* p0_base_bridge
* p0_mapping
* p0_map_manager
* p0_system_manager
* p0_safety_manager
* p0_data_tools

不启动：

* p0_navigation 的自主导航主链路
* p0_semantic_nav
* p0_task_manager 的完整任务链路

---

## 16.2 定位运行模式

启动包建议：

* p0_sensor_drivers
* p0_base_bridge
* p0_localization
* p0_map_manager
* p0_system_manager
* p0_safety_manager
* p0_data_tools

---

## 16.3 自主任务模式

启动包建议：

* p0_sensor_drivers
* p0_base_bridge
* p0_localization
* p0_map_manager
* p0_navigation
* p0_semantic_nav
* p0_task_manager
* p0_safety_manager
* p0_system_manager
* p0_data_tools

---

## 16.4 调试模式

根据调试对象裁剪启动：

* 感知调试
* 底盘桥接调试
* 定位调试
* 导航调试
* 安全管理调试

由 `p0_bringup` 统一组织。

---

## 17. 软件架构与计算通信架构的映射关系

| 计算实体      | 主要软件包/组件                                                                                                                                                                                                                   |
| --------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Orin NX   | p0_interfaces, p0_bringup, p0_sensor_drivers, p0_base_bridge, p0_localization, p0_mapping, p0_map_manager, p0_navigation, p0_semantic_nav, p0_task_manager, p0_safety_manager, p0_system_manager, p0_data_tools, 第三方ROS2依赖 |
| STM32F407 | 独立固件（不属于 ROS2 workspace），通过 p0_base_bridge 与 Orin NX 连接                                                                                                                                                                    |

这与已确定的“ROS2 主业务集中在 Orin NX，STM32 不承担 ROS2 主业务”的计算与通信架构一致。

---

## 18. 软件架构与系统总架构的映射关系

| 系统总架构模块   | 软件包落位                                         |
| --------- | --------------------------------------------- |
| 执行模块      | p0_base_bridge + STM32 固件                     |
| 感知模块      | p0_sensor_drivers                             |
| 空间认知模块    | p0_localization + p0_mapping + p0_map_manager |
| 行动规划模块    | p0_navigation                                 |
| 任务决策模块    | p0_semantic_nav + p0_task_manager             |
| 安全保障模块    | p0_safety_manager                             |
| 系统管理模块    | p0_system_manager + p0_bringup                |
| 数据记录与复盘模块 | p0_data_tools                                 |

显式映射表如下:

| 总架构层/链路 | 对应软件包 |
|---|---|
| 执行层 | p0_base_bridge |
| 感知层 | p0_sensor_drivers |
| 空间认知层 | p0_localization, p0_mapping, p0_map_manager |
| 行动规划层 | p0_navigation |
| 任务决策层 | p0_semantic_nav, p0_task_manager |
| 安全保障链路 | p0_safety_manager |
| 系统管理链路 | p0_system_manager, p0_bringup |
| 数据记录链路 | p0_data_tools |
| 统一接口 | p0_interfaces |
因此，本软件架构是在系统总架构骨架上的**软件层展开**，而不是对总架构的重新定义。

---

## 19. 迭代一到迭代二的软件演进边界

### 19.1 迭代一阶段

迭代一软件架构重点是：

* 跑通主链路
* 建立统一接口骨架
* 建立安全、管理、记录的基础辅助包
* 保证地图、语义位置表、任务、模式都能最小成立

### 19.2 迭代二阶段

迭代二不推翻软件架构，只做以下增强：

#### （1）感知与空间认知增强

* p0_sensor_drivers 增加对 D435 更深利用
* p0_localization 增加多传感器融合增强
* 可能增加回环增强相关子模块（可内聚到 p0_localization，必要时再独立增包）

#### （2）语义导航增强

* p0_semantic_nav 增强解析能力
* p0_task_manager 增强任务表达与多轮任务组织能力

#### （3）数据与实验支撑增强

* p0_data_tools 增强实验记录与对比实验辅助能力

---

## 20. 直接放入项目总文件夹的建议文件名

建议文件名：

```text
software_architecture.md
```

建议放置位置：

```text
项目总文件夹/docs/architecture/software_architecture.md
```

如果当前总文件夹未细分，也可先放在：

```text
项目总文件夹/software_architecture.md
```

---

## 21. 最终结论

项目0软件架构可以概括为：

> 项目0采用基于单一主 ROS2 workspace 的软件架构，在 Orin NX 上统一组织感知接入、底盘桥接、定位、建图、地图管理、导航、语义导航、任务管理、安全管理、系统管理与数据记录等软件包，并通过 `p0_interfaces` 统一定义项目内部消息、服务与动作接口。软件主链路按“感知输入 → 空间认知 → 行动规划 → 任务决策 → 底盘控制”组织，辅助链路按“安全监测与处置、系统管理与模式组织、数据记录与复盘支撑”组织；STM32 不运行 ROS2 主业务，仅以独立固件形式通过 `p0_base_bridge` 接入 ROS2 世界。该软件架构既能直接支撑迭代一最小闭环平台成立，也能在不推翻整体结构的前提下承接迭代二的多传感器融合增强、定位建图鲁棒性增强与语义导航深化。 

```
```

## 24. 关键包之间的调用关系（展开版）

本节在前文“包依赖关系总览”基础上，进一步给出更接近工程实施的调用逻辑。

---

### 24.1 p0_semantic_nav 与 p0_map_manager

调用关系：
- `p0_semantic_nav` 接收语义输入
- 调用 `p0_map_manager` 的语义查询服务
- 获得目标位姿或目标区域信息
- 再将结果转换为导航目标输出

结论：
- `p0_semantic_nav` 负责“理解语义并转目标”
- `p0_map_manager` 负责“提供语义-空间映射数据”

二者边界不能混。

---

### 24.2 p0_task_manager 与 p0_navigation

调用关系：
- `p0_task_manager` 根据任务类型发起导航动作
- `p0_navigation` 负责执行导航并持续反馈状态
- `p0_task_manager` 根据反馈维护任务生命周期

结论：
- `p0_task_manager` 负责“任务是否成立、任务是否结束”
- `p0_navigation` 负责“导航怎么执行”

---

### 24.3 p0_safety_manager 与 p0_navigation / p0_base_bridge

调用关系：
- `p0_safety_manager` 订阅导航状态、定位状态、感知状态、底盘状态
- 当异常成立时：
  - 对 `p0_task_manager` 发出任务中止/冻结影响
  - 对 `p0_base_bridge` 发出停车/保护指令

结论：
- 安全包不直接接管导航逻辑
- 但安全包有权中断导航结果继续下发到底盘

---

### 24.4 p0_system_manager 与全系统

调用关系：
- 汇总来自各包的状态
- 判断系统是否允许进入某一模式
- 负责系统状态和模式对外统一输出
- 可通过服务触发自检、故障重置、模式切换

结论：
- `p0_system_manager` 是系统级运行组织中心
- 但不是导航中心，也不是任务中心

---

### 24.5 p0_data_tools 与全系统

调用关系：
- 订阅各功能包的关键状态和事件
- 组织 bag 录制和日志标记
- 不向主业务链路回写控制指令

结论：
- `p0_data_tools` 必须全局可观测
- 但不应拥有控制权

---

## 25. 包划分边界的反例说明（防止后续跑偏）

为了便于你后面继续做软件架构审查、接口定义和代码实现，这里专门写出几条**不能这么做**的反例。

### 25.1 不能把语义位置表管理写进 p0_semantic_nav
原因：
- 语义位置表本质上属于地图/空间静态资源
- 它应由 `p0_map_manager` 管理
- `p0_semantic_nav` 只负责使用，不负责拥有

### 25.2 不能把系统模式管理完全塞进 p0_task_manager
原因：
- 任务管理只是一部分业务逻辑
- 系统模式涉及建图、定位运行、急停、调试、待机等全局状态
- 这些必须由 `p0_system_manager` 统一管理，`p0_task_manager` 只负责业务侧配合

### 25.3 不能把安全检测散落到所有包里各自处理
原因：
- 可以允许局部包输出自身状态
- 但真正的安全判断与处置仲裁必须由 `p0_safety_manager` 集中承担
- 否则后续会出现多处急停逻辑打架

### 25.4 不能让 p0_base_bridge 直接理解语义任务
原因：
- 底盘桥接包只处理“底盘控制与反馈桥接”
- 不应越级承担任务、语义、导航理解逻辑
- 否则会破坏分层

### 25.5 不能让 p0_data_tools 侵入主业务代码
原因：
- 记录链路应是伴随式支撑
- 不能把业务决策建立在记录链路之上
- 否则后期调试和发布版本会高度耦合

---

## 26. 推荐 launch 文件组织结构

虽然 launch 的具体实现属于后续工程层，但软件架构需要给出可落地的目录组织建议，否则总文件夹不够完整。

建议如下：

```text
launch/
├── modes/
│   ├── mapping.launch.py
│   ├── localization.launch.py
│   ├── autonomous_task.launch.py
│   ├── manual_debug.launch.py
│   └── safe_mode.launch.py
├── groups/
│   ├── sensors.launch.py
│   ├── base_bridge.launch.py
│   ├── localization.launch.py
│   ├── mapping.launch.py
│   ├── navigation.launch.py
│   ├── task_manager.launch.py
│   ├── safety_manager.launch.py
│   ├── system_manager.launch.py
│   └── data_tools.launch.py
└── bringup.launch.py
````

### 26.1 modes 目录

按系统运行模式组织启动入口，适合日常使用和验收。

### 26.2 groups 目录

按功能包或功能组组织启动片段，适合联调和局部调试。

### 26.3 bringup.launch.py

作为统一总入口，根据参数选择不同模式或组合启动。

### 26.4 模式化启动映射表

| 启动模式 | 启动包集合 | 对应 Launch |
|----------|-----------|-------------|
| 建图模式 | sensor_drivers, base_bridge, mapping, map_manager, system_manager, safety_manager, data_tools | mapping.launch.py |
| 定位导航模式 | sensor_drivers, base_bridge, localization, map_manager, navigation, system_manager, safety_manager, data_tools | localization.launch.py |
| 语义任务模式 | 定位导航模式全部 + semantic_nav, task_manager | autonomous_task.launch.py |
| 手动调试模式 | sensor_drivers, base_bridge, system_manager, safety_manager, data_tools | manual_debug.launch.py |
| 安全模式 | base_bridge（仅急停监听）, safety_manager, system_manager | safe_mode.launch.py |
---



## 27. 配置文件组织结构（建议版）

为了让该文档能直接进入项目总文件夹并服务后续实现，配置文件目录建议也要同步写清。

```text
config/
├── sensors/
│   ├── mid360.yaml
│   ├── d435.yaml
│   └── sensor_status_rules.yaml
├── base/
│   ├── base_bridge.yaml
│   ├── base_limits.yaml
│   └── base_modes.yaml
├── localization/
│   ├── fastlio_mapping.yaml
│   ├── fastlio_localization.yaml
│   └── localization_rules.yaml
├── navigation/
│   ├── nav2_common.yaml
│   ├── global_planner.yaml
│   ├── local_planner.yaml
│   ├── costmap_global.yaml
│   ├── costmap_local.yaml
│   └── navigation_rules.yaml
├── semantic/
│   ├── semantic_nav.yaml
│   └── semantic_places.yaml
├── safety/
│   ├── safety_rules.yaml
│   ├── keepout_policy.yaml
│   └── stop_conditions.yaml
├── system/
│   ├── system_modes.yaml
│   ├── self_check_rules.yaml
│   └── system_state_rules.yaml
└── modes/
    ├── mapping_mode.yaml
    ├── localization_mode.yaml
    ├── autonomous_task_mode.yaml
    └── debug_mode.yaml
```

### 27.1 配置组织原则

* 驱动配置和业务规则配置分开
* 共性配置和模式配置分开
* 尽量不把配置硬编码进 launch
* 尽量让“模式切换”通过配置切换而不是代码复制

---

## 28. 第三方包与自研包的边界

为了避免后续开发中把第三方依赖和自研逻辑揉在一起，这里明确边界。

### 28.1 第三方包

主要负责：

* 提供驱动
* 提供通用导航能力
* 提供通用建图/定位能力
* 提供行为树底层框架能力

这些包包括：

* livox_ros_driver2
* realsense2_camera
* FAST-LIO2 ROS2 版本
* Nav2
* BehaviorTree.CPP 相关依赖

### 28.2 自研包

主要负责：

* 项目0自身系统组织
* 任务逻辑
* 语义导航逻辑
* 地图资源管理
* 安全链路组织
* 系统管理
* 底盘桥接
* 数据记录和复盘组织

### 28.3 边界要求

* 不要直接修改第三方包核心代码作为主路径
* 自研逻辑尽量通过外层封装、接口适配、参数配置、组合启动来实现
* 只有在确实必要时才对第三方包做最小修改，并且要单独记录

---

## 29. 软件架构下的最小可运行闭环

为了保证软件架构不是纯结构化描述，而是能直接指导迭代一落地，这里给出“最小可运行闭环”的软件包集合。

### 29.1 最小建图闭环

* p0_sensor_drivers
* p0_base_bridge
* p0_mapping
* p0_map_manager
* p0_system_manager
* p0_safety_manager
* p0_data_tools

### 29.2 最小定位导航闭环

* p0_sensor_drivers
* p0_base_bridge
* p0_localization
* p0_map_manager
* p0_navigation
* p0_system_manager
* p0_safety_manager
* p0_data_tools

### 29.3 最小语义任务闭环

* p0_sensor_drivers
* p0_base_bridge
* p0_localization
* p0_map_manager
* p0_navigation
* p0_semantic_nav
* p0_task_manager
* p0_system_manager
* p0_safety_manager
* p0_data_tools

这三个集合分别对应：

* 建图成立
* 自主导航成立
* 语义导航与任务调度成立

与项目流程 P3、P4、P5 的推进节奏一致。

---

## 30. 软件架构边界结论

为了确保你后续写接口定义、模块实现和联调文档时不跑偏，这里再做一次明确收束。

### 30.1 本文档已经定义的内容

* workspace 如何组织
* 包如何划分
* 包之间职责边界是什么
* 主要话题 / 服务 / 动作接口如何定义
* 数据流、控制流、状态流如何展开
* 模式启动如何组织
* 与系统总架构、计算与通信架构如何映射

### 30.2 本文档故意不定义的内容

* 每个包内部到底有几个节点
* 每个节点的具体回调逻辑
* 协议帧字节布局
* 各接口的字段级消息定义
* 第三方包参数具体怎么调
* launch 文件具体 Python 实现
* rosbag 录制脚本具体写法

这些内容应分别交给：

* 接口定义文档
* 模块实现设计文档
* 联调与部署说明
* 参数配置文档

## 1-2 条典型异常传播路径的文字描述

示例：底盘通信中断
STM32 通信超时 → p0_base_bridge 检测到 → 发布 ChassisStatus(COMM_LOST) 
→ p0_safety_manager 订阅 → 触发 TriggerEmergencyStop 
→ p0_system_manager 执行 → 切换至急停模式 
→ p0_task_manager 收到模式变更 → 中止当前任务
---

## 31. 最终定稿式总结（补充版）

项目0软件架构最终可以进一步精炼为：

> 项目0在 Orin NX 上采用单一主 ROS2 workspace 作为软件主承载结构，通过 `p0_interfaces` 统一定义内部接口，通过 `p0_bringup` 统一组织模式化启动，通过感知接入、底盘桥接、定位、建图、地图管理、导航、语义导航、任务管理、安全管理、系统管理和数据记录等自研包完成系统主链路与辅助链路的软件展开。软件主链路按“感知输入—空间认知—行动规划—任务决策—底盘控制”组织，辅助链路按“安全、管理、记录”组织，并通过明确的话题、服务、动作接口解耦。该软件架构能够直接支撑迭代一最小闭环成立，同时为迭代二的多传感器融合增强、定位建图鲁棒性增强和语义导航深化提供稳定的软件骨架。
