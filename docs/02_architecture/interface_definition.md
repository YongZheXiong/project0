# 1. 文档定位

本文档属于项目0在 P1 阶段的系统架构设计输出物之一，放置在 docs/02_architecture/ 目录下，与 system_architecture.md、compute_comm_architecture.md、power_architecture.md、hardware_architecture.md、software_architecture.md 并列管理。

根据项目文件结构设计，项目0在 docs/02_architecture/ 下单独保留 interface_definition.md，用于继续展开模块间具体接口定义、自定义消息结构与调用关系。

本文档与 software_architecture.md 的边界如下：

* software_architecture.md：回答“为什么这样分包、包之间大概如何交互、主链路和辅助链路如何在软件层面贯通”。
* interface_definition.md：回答“具体有哪些 topic / service / action，它们的名字、数据类型、发布者、订阅者、调用方、返回结构分别是什么”

本文档当前版本为**骨架版 V0.1**，服务于迭代一“先跑通主链路、建立统一接口骨架、建立安全/管理/记录基础辅助包、保证地图/语义位置表/任务/模式最小成立”的目标，不追求一次性把全部字段定义写死。

----------------------------------------

# 2. 编写原则

## 2.1 接口分层原则

项目0内部接口分为三类：

* **Topic**：用于持续数据流、状态流、广播型信息，如传感器数据、底盘状态、定位状态、导航状态、系统状态等。
* **Service**：用于快速请求-响应型操作，如模式切换、保存地图、加载地图、查询语义位置、触发自检、急停触发等。
* **Action**：用于有执行过程、过程反馈和成功/失败结果的长任务，如点位导航、语义导航任务、长时任务执行反馈等。

## 2.2 接口统一归口原则

凡是跨包通用、且标准消息无法直接表达的结构，统一收口到 `p0_interfaces` 中定义，避免各包私自定义重复数据结构。

典型统一结构包括：

* 底盘控制与状态结构；
* 系统状态结构；
* 安全事件结构；
* 定位质量结构；
* 语义目标结构；
* 任务状态结构。

## 2.3 接口边界原则

接口设计必须服务于分层解耦，而不能破坏分层。典型约束包括：

* `p0_base_bridge` 不直接理解语义任务；
* `p0_semantic_nav` 不直接管理地图文件；
* `p0_task_manager` 不直接承担底层路径规划；
* `p0_safety_manager` 集中承担安全仲裁；
* `p0_data_tools` 不反向控制主业务逻辑。

## 2.4 当前版本定位原则

本版本是骨架版接口定义表，因此：

* 允许部分字段写为“待细化 / 后续补充”；
* 允许少量接口名称在 P2-P5 联调中调整；
* 允许为迭代二增强保留预留字段与备注列；
* 但迭代一最小闭环所需接口应尽量先稳定下来。

----------------------------------------

# 3. 命名规范

## 3.1 统一前缀

接口命名统一采用 `/p0/...` 前缀，后续实现时按此落地。

## 3.2 命名风格

建议采用如下风格：

* Topic：`/p0/<domain>/<subdomain>/<name>`
* Service：`/p0/<domain>/<operation>`
* Action：`/p0/<domain>/<task>`

示例：

* `/p0/sensors/lidar/points`
* `/p0/system/set_mode`
* `/p0/navigation/go_to_pose`

## 3.3 类型命名

自定义接口类型统一放入 `p0_interfaces` 包中，命名风格如下：

* msg：`<Name>.msg`
* srv：`<Verb><Name>.srv` 或 `<Name>.srv`
* action：`<Verb><Name>.action`

示例：

* `ChassisCmd.msg`
* `ChassisStatus.msg`
* `SetSystemMode.srv`
* `NavigateToSemantic.action`

----------------------------------------

# 4. 软件包与接口责任映射

