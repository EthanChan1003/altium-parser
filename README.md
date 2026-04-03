# Altium Designer 工程文件解析器 - 操作文档

## 目录

- [1. 简介](#1-简介)
- [2. 环境准备](#2-环境准备)
- [3. 安装解析器](#3-安装解析器)
- [4. 命令行使用](#4-命令行使用)
- [5. 支持的文件类型](#5-支持的文件类型)
- [6. 输出格式说明](#6-输出格式说明)
- [7. 完整使用示例](#7-完整使用示例)
- [8. JSON 输出结构详解](#8-json-输出结构详解)
- [9. XML 输出结构详解](#9-xml-输出结构详解)
- [10. 高级用法](#10-高级用法)
- [11. Python API 调用](#11-python-api-调用)
- [12. 运行测试](#12-运行测试)
- [13. 常见问题](#13-常见问题)
- [14. 项目结构](#14-项目结构)

---

## 1. 简介

本工具是一个 **Altium Designer 工程源文件解析器**，能够解析 Altium Designer 生成的全部工程文件类型（`.PrjPcb`、`.SchDoc`、`.PcbDoc`、`.SchLib`、`.PcbLib`），提取其中的元器件、网络、走线、图层、封装、过孔等完整信息及详细坐标参数，并输出为规范化的 **JSON** 和/或 **XML** 格式。

### 核心能力

| 能力 | 说明 |
|------|------|
| 原理图解析 | 元器件、位号、引脚、走线、网络标签、电源端口、图形元素，含完整坐标 |
| PCB 解析 | 板框、层叠结构、元器件、走线、圆弧、焊盘、过孔、网络、铜皮、设计规则、3D模型引用，含完整坐标 |
| 库文件解析 | 原理图符号库、PCB 封装库的完整图元定义 |
| 工程文件解析 | 工程引用的所有子文档列表 |
| 双格式输出 | JSON 和 XML，可同时输出 |
| 可视化查看 | 内置 PCB Viewer 网页版可视化工具 |

---

## 2. 环境准备

### 2.1 安装 Python

本工具需要 **Python 3.10 或更高版本**。

**Windows 安装步骤：**

1. 访问 Python 官网下载页面：https://www.python.org/downloads/
2. 下载 Python 3.10+ 的 Windows 安装包（推荐 3.12）
3. 运行安装程序时，**务必勾选** "Add Python to PATH"（添加到系统环境变量）
4. 安装完成后，打开命令提示符（cmd）或 PowerShell，验证安装：

```bash
python --version
# 应输出: Python 3.12.x (或你安装的版本)

pip --version
# 应输出: pip 24.x.x from ...
```

> **注意**：如果你的系统显示 Python 版本但执行报错或跳转到 Microsoft Store，说明当前的 Python 是 Windows Store 占位符，需要按上述步骤重新安装真正的 Python。

### 2.2 确认 pip 可用

```bash
pip --version
```

如果 pip 不可用，运行：

```bash
python -m ensurepip --upgrade
```

---

## 3. 安装解析器

### 3.1 开发模式安装（推荐）

打开命令提示符，切换到 `parser` 目录，执行安装：

```bash
# 切换到 parser 目录
cd X:\your-own-path\parser

# 以开发模式安装（-e 表示 editable，修改代码后无需重新安装）
pip install -e .
```

安装成功后会自动：
- 安装唯一的外部依赖 `olefile`（用于读取 Altium 的 OLE 复合文档格式）
- 注册 `altium-parser` 命令到系统 PATH

### 3.2 验证安装

```bash
altium-parser --version
# 应输出: altium-parser 1.0.0

altium-parser --help
# 应输出完整的帮助信息
```

### 3.3 安装测试依赖（可选）

如果你需要运行单元测试：

```bash
pip install -e ".[dev]"
```

这会额外安装 `pytest` 测试框架。

---

## 4. 命令行使用

### 4.1 基本语法

```
altium-parser <输入文件> [选项]
```

### 4.2 完整参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `<输入文件>` | Altium 文件路径（必填） | - |
| `-o, --output <路径>` | 指定输出文件路径 | 与输入文件同目录，扩展名为 `.json` 或 `.xml` |
| `-f, --format <格式>` | 输出格式：`json`、`xml`、`both` | `json` |
| `--pretty` | 美化输出（带缩进换行） | 默认开启 |
| `--compact` | 紧凑输出（无缩进，单行） | 关闭 |
| `--log-level <级别>` | 日志级别：`DEBUG`、`INFO`、`WARNING`、`ERROR` | `INFO` |
| `--dump-structure` | 仅打印 OLE 文件内部结构（调试用） | 关闭 |
| `--version` | 显示版本号 | - |
| `-h, --help` | 显示帮助信息 | - |

---

## 5. 支持的文件类型

| 扩展名 | 文件类型 | 说明 |
|--------|---------|------|
| `.PrjPcb` | 工程文件 | 纯文本 INI 格式，列出工程中所有子文档的引用路径 |
| `.SchDoc` | 原理图文档 | OLE 二进制格式，包含电路原理图的全部信息 |
| `.PcbDoc` | PCB 文档 | OLE 二进制格式，包含 PCB 布局布线的全部信息 |
| `.SchLib` | 原理图符号库 | OLE 二进制格式，包含原理图符号定义 |
| `.PcbLib` | PCB 封装库 | OLE 二进制格式，包含 PCB 封装定义 |

---

## 6. 输出格式说明

所有输出文件都包含一个统一的信封结构：

**JSON 信封：**
```json
{
  "schema_version": "1.0",
  "generator": "altium-parser",
  "file_type": "SchDoc",
  "source_file": "原始文件名.SchDoc",
  "data": { ... }
}
```

**XML 信封：**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<altium-document schema-version="1.0" generator="altium-parser"
                 file-type="SchDoc" source-file="原始文件名.SchDoc">
  ...
</altium-document>
```

- `schema_version` — 输出格式版本号，便于后续兼容性管理
- `generator` — 生成工具标识
- `file_type` — 原始文件类型
- `source_file` — 原始文件名
- `data` — 解析出的完整数据

**坐标单位**：所有坐标值默认输出为 **毫米（mm）**。

---

## 7. 完整使用示例

### 7.1 解析原理图文件，输出 JSON

```bash
altium-parser C:\MyProject\TopSheet.SchDoc
```

输出文件：`C:\MyProject\TopSheet.json`

### 7.2 解析 PCB 文件，输出 JSON + XML 双格式

```bash
altium-parser C:\MyProject\Board.PcbDoc -f both
```

输出文件：
- `C:\MyProject\Board.json`
- `C:\MyProject\Board.xml`

### 7.3 指定输出路径

```bash
altium-parser C:\MyProject\Board.PcbDoc -o D:\Output\board_parsed.json
```

输出文件：`D:\Output\board_parsed.json`

### 7.4 解析原理图库

```bash
altium-parser C:\MyLibrary\Components.SchLib -f json
```

输出文件：`C:\MyLibrary\Components.json`

### 7.5 解析封装库

```bash
altium-parser C:\MyLibrary\Footprints.PcbLib -f both
```

### 7.6 解析工程文件

```bash
altium-parser C:\MyProject\Project.PrjPcb
```

输出：工程中引用的所有子文档列表及其类型。

### 7.7 紧凑输出（无缩进）

```bash
altium-parser Board.PcbDoc --compact
```

### 7.8 调试模式（详细日志）

```bash
altium-parser Board.PcbDoc --log-level DEBUG
```

### 7.9 查看文件内部 OLE 结构（调试用）

```bash
altium-parser Board.PcbDoc --dump-structure
```

输出示例：
```
OLE Structure: Board.PcbDoc
  Board6/Header (48 bytes)
  Board6/Data (2340 bytes)
  Tracks6/Header (48 bytes)
  Tracks6/Data (156780 bytes)
  Pads6/Header (48 bytes)
  Pads6/Data (89432 bytes)
  ...
```

---

## 8. JSON 输出结构详解

### 8.1 原理图（SchDoc）输出结构

```
{
  "schema_version": "1.0",
  "file_type": "SchDoc",
  "data": {
    "sheet": {                          // 图纸属性
      "size": "A4",                     //   纸张大小
      "width_mm": 297,                  //   宽度（mm）
      "height_mm": 210,                 //   高度（mm）
      "grid_size_mm": 2.54,             //   网格间距（mm）
      "title_block": {                  //   标题栏
        "title": "...",
        "date": "...",
        "revision": "...",
        "company": "...",
        "author": "..."
      }
    },
    "components": [{                    // 元器件列表
      "refdes": "U1",                   //   位号
      "lib_reference": "STM32F103",     //   库引用名
      "position": {"x_mm": ..., "y_mm": ...},  // 位置坐标
      "rotation": 0,                    //   旋转角度（度）
      "is_mirrored": false,             //   是否镜像
      "part_count": 1,                  //   子部件数量
      "description": "ARM MCU",         //   描述
      "source_library": "MyLib.SchLib", //   来源库
      "unique_id": "...",               //   唯一标识
      "pins": [{                        //   引脚列表
        "name": "PA0",                  //     引脚名称
        "number": "14",                 //     引脚编号
        "electrical_type": "bidirectional",  // 电气类型
        "position": {"x_mm": ..., "y_mm": ...},
        "orientation": 0,               //     方向（0=右,1=上,2=左,3=下）
        "length_mm": 2.54,              //     引脚长度
        "is_hidden": false              //     是否隐藏
      }],
      "parameters": [{                  //   参数/属性
        "name": "Value",
        "value": "STM32F103RBT6",
        "is_hidden": false
      }],
      "graphic_primitives": [...]       //   图形元素（矩形、线等）
    }],
    "wires": [{                         // 电气走线
      "points": [                       //   坐标点序列
        {"x_mm": 50.8, "y_mm": 25.4},
        {"x_mm": 76.2, "y_mm": 25.4}
      ]
    }],
    "net_labels": [{                    // 网络标签
      "name": "VCC",                    //   网络名称
      "position": {"x_mm": ..., "y_mm": ...},
      "orientation": 0
    }],
    "power_ports": [{                   // 电源端口
      "name": "GND",
      "style": "power_ground",          //   样式（arrow/bar/power_ground/...）
      "position": {"x_mm": ..., "y_mm": ...},
      "orientation": 1,
      "is_cross_sheet": false           //   是否跨图纸连接
    }],
    "junctions": [{...}],              // 节点（交叉点）
    "buses": [{...}],                  // 总线
    "bus_entries": [{...}],            // 总线入口
    "ports": [{...}],                  // 端口
    "polylines": [{...}],             // 多段线
    "polygons": [{...}],              // 多边形
    "rectangles": [{...}],            // 矩形
    "lines": [{...}],                 // 直线
    "arcs": [{...}],                  // 圆弧
    "ellipses": [{...}],              // 椭圆
    "texts": [{...}],                 // 文本
    "labels": [{...}],                // 标签
    "images": [{...}],                // 图片
    "sheet_symbols": [{...}],         // 层次图纸符号
    "statistics": {                    // 统计信息
      "total_records": 245,
      "unknown_records": 3,
      "component_count": 12,
      "wire_count": 38,
      "net_label_count": 15
    }
  }
}
```

### 8.2 PCB（PcbDoc）输出结构

```
{
  "schema_version": "1.0",
  "file_type": "PcbDoc",
  "data": {
    "board_outline": {                  // 板框轮廓
      "vertices": [                     //   顶点坐标序列
        {"x_mm": 0, "y_mm": 0},
        {"x_mm": 90, "y_mm": 0},
        {"x_mm": 90, "y_mm": 70},
        {"x_mm": 0, "y_mm": 70}
      ],
      "bounding_box": {                 //   包围盒
        "x1_mm": 0, "y1_mm": 0,
        "x2_mm": 90, "y2_mm": 70
      }
    },
    "layer_stackup": [{                 // 层叠结构
      "id": 1,                          //   层ID
      "name": "Top Layer",              //   层名称
      "copper_thickness_mm": 0.035,     //   铜厚（mm）
      "dielectric_constant": 4.2,       //   介电常数
      "dielectric_height_mm": 0.2,      //   介质厚度（mm）
      "material": "FR-4"               //   板材
    }],
    "nets": [{                          // 网络列表
      "id": 1,
      "name": "GND"
    }],
    "components": [{                    // 元器件放置
      "designator": "U1",              //   位号
      "comment": "STM32F103",          //   注释
      "footprint_name": "LQFP-64",    //   封装名称
      "position": {"x_mm": 45, "y_mm": 35},  // 放置位置
      "rotation": 0,                   //   旋转角度
      "layer": "top",                  //   所在层（top/bottom）
      "is_locked": false               //   是否锁定
    }],
    "tracks": [{                        // 走线
      "start": {"x_mm": 10, "y_mm": 10},    // 起点坐标
      "end": {"x_mm": 20, "y_mm": 10},      // 终点坐标
      "width_mm": 0.254,               //   线宽（mm）
      "layer": "Top Layer",            //   所在层
      "net": "VCC"                     //   所属网络
    }],
    "arcs": [{                          // 圆弧
      "center": {"x_mm": 15, "y_mm": 15},  // 圆心坐标
      "radius_mm": 5.0,               //   半径（mm）
      "start_angle": 0,               //   起始角度（度）
      "end_angle": 180,               //   终止角度（度）
      "width_mm": 0.254,              //   线宽（mm）
      "layer": "Top Layer",           //   所在层
      "net": "GND"                    //   所属网络
    }],
    "pads": [{                          // 焊盘
      "designator": "1",              //   焊盘编号
      "position": {"x_mm": 12, "y_mm": 12},
      "top_size": {"x_mm": 0.6, "y_mm": 1.2},   // 顶层焊盘尺寸
      "mid_size": {"x_mm": 0.6, "y_mm": 1.2},   // 中间层尺寸（通孔焊盘）
      "bottom_size": {"x_mm": 0.6, "y_mm": 1.2}, // 底层尺寸（通孔焊盘）
      "hole_size_mm": 0.8,            //   孔径（0=SMD 无孔）
      "hole_shape": "round",          //   孔形（round/square/slot）
      "shape": "rectangular",          //   焊盘形状
      "rotation": 0,
      "layer": "Multi-Layer",
      "net": "PA0",
      "pad_type": "through_hole",     //   类型（smd/through_hole）
      "is_plated": true               //   是否电镀
    }],
    "vias": [{                          // 过孔
      "position": {"x_mm": 15, "y_mm": 15},
      "diameter_mm": 0.6,             //   外径（mm）
      "hole_mm": 0.3,                 //   孔径（mm）
      "start_layer": "Top Layer",     //   起始层
      "end_layer": "Bottom Layer",    //   终止层
      "net": "GND",                   //   所属网络
      "is_tented_top": false,         //   顶层是否覆盖阻焊
      "is_tented_bottom": false       //   底层是否覆盖阻焊
    }],
    "fills": [{                         // 填充
      "corner1": {"x_mm": ..., "y_mm": ...},
      "corner2": {"x_mm": ..., "y_mm": ...},
      "rotation": 0,
      "layer": "Top Layer",
      "net": "GND"
    }],
    "regions": [{                       // 区域/铜皮
      "vertices": [...],              //   顶点序列
      "layer": "Top Layer",
      "net": "GND",
      "is_keepout": false             //   是否为禁布区
    }],
    "texts": [{                         // 文本
      "content": "U1",
      "position": {"x_mm": 44, "y_mm": 30},
      "height_mm": 1.0,
      "rotation": 0,
      "layer": "Top Overlay",
      "font": "stroke",              //   字体类型（stroke/truetype/barcode）
      "is_mirrored": false
    }],
    "polygon_pours": [{                 // 覆铜区域
      "net": "GND",
      "layer": "Top Layer",
      "vertices": [...],
      "pour_mode": "solid",           //   填充模式（solid/hatched/none）
      "clearance_mm": 0.254,
      "min_track_width_mm": 0.254
    }],
    "design_rules": [{                  // 设计规则
      "name": "Clearance",
      "rule_type": "Clearance",
      "value_mm": 0.15,
      "scope": "All",
      "priority": 1,
      "enabled": true
    }],
    "model_3d_refs": [{                 // 3D模型引用
      "name": "LQFP-64",               //   模型名称
      "file_path": "Models/LQFP-64.step", //   文件路径
      "rotation": {"x": 0, "y": 0, "z": 0}, //   旋转角度
      "offset_mm": {"x": 0, "y": 0, "z": 0}  //   偏移量
    }],
    "statistics": {                     // 统计信息
      "component_count": 25,
      "track_count": 1234,
      "pad_count": 340,
      "via_count": 89,
      "net_count": 56,
      "layer_count": 4
    }
  }
}
```

### 8.3 工程文件（PrjPcb）输出结构

```
{
  "schema_version": "1.0",
  "file_type": "PrjPcb",
  "data": {
    "version": "1.0",
    "documents": [                      // 工程包含的文档列表
      {"path": "TopSheet.SchDoc", "doc_type": "SchDoc"},
      {"path": "Board.PcbDoc", "doc_type": "PcbDoc"},
      {"path": "Components.SchLib", "doc_type": "SchLib"}
    ],
    "parameters": {...}                // 工程级参数
  }
}
```

### 8.4 原理图库（SchLib）输出结构

```
{
  "schema_version": "1.0",
  "file_type": "SchLib",
  "data": {
    "symbols": [{                       // 符号列表
      "name": "RES_0402",             //   符号名称
      "description": "0402 Resistor", //   描述
      "designator_prefix": "R",       //   位号前缀
      "part_count": 1,                //   子部件数
      "pins": [{...}],               //   引脚定义
      "parameters": [{...}],         //   参数
      "polylines": [{...}],          //   多段线图元
      "rectangles": [{...}],         //   矩形图元
      "arcs": [{...}],               //   圆弧图元
      "texts": [{...}],              //   文本
      "statistics": {
        "pin_count": 2,
        "primitive_count": 5
      }
    }],
    "statistics": {
      "symbol_count": 50
    }
  }
}
```

### 8.5 封装库（PcbLib）输出结构

```
{
  "schema_version": "1.0",
  "file_type": "PcbLib",
  "data": {
    "footprints": [{                    // 封装列表
      "name": "LQFP-64",              //   封装名称
      "description": "64-pin LQFP",   //   描述
      "height_mm": 1.6,               //   高度（mm）
      "pads": [{...}],               //   焊盘图元
      "tracks": [{...}],             //   走线图元
      "arcs": [{...}],               //   圆弧图元
      "texts": [{...}],              //   文本图元
      "regions": [{...}],            //   区域图元
      "parameters": {...},            //   封装参数
      "statistics": {
        "pad_count": 64,
        "track_count": 12
      }
    }],
    "statistics": {
      "footprint_count": 30
    }
  }
}
```

---

## 9. XML 输出结构详解

XML 与 JSON 内容一一对应，结构映射规则：

| JSON 结构 | XML 映射 |
|-----------|----------|
| 简单值（字符串/数字/布尔） | 元素属性（attribute） |
| 对象（`{}`） | 子元素（child element） |
| 数组（`[]`） | 重复子元素（以单数命名） |

**示例**：PCB 元器件的 XML 表示：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<altium-document schema-version="1.0" generator="altium-parser"
                 file-type="PcbDoc" source-file="Board.PcbDoc">
  <board-outline>
    <vertices>
      <vertex x-mm="0" y-mm="0" />
      <vertex x-mm="90" y-mm="0" />
    </vertices>
    <bounding-box x1-mm="0" y1-mm="0" x2-mm="90" y2-mm="70" />
  </board-outline>
  <layer-stackup>
    <layer id="1" name="Top Layer" copper-thickness-mm="0.035" material="FR-4" />
  </layer-stackup>
  <components>
    <component designator="U1" footprint-name="LQFP-64" rotation="0" layer="top">
      <position x-mm="45" y-mm="35" />
    </component>
  </components>
  <tracks>
    <track width-mm="0.254" layer="Top Layer" net="VCC">
      <start x-mm="10" y-mm="10" />
      <end x-mm="20" y-mm="10" />
    </track>
  </tracks>
</altium-document>
```

---

## 10. 高级用法

### 10.1 批量解析工程中的所有文件

先解析工程文件获取子文档列表，再逐一解析：

```bash
# 步骤 1：解析工程文件，得到子文档列表
altium-parser MyProject.PrjPcb -o project.json

# 步骤 2：根据列表中的文件路径逐一解析
altium-parser TopSheet.SchDoc -f both
altium-parser Board.PcbDoc -f both
altium-parser Components.SchLib -f both
```

### 10.2 批量解析脚本（Windows BAT）

创建 `parse_all.bat` 文件：

```bat
@echo off
set PROJECT_DIR=C:\MyProject
set OUTPUT_DIR=C:\MyProject\parsed

mkdir "%OUTPUT_DIR%" 2>nul

echo Parsing schematic...
altium-parser "%PROJECT_DIR%\TopSheet.SchDoc" -o "%OUTPUT_DIR%\TopSheet.json" -f json

echo Parsing PCB...
altium-parser "%PROJECT_DIR%\Board.PcbDoc" -o "%OUTPUT_DIR%\Board.json" -f json

echo Parsing libraries...
altium-parser "%PROJECT_DIR%\Components.SchLib" -o "%OUTPUT_DIR%\Components.json" -f json

echo Done! Output in %OUTPUT_DIR%
pause
```

### 10.3 批量解析脚本（PowerShell）

```powershell
$projectDir = "C:\MyProject"
$outputDir = "C:\MyProject\parsed"
New-Item -ItemType Directory -Force -Path $outputDir | Out-Null

Get-ChildItem $projectDir -Include *.SchDoc,*.PcbDoc,*.SchLib,*.PcbLib -Recurse | ForEach-Object {
    $outFile = Join-Path $outputDir ($_.BaseName + ".json")
    Write-Host "Parsing $($_.Name)..."
    altium-parser $_.FullName -o $outFile -f json
}

Write-Host "All files parsed to $outputDir"
```

### 10.4 使用 PCB Viewer 可视化工具

项目内置了一个基于 HTML5 Canvas 的 PCB 可视化查看器，可以直观地查看解析后的 PCB 数据。

**使用步骤：**

1. 解析 PCB 文件并输出 JSON 到 `viewer` 目录：
```bash
altium-parser Board.PcbDoc -o viewer/output.json -f json
```

2. 启动本地 HTTP 服务器（可选择任意方式）：
```bash
# 方式一：Python 内置服务器
cd viewer
python -m http.server 8080

# 方式二：Node.js（需安装 http-server）
npx http-server viewer -p 8080
```

3. 打开浏览器访问：`http://localhost:8080`

**功能特性：**
- 图层控制：显示/隐藏走线、焊盘、过孔、圆弧、位号
- 图层过滤：按层筛选显示内容
- 交互操作：鼠标拖拽平移、滚轮缩放
- 实时坐标：显示鼠标位置的 PCB 坐标
- 颜色图例：不同层用不同颜色区分

---

## 11. Python API 调用

除了命令行使用，你也可以在 Python 脚本中直接调用解析器：

```python
from altium_parser.registry import parse_file, get_file_type
from altium_parser.serializers.json_serializer import serialize_to_json
from altium_parser.serializers.xml_serializer import serialize_to_xml

# --- 解析原理图 ---
sch_doc = parse_file("C:/MyProject/TopSheet.SchDoc")

# 访问元器件
for comp in sch_doc.components:
    print(f"位号: {comp.refdes}, 库引用: {comp.lib_reference}")
    print(f"  位置: ({comp.position.x_mm}, {comp.position.y_mm}) mm")
    print(f"  引脚数: {len(comp.pins)}")
    for pin in comp.pins:
        print(f"    {pin.number}: {pin.name} ({pin.electrical_type})")

# 访问走线
for wire in sch_doc.wires:
    coords = [(p.x_mm, p.y_mm) for p in wire.points]
    print(f"走线坐标: {coords}")

# 访问网络标签
for label in sch_doc.net_labels:
    print(f"网络: {label.name} at ({label.position.x_mm}, {label.position.y_mm})")


# --- 解析 PCB ---
pcb_doc = parse_file("C:/MyProject/Board.PcbDoc")

# 板框尺寸
bb = pcb_doc.board_outline.bounding_box
print(f"板子尺寸: {bb.x2_mm - bb.x1_mm} x {bb.y2_mm - bb.y1_mm} mm")

# 层叠信息
for layer in pcb_doc.layer_stackup:
    print(f"层 {layer.name}: 铜厚 {layer.copper_thickness_mm}mm, 材质 {layer.material}")

# 元器件
for comp in pcb_doc.components:
    print(f"{comp.designator}: {comp.footprint_name} at ({comp.position.x_mm}, {comp.position.y_mm})")

# 过孔统计
print(f"过孔总数: {len(pcb_doc.vias)}")
for via in pcb_doc.vias:
    print(f"  {via.net}: 外径{via.diameter_mm}mm, 孔径{via.hole_mm}mm")


# --- 导出为 JSON ---
json_str = serialize_to_json(pcb_doc, "PcbDoc", "Board.PcbDoc", "output.json")

# --- 导出为 XML ---
xml_str = serialize_to_xml(pcb_doc, "PcbDoc", "Board.PcbDoc", "output.xml")


# --- 转为 Python 字典 ---
data_dict = pcb_doc.to_dict()
# 现在可以用标准方式处理 data_dict
import json
print(json.dumps(data_dict, indent=2, ensure_ascii=False))
```

---

## 12. 运行测试

### 12.1 安装测试依赖

```bash
cd C:\Users\kingdee\Documents\EDA可视化单页原型\modular_v3\parser
pip install -e ".[dev]"
```

### 12.2 运行全部测试

```bash
pytest tests/ -v
```

### 12.3 运行单个测试文件

```bash
# 测试 KV 解析器
pytest tests/test_kv_parser.py -v

# 测试二进制读取器
pytest tests/test_binary_reader.py -v

# 测试单位转换
pytest tests/test_units.py -v

# 测试序列化器
pytest tests/test_json_serializer.py -v

# 测试数据模型
pytest tests/test_schdoc_parser.py -v
pytest tests/test_pcbdoc_parser.py -v
```

### 12.4 预期测试结果

```
tests/test_binary_reader.py    - 24 tests PASSED
tests/test_kv_parser.py        - 11 tests PASSED
tests/test_units.py            - 14 tests PASSED
tests/test_prjpcb_parser.py    -  3 tests PASSED
tests/test_json_serializer.py  -  5 tests PASSED (含 XML 测试)
tests/test_schdoc_parser.py    -  7 tests PASSED
tests/test_pcbdoc_parser.py    - 14 tests PASSED
tests/test_schlib_parser.py    -  2 tests PASSED
tests/test_pcblib_parser.py    -  2 tests PASSED
```

---

## 13. 常见问题

### Q1: 运行 `altium-parser` 报 "不是内部或外部命令"

**原因**：Python Scripts 目录不在系统 PATH 中。

**解决方法**：改用以下方式运行：
```bash
python -m altium_parser.cli Board.PcbDoc -f json
```

或者将 Python Scripts 目录添加到 PATH（通常是 `C:\Users\<用户名>\AppData\Local\Programs\Python\Python3x\Scripts`）。

### Q2: 解析报错 "Cannot open as OLE compound document"

**原因**：文件可能不是有效的 Altium 文件，或文件已损坏。

**排查方法**：
```bash
# 查看文件内部结构
altium-parser MyFile.SchDoc --dump-structure
```

### Q3: 输出中某些字段为空

**原因**：Altium 不同版本的文件格式存在差异，某些新版本的记录类型可能未被解析。

**排查方法**：
```bash
# 使用 DEBUG 日志查看解析过程
altium-parser MyFile.SchDoc --log-level DEBUG
```

日志会显示未识别的记录类型和跳过的数据。

### Q4: 如何升级解析器？

```bash
cd C:\Users\kingdee\Documents\EDA可视化单页原型\modular_v3\parser
pip install -e . --force-reinstall
```

### Q5: 如何卸载？

```bash
pip uninstall altium-parser
```

---

## 14. 项目结构

```
parser/
├── pyproject.toml                    # 项目配置和依赖声明
├── altium_parser/                    # 主包
│   ├── __init__.py                   # 版本号
│   ├── cli.py                        # 命令行入口
│   ├── registry.py                   # 文件类型 → 解析器调度
│   ├── core/                         # 核心基础设施
│   │   ├── exceptions.py             #   自定义异常
│   │   ├── constants.py              #   枚举常量（记录类型、图层ID等）
│   │   ├── units.py                  #   坐标单位转换
│   │   ├── binary_reader.py          #   二进制流读取器
│   │   ├── kv_parser.py              #   |KEY=VALUE 记录解析器
│   │   └── ole_reader.py             #   OLE 复合文档读取器
│   ├── models/                       # 数据模型
│   │   ├── common.py                 #   通用类型（Point2D, Color...）
│   │   ├── project.py                #   PrjPcb 模型
│   │   ├── schematic.py              #   SchDoc 模型
│   │   ├── pcb.py                    #   PcbDoc 模型
│   │   ├── schlib.py                 #   SchLib 模型
│   │   └── pcblib.py                 #   PcbLib 模型
│   ├── parsers/                      # 文件解析器
│   │   ├── prjpcb_parser.py          #   .PrjPcb 解析
│   │   ├── schdoc_parser.py          #   .SchDoc 解析
│   │   ├── pcbdoc_parser.py          #   .PcbDoc 解析
│   │   ├── schlib_parser.py          #   .SchLib 解析
│   │   └── pcblib_parser.py          #   .PcbLib 解析
│   └── serializers/                  # 输出序列化
│       ├── json_serializer.py        #   JSON 输出
│       └── xml_serializer.py         #   XML 输出
├── viewer/                           # PCB 可视化查看器
│   ├── index.html                    #   HTML5 Canvas 查看器
│   └── output.json                   #   示例输出数据
└── tests/                            # 单元测试
    ├── conftest.py                   #   共享测试夹具
    ├── test_binary_reader.py
    ├── test_kv_parser.py
    ├── test_units.py
    ├── test_prjpcb_parser.py
    ├── test_schdoc_parser.py
    ├── test_pcbdoc_parser.py
    ├── test_schlib_parser.py
    ├── test_pcblib_parser.py
    └── test_json_serializer.py
```
