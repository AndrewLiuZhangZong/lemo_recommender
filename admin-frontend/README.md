# Lemo推荐系统 - 管理后台

## 功能特性

- 🎛️ **仪表板**: 核心指标展示、趋势图表
- ⚙️ **场景管理**: 场景CRUD、配置管理
- 📦 **物品管理**: 物品CRUD、批量导入
- 🧪 **AB实验**: 实验创建、启动/停止、结果查看
- 📊 **数据分析**: 物品分布、用户行为分析

## 快速开始

### 安装依赖

```bash
cd admin-frontend
npm install
```

### 启动开发服务器

```bash
npm run dev
```

访问: http://localhost:3000

### 构建生产版本

```bash
npm run build
```

## 技术栈

- **Vue 3** - 前端框架
- **Element Plus** - UI组件库
- **Vue Router** - 路由管理
- **Pinia** - 状态管理
- **Axios** - HTTP客户端
- **ECharts** - 数据可视化
- **Vite** - 构建工具

## 目录结构

```
admin-frontend/
├── src/
│   ├── views/          # 页面组件
│   │   ├── Layout.vue
│   │   ├── Dashboard.vue
│   │   ├── Scenarios.vue
│   │   ├── Items.vue
│   │   ├── Experiments.vue
│   │   └── Analytics.vue
│   ├── api/            # API接口
│   │   └── index.js
│   ├── router/         # 路由配置
│   │   └── index.js
│   ├── App.vue
│   └── main.js
├── index.html
├── vite.config.js
└── package.json
```

## API配置

默认API地址: `http://localhost:8080/api/v1`

可在 `src/api/index.js` 中修改租户ID和用户ID。

## 使用说明

### 1. 场景管理

- 创建新场景（vlog、news、ecommerce等）
- 编辑场景配置
- 删除场景

### 2. 物品管理

- 单个物品创建
- 批量导入（JSON格式）
- 按场景筛选

### 3. AB实验

- 创建实验（配置变体、流量分配）
- 启动/停止实验
- 查看实验结果（CTR、显著性检验）

### 4. 数据分析

- 物品分类分布（饼图）
- 用户活跃时段（柱状图）
- 可选时间范围

## 注意事项

- 确保后端服务已启动（端口8080）
- 默认租户ID: `demo_tenant`
- 需要配置CORS允许前端访问

## 未来扩展

- [ ] 用户权限管理
- [ ] 更多图表类型
- [ ] 实时数据刷新
- [ ] 导出报表功能
- [ ] 场景配置可视化编辑器