| 软件包 | 接口责任 |
| --- | --- |
| `p0_interfaces` | 统一定义项目内部 msg / srv / action |
| `p0_sensor_drivers` | 发布激光雷达、IMU、相机及传感器状态数据 |
| `p0_base_bridge` | 接收底盘控制指令，发布底盘反馈、通信状态、运动状态 |
| `p0_mapping` | 消费建图传感器数据，发布建图状态，调用地图保存接口 |
| `p0_localization` | 消费定位传感器数据与地图资源，发布定位状态 |
| `p0_map_manager` | 提供地图保存/加载/当前地图信息/语义位置查询接口 |
| `p0_navigation` | 接收导航目标，发布导航状态/路径/事件，提供导航 action |
| `p0_semantic_nav` | 接收语义目标输入，调用语义位置查询接口，输出导航目标或语义解析结果 |
| `p0_task_manager` | 发起导航任务，维护任务状态，订阅安全事件与导航状态 |
| `p0_safety_manager` | 接收多源状态输入，发布安全事件，必要时触发安全处置接口 |
| `p0_system_manager` | 提供模式切换、自检、故障复位等服务，聚合系统状态 |
| `p0_data_tools` | 订阅关键数据流、状态流、事件流，用于记录与复盘，不反控主逻辑 |

----------------------------------------

# 5. Topic 接口定义表

## 5.1 感知层 Topic

| Topic 名称 | 类型 | 发布方 | 订阅方 | 作用 | 迭代一状态 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| `/p0/sensors/lidar/points` | 标准点云消息 | `p0_sensor_drivers` | `p0_localization`, `p0_mapping`, `p0_navigation`, `p0_data_tools` | Mid360 点云主输入 | 必须实现 | 具体消息类型后续细化，建议采用标准点云消息。 |
| `/p0/sensors/imu/data` | 标准 IMU 消息 | `p0_sensor_drivers` | `p0_localization`, `p0_mapping`, `p0_data_tools` | Mid360 内置 IMU 主输入 | 必须实现 | 建议采用标准 IMU 消息。 |
| `/p0/sensors/camera/color` | 标准图像消息 | `p0_sensor_drivers` | `p0_data_tools` | D435 RGB 输入 | 建议实现 | 迭代一先以记录与调试为主，迭代二可增强利用。 |
| `/p0/sensors/camera/depth` | 标准图像/深度消息 | `p0_sensor_drivers` | `p0_data_tools` | D435 深度输入 | 建议实现 | 迭代一先接入，深度利用可后续增强。 |
| `/p0/sensors/status` | `p0_interfaces/SensorStatus` | `p0_sensor_drivers` | `p0_system_manager`, `p0_safety_manager`, `p0_data_tools` | 传感器在线状态、异常状态、基础健康信息 | 接口预留 | 当前类型待补充到 `p0_interfaces`。依据传感器管理与状态可观测预留需求设置。 |

## 5.2 底盘与执行层 Topic

| Topic 名称 | 类型 | 发布方 | 订阅方 | 作用 | 迭代一状态 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| `/p0/base/cmd_vel` | `p0_interfaces/ChassisCmd` | `p0_navigation`, 手动控制节点 | `p0_base_bridge` | 上位机到底盘的速度指令 | 必须实现 | 对应“系统能够接收上层速度指令并转化为电机控制信号”。 |
| `/p0/base/status` | `p0_interfaces/ChassisStatus` | `p0_base_bridge` | `p0_navigation`, `p0_localization`, `p0_system_manager`, `p0_safety_manager`, `p0_data_tools` | 底盘反馈、通信状态、编码器、电压等 | 必须实现 | 属于跨包通用底盘状态结构。 |
| `/p0/base/odom` | 标准里程计消息 | `p0_base_bridge` | `p0_localization`, `p0_navigation`, `p0_data_tools` | 底盘里程计输出 | 必须实现 | 消息类型后续细化，建议使用标准 odom 消息。 |
| `/p0/base/event` | `p0_interfaces/BaseEvent` | `p0_base_bridge` | `p0_safety_manager`, `p0_system_manager`, `p0_data_tools` | 底盘通信异常、超时、控制模式变化等事件 | 接口预留 | 当前 V0.1 保留。 |

## 5.3 建图与定位层 Topic

