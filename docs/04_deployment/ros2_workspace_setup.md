# ROS2 工作区与基础环境搭建

## P1.4-1 ROS2 Humble 基础环境记录

记录日期：2026-06-03

本节记录 Orin NX 在 P1.4 工程环境搭建阶段的 ROS2 Humble 基础安装与最小通信验证结果。本文只记录已经完成的基础环境动作，不表示 FAST-LIO2、Nav2、Livox 驱动、RealSense 驱动、仿真环境或正式 ROS2 工作区功能包已经完成。

### 1. 安装前状态

安装前已确认：

| 项目 | 当前记录 |
| --- | --- |
| 主机名 | `gdsdc-desktop` |
| 系统版本 | Ubuntu 22.04.5 LTS / jammy |
| 架构 | `aarch64` / `arm64` |
| 远程访问 | SSH 可用，Orin NX 已可按 headless 模式使用 |
| locale | `LANG=zh_CN.UTF-8`，`LC_ALL` 为空 |
| apt 源 | Ubuntu ports 与 NVIDIA Jetson r36.4 源可正常更新 |

安装前 `sudo apt update` 正常完成，并提示仍有大量系统软件包可升级。当前记录不执行整机 `apt upgrade`，避免在 Jetson / L4T 镜像上引入无边界系统变化。

### 2. ROS2 apt 源配置

已安装基础工具并启用 `universe`：

```bash
sudo apt install software-properties-common curl -y
sudo add-apt-repository universe
sudo apt update
```

GitHub 连通性检查通过：

```bash
curl -I https://github.com
```

返回过 `HTTP/2 200`。

按 ROS2 官方推荐方式安装 `ros2-apt-source`：

```bash
export ROS_APT_SOURCE_VERSION=$(curl -s https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest | grep -F "tag_name" | awk -F'"' '{print $4}')
echo $ROS_APT_SOURCE_VERSION
curl -L -o /tmp/ros2-apt-source.deb "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.$(. /etc/os-release && echo ${UBUNTU_CODENAME:-${VERSION_CODENAME}})_all.deb"
sudo dpkg -i /tmp/ros2-apt-source.deb
sudo apt update
```

本次记录中 `ROS_APT_SOURCE_VERSION` 为：

```text
1.2.0
```

`sudo apt update` 已成功拉取 `http://packages.ros.org/ros2/ubuntu jammy` 的 sources 与 `arm64` packages。

### 3. ROS2 Humble 基础安装

已安装 ROS2 Humble 基础版与开发工具：

```bash
sudo apt install ros-humble-ros-base ros-dev-tools -y
```

说明：

1. 当前选择 `ros-humble-ros-base`，不是 `ros-humble-desktop`。
2. 这是为了先建立轻量、可验证的 ROS2 基线。
3. RViz、Gazebo、Nav2、FAST-LIO2、Livox 驱动、RealSense 驱动等后续按阶段需要再补，不在本节写成已完成。

### 4. 基础验证

已执行：

```bash
source /opt/ros/humble/setup.bash
ros2 pkg list | head
printenv ROS_DISTRO
```

验证结果：

1. `ros2 pkg list` 可列出 ROS2 包，例如 `action_msgs`、`ament_cmake` 等。
2. `printenv ROS_DISTRO` 输出 `humble`。
3. `ros2 --version` 在 Humble 中不是有效参数；该命令显示 usage 和 `unrecognized arguments: --version` 不作为安装失败判断。
4. `ros2 pkg list | head` 出现过 `BrokenPipeError`，这是 `head` 提前关闭管道导致的输出中断，不作为 ROS2 安装失败判断。

已执行：

```bash
ros2 doctor --report
```

关键结果：

| 项目 | 当前记录 |
| --- | --- |
| ROS distribution | `humble` |
| Distribution type | `ros2` |
| Release platform | Ubuntu jammy |
| RMW middleware | `rmw_fastrtps_cpp` |
| 网络接口 | `lo`、`wlP1p1s0`、`enP8p1s0`、`l4tbr0`、`usb0`、`usb1` |
| 当前 Wi-Fi IPv4 | `10.40.146.23` |

`ros2 doctor --report` 出现过 `Fail to call PackageReport class functions` warning。当前基础通信验证已通过，因此该 warning 先记录为待观察项，不作为 P1.4-1 阻断问题。

### 5. demo 节点安装与 talker/listener 验证

初次检查：

```bash
ros2 pkg list | grep demo_nodes
```

未发现 demo 包，因此已安装：

```bash
sudo apt install ros-humble-demo-nodes-cpp ros-humble-demo-nodes-py -y
```

安装内容包括：

1. `ros-humble-example-interfaces`
2. `ros-humble-demo-nodes-cpp`
3. `ros-humble-demo-nodes-py`

随后已完成 `demo_nodes_cpp` 的 talker/listener 最小通信测试。测试方式为两个 SSH 窗口分别运行：

```bash
source /opt/ros/humble/setup.bash
ros2 run demo_nodes_cpp talker
```

```bash
source /opt/ros/humble/setup.bash
ros2 run demo_nodes_cpp listener
```

用户确认测试成功。

### 6. shell 环境加载

talker/listener 测试成功后，已执行：

```bash
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
source ~/.bashrc
printenv ROS_DISTRO
```

目的：让后续 SSH 登录后默认加载 ROS2 Humble 环境。

### 7. 当前结论

P1.4-1 ROS2 Humble 基础环境已完成最小验证：

1. ROS2 apt 源已添加；
2. `ros-humble-ros-base` 与 `ros-dev-tools` 已安装；
3. ROS2 Humble 环境变量可用；
4. `ros2 doctor --report` 可识别 Humble、平台和 RMW；
5. `demo_nodes_cpp` talker/listener 最小通信测试已成功；
6. Orin NX 可继续按 headless + SSH 方式推进后续环境搭建。

下一步建议进入 P1.4-2：ROS2 工作区骨架创建与 `colcon build` 验证。该步骤只应创建基础 workspace 和示例 / 空包，不提前展开正式控制、SLAM、导航或传感器驱动实现。