| Topic 名称 | 类型 | 发布方 | 订阅方 | 作用 | 迭代一状态 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| `/p0/mapping/status` | `p0_interfaces/MappingStatus` | `p0_mapping` | `p0_system_manager`, `p0_data_tools` | 建图状态 | 建议实现 | 已在建议版接口中出现。 |
| `/p0/localization/status` | `p0_interfaces/LocalizationStatus` | `p0_localization` | `p0_system_manager`, `p0_navigation`, `p0_safety_manager`, `p0_data_tools` | 定位质量状态（Good / Degraded / Lost） | 必须实现 | 已在初始接口清单中给出骨架。 |
| `/p0/localization/pose` | 标准位姿消息 | `p0_localization` | `p0_navigation`, `p0_data_tools` | 当前机器人位姿输出 | 必须实现 | 消息类型后续细化。 |
| `/p0/map/current_info` | `p0_interfaces/MapInfo` | `p0_map_manager` | `p0_localization`, `p0_navigation`, `p0_system_manager` | 当前运行地图信息 | 建议实现 | 已在建议版接口中出现。 |

## 5.4 导航层 Topic

| Topic 名称 | 类型 | 发布方 | 订阅方 | 作用 | 迭代一状态 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| `/p0/navigation/goal` | 标准位姿目标或自定义目标 | `p0_semantic_nav`, `p0_task_manager` | `p0_navigation` | 导航目标输入 | 必须实现 | 已在建议版接口中出现。[14] |
| `/p0/navigation/status` | `p0_interfaces/NavigationStatus` | `p0_navigation` | `p0_task_manager`, `p0_safety_manager`, `p0_system_manager`, `p0_data_tools` | 导航执行状态 | 必须实现 | 已在建议版接口中出现。 |
| `/p0/navigation/path` | 标准路径消息 | `p0_navigation` | `p0_data_tools`, 调试工具 | 当前规划路径 | 建议实现 | 便于调试与记录。 |
| `/p0/navigation/event` | `p0_interfaces/NavigationEvent` | `p0_navigation` | `p0_task_manager`, `p0_safety_manager`, `p0_data_tools` | 导航异常、重规划、到达等事件 | 建议实现 | 已在建议版接口中出现。 |

## 5.5 语义与任务层 Topic

| Topic 名称 | 类型 | 发布方 | 订阅方 | 作用 | 迭代一状态 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| `/p0/semantic/input` | `p0_interfaces/SemanticGoal` | 外部输入适配节点 / 上层调用方 | `p0_semantic_nav` | 语义目标输入 | 必须实现 | 已在建议版接口中出现。 |
| `/p0/semantic/result` | `p0_interfaces/SemanticResult` | `p0_semantic_nav` | `p0_task_manager`, `p0_data_tools` | 语义解析结果 | 建议实现 | 已在建议版接口中出现。 |
| `/p0/task/state` | `p0_interfaces/TaskState` | `p0_task_manager` | `p0_system_manager`, `p0_data_tools` | 任务状态广播 | 建议实现 | 建议纳入统一任务状态结构。 |

## 5.6 安全与系统管理层 Topic

| Topic 名称 | 类型 | 发布方 | 订阅方 | 作用 | 迭代一状态 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| `/p0/safety/event` | `p0_interfaces/SafetyEvent` | `p0_safety_manager` | `p0_task_manager`, `p0_system_manager`, `p0_data_tools` | 安全事件广播 | 必须实现 | 已在初始接口清单中给出骨架。 |
| `/p0/system/status` | `p0_interfaces/SystemStatus` | `p0_system_manager` | 全局关键模块、`p0_data_tools` | 当前系统模式、模块在线状态、基础系统状态 | 必须实现 | 已在初始接口清单中给出骨架。 |
| `/p0/system/heartbeat` | `p0_interfaces/SystemHeartbeat` | `p0_system_manager` | `p0_data_tools`, 监控工具 | 系统周期心跳与存活观测 | 接口预留 | 当前 V0.1 预留，便于后续状态可观测增强。 |

----------------------------------------

# 6. Service 接口定义表

## 6.1 地图与语义服务

| Service 名称 | 类型 | 服务方 | 调用方 | 作用 | 迭代一状态 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| `/p0/map/save` | `p0_interfaces/SaveMap` | `p0_map_manager` | `p0_mapping`, 运维入口 | 保存当前地图 | 建议实现 | 软件架构指出建图通过请求响应型接口与地图管理协作完成地图保存。 |
| `/p0/map/load` | `p0_interfaces/LoadMap` | `p0_map_manager` | `p0_localization`, `p0_system_manager` | 加载指定地图 | 必须实现 | 软件架构指出地图管理向定位提供地图加载资源。 |
| `/p0/map/query_semantic_pose` | `p0_interfaces/QuerySemanticPose` | `p0_map_manager` | `p0_semantic_nav` | 查询语义位置对应空间目标 | 必须实现 | 已在建议版接口中出现。 |

## 6.2 系统管理服务

| Service 名称 | 类型 | 服务方 | 调用方 | 作用 | 迭代一状态 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| `/p0/system/set_mode` | `p0_interfaces/SetSystemMode` | `p0_system_manager` | `p0_task_manager`, 运维入口 | 切换系统模式 | 必须实现 | 已在初始接口清单与建议版接口中出现。 |
| `/p0/system/self_check` | `p0_interfaces/RunSelfCheck` | `p0_system_manager` | 运维入口、`p0_bringup` | 触发自检 | 建议实现 | 已在建议版接口中出现。 |
| `/p0/system/reset_fault` | `p0_interfaces/ResetFault` | `p0_system_manager` | 运维入口 | 清除可恢复故障状态 | 接口预留 | 已在建议版接口中出现。 |

## 6.3 安全相关服务

| Service 名称 | 类型 | 服务方 | 调用方 | 作用 | 迭代一状态 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| `/p0/safety/emergency_stop` | `p0_interfaces/TriggerEmergencyStop` | `p0_safety_manager` 或 `p0_system_manager` | 运维入口、`p0_system_manager` | 触发 / 解除急停 | 必须实现 | 初始接口清单已给出骨架，最终归属待联调确认。 |
| `/p0/safety/reset_emergency` | `p0_interfaces/ResetEmergency` | `p0_safety_manager` | 运维入口 | 清除软件侧急停状态 | 接口预留 | 与硬件急停边界需在 P2-P4 联调中进一步明确。 |

## 6.4 底盘桥接服务

| Service 名称 | 类型 | 服务方 | 调用方 | 作用 | 迭代一状态 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| `/p0/base/reset_bridge` | `p0_interfaces/ResetBridge` | `p0_base_bridge` | `p0_system_manager` | 重新初始化底盘桥接 | 建议实现 | 已在建议版接口中出现。 |
| `/p0/base/set_control_mode` | `p0_interfaces/SetBaseMode` | `p0_base_bridge` | `p0_task_manager`, `p0_system_manager` | 切换底盘控制模式 | 建议实现 | 已在建议版接口中出现。 |

----------------------------------------

# 7. Action 接口定义表

## 7.1 导航 Action

| Action 名称 | 类型 | 服务方 | 调用方 | 作用 | 迭代一状态 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| `/p0/navigation/go_to_pose` | 标准导航动作或封装动作 | `p0_navigation` | `p0_task_manager` | 执行点位导航 | 必须实现 | 已在建议版接口中出现。 |
| `/p0/navigation/follow_waypoints` | 标准导航动作或封装动作 | `p0_navigation` | `p0_task_manager` | 执行多点位导航 | 接口预留 | 已在建议版接口中出现片段，迭代一非必须。 |
| `/p0/navigation/navigate_to_semantic` | `p0_interfaces/NavigateToSemantic` | `p0_navigation` 或 `p0_task_manager` | 上层任务调用方 | 语义导航任务执行 | 接口预留 | 初始接口清单给出骨架，最终服务方待联调确认。 |

## 7.2 任务 Action

| Action 名称 | 类型 | 服务方 | 调用方 | 作用 | 迭代一状态 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| `/p0/task/execute` | `p0_interfaces/ExecuteTask` | `p0_task_manager` | 上层任务入口 | 执行单步或多步任务 | 接口预留 | 迭代一先保证顺序任务可成立，复杂任务表达后续增强。 |

----------------------------------------

# 8. p0_interfaces 自定义类型骨架

根据架构约束，凡是跨包通用且标准消息无法直接表达的结构，统一放入 `p0_interfaces`。

## 8.1 Message 清单（骨架版）

| 文件名 | 作用 | 当前状态 |
| --- | --- | --- |
| `ChassisCmd.msg` | 上位机 → 底盘：速度指令 | 必须实现 |
| `ChassisStatus.msg` | 底盘 → 上位机：底盘状态（通信状态、编码器、电压等） | 必须实现 |
| `SystemStatus.msg` | 系统管理：当前模式、各模块在线状态 | 必须实现 |
| `SafetyEvent.msg` | 安全管理：安全事件类型、等级、时间戳 | 必须实现 |
| `LocalizationStatus.msg` | 定位模块：定位质量等级（Good / Degraded / Lost） | 必须实现[4] |
| `MappingStatus.msg` | 建图状态 | 建议实现 |
| `MapInfo.msg` | 当前地图信息 | 建议实现 |
| `NavigationStatus.msg` | 导航执行状态 | 必须实现 |
| `NavigationEvent.msg` | 导航异常 / 重规划 / 到达等事件 | 建议实现 |
| `SemanticGoal.msg` | 语义目标输入结构 | 必须实现 |
| `SemanticResult.msg` | 语义解析结果结构 | 建议实现 |
| `TaskState.msg` | 任务状态结构 | 建议实现 |
| `SensorStatus.msg` | 传感器状态结构 | 接口预留 |
| `BaseEvent.msg` | 底盘桥接事件结构 | 接口预留 |
| `SystemHeartbeat.msg` | 系统心跳结构 | 接口预留 |

## 8.2 Service 清单（骨架版）

| 文件名 | 作用 | 当前状态 |
| --- | --- | --- |
| `QuerySemanticPose.srv` / `GetSemanticPose.srv` | 查询语义位置 → 空间位姿 | 必须实现 |
| `SetSystemMode.srv` | 请求切换系统模式 | 必须实现 |
| `TriggerEmergencyStop.srv` | 触发 / 解除急停 | 必须实现 |
| `LoadMap.srv` | 加载地图 | 必须实现 |
| `RunSelfCheck.srv` | 触发自检 | 建议实现 |
| `ResetFault.srv` | 清除可恢复故障状态 | 接口预留 |
| `ResetBridge.srv` | 重新初始化底盘桥接 | 建议实现 |
| `SetBaseMode.srv` | 切换底盘控制模式 | 建议实现 |

> 注：`QuerySemanticPose.srv` 与 `GetSemanticPose.srv` 当前命名存在两版来源，V0.1 暂记为“二选一待统一”，后续建议统一为单一名称。

## 8.3 Action 清单（骨架版）

| 文件名 | 作用 | 当前状态 |
| --- | --- | --- |
| `NavigateToSemantic.action` | 语义导航任务（目标名称 → 导航执行 → 结果反馈） | 接口预留 / 建议实现 |
| `ExecuteTask.action` | 任务执行动作 | 接口预留 |
| `GoToPose.action` | 点位导航封装动作 | 建议实现 |

----------------------------------------

# 9. 迭代一最小闭环必需接口

## 9.1 P2 底盘与基础运动成立

至少应先稳定以下接口：

* `/p0/base/cmd_vel`
* `/p0/base/status`
* `/p0/base/odom`
* `/p0/system/status`
* `/p0/safety/emergency_stop`

## 9.2 P3 感知与建图成立

至少应补齐以下接口：

* `/p0/sensors/lidar/points`
* `/p0/sensors/imu/data`
* `/p0/mapping/status`
* `/p0/map/save`
* `/p0/system/self_check`

## 9.3 P4 定位与导航成立

至少应补齐以下接口：

* `/p0/localization/pose`
* `/p0/localization/status`
* `/p0/map/load`
* `/p0/navigation/goal`
* `/p0/navigation/status`
* `/p0/navigation/go_to_pose`

## 9.4 P5 语义导航与任务调度成立

至少应补齐以下接口：

* `/p0/map/query_semantic_pose`
* `/p0/semantic/input`
* `/p0/semantic/result`
* `/p0/task/state`
* `NavigateToSemantic.action`

----------------------------------------

# 10. 接口预留项

根据迭代一“接口预留”原则，以下能力当前可不要求完整实现，但应保留接口扩展空间：

* 传感器统一状态管理接口；
* 通信状态可观测与扩展接口；
* 电源管理 / 电量监测 / 告警 / 保护相关接口；
* 补光接入与控制接口；
* 部署迁移 / 配置管理辅助接口；
* 新传感器 / 新功能模块 / 迭代二增强能力接入接口。

建议在后续版本逐步考虑补充：

* `/p0/power/status`
* `/p0/lighting/control`
* `/p0/comm/status`
* `/p0/system/version_info`

----------------------------------------

# 11. 待统一与待确认项

以下内容在 V0.1 中明确标记为待统一：

1. `QuerySemanticPose.srv` 与 `GetSemanticPose.srv` 的最终命名统一；
2. `TriggerEmergencyStop.srv` 的最终服务方归属是 `p0_safety_manager` 还是 `p0_system_manager`；
3. `/p0/navigation/go_to_pose` 是否直接采用 Nav2 标准动作，还是由 `p0_navigation` 再封装一层；
4. `NavigateToSemantic.action` 的服务方归属是 `p0_navigation`、`p0_semantic_nav` 还是 `p0_task_manager`；
5. 部分 Topic 的标准消息类型选型与最终字段（如 odom、pose、path 等）在 P2-P4 联调中进一步确认。

----------------------------------------

# 12. 维护规则

## 12.1 版本管理

本文件采用增量维护方式：

* V0.1：P1 骨架版，建立统一接口骨架；
* V0.2：P2-P3 联调版，补齐底盘、建图、定位关键接口；
* V0.3：P4-P5 导航任务版，补齐语义导航与任务调度接口；
* V1.0：P6 验收版，冻结迭代一正式接口清单。

## 12.2 修改原则

后续修改应遵循：

* 优先新增字段，避免随意破坏既有接口；
* 优先保持命名统一与前向兼容；
* 自定义结构优先沉淀到 `p0_interfaces`；
* 每次接口变更应对应一条 CHANGELOG 条目，并与版本路线图对齐。

## 12.3 与后续文档协同

本文件后续应与以下文档联动更新：

* `docs/03_design/` 各模块详细设计文档；
* `docs/04_deployment/` 部署与运行文档；
* `docs/06_testing/` 测试计划、验收标准与测试记录；
* `hardware/wiring/` 接线图与相关物理接口说明；

----------------------------------------

# 13. 附：本版最小自定义接口骨架示例（占位）

> 以下仅为骨架占位，后续在 `src/p0_interfaces/msg|srv|action/` 中落地。

## 13.1 ChassisCmd.msg（占位）

```text
# TODO: 线速度、角速度、时间戳、控制模式等字段后续细化
```

## 13.2 ChassisStatus.msg（占位）

```text
# TODO: 编码器、左右轮速度、电压、通信状态、故障码等字段后续细化
```

## 13.3 SystemStatus.msg（占位）

```text
# TODO: 当前模式、模块在线状态、系统故障等级、时间戳等字段后续细化
```

## 13.4 SafetyEvent.msg（占位）

```text
# TODO: 事件类型、等级、来源模块、时间戳、描述等字段后续细化
```

## 13.5 LocalizationStatus.msg（占位）

```text
# TODO: 定位质量枚举（Good / Degraded / Lost）、时间戳、附加说明
```

## 13.6 SetSystemMode.srv（占位）

```text
# Request:
#   target_mode
# Response:
#   success
#   message
```

## 13.7 TriggerEmergencyStop.srv（占位）

```text
# Request:
#   enable
# Response:
#   success
#   message
```

## 13.8 NavigateToSemantic.action（占位）

```text
# Goal:
#   semantic_name
# Feedback:
#   progress / current_state
# Result:
#   success / fail_reason
```

----------------------------------------

# 14. 总结

本文档作为 `interface_definition.md` 骨架版 V0.1，已经在软件架构给出的接口组织原则、架构级接口关系、建议版话题/服务/动作接口与 `p0_interfaces` 初始接口清单基础上，整理出面向迭代一最小闭环的具体接口定义表骨架，用于支撑后续 P2-P6 的模块设计、实现、联调、测试与验收。[2][3][4][5][10][14][17][18]
```