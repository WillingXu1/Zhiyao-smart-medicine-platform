# Zhiyao smart medicine platform（智能医药电商平台）

## 📖 项目简介 (Introduction)
本项目是一个全栈式 O2O 医药健康服务平台，旨在打通患者、药店商家、平台管理之间的业务闭环。系统集成了 **AI 智能问诊**、**医药电商**等核心功能，为用户提供便捷的购药与健康咨询服务，同时赋能商家实现数字化经营。

<div align="center">
  <img src="./result/demo.gif" alt="智药核心功能演示" width="25%">
  <br/>
  <small><i>🎬 “智药”核心功能演示</i></small>
</div>


## 🚀 核心功能 (Core Features)

*   **👨‍⚕️ 用户端 (Customer Web)**
    *   **AI 智能问诊**：基于 Qwen2.5-1.5B LoRA 微调模型的医药咨询助手，结合 RAG 与风险分级约束，提升回答可靠性与安全性。
    *   **医药商城**：药品搜索、分类浏览、购物车、在线支付。
    *   **订单管理**：实时查看订单状态、物流轨迹、评价晒单。
    *   **个人中心**：收货地址管理、我的收藏、电子病历/处方管理。

*   **🏪 商家端 (Merchant Dashboard)**
    *   **商品管理**：药品上架、库存管理、价格调整。
    *   **订单处理**：接单、拒绝、发货、退款审核。
    *   **经营报表**：销售数据统计、热销商品分析。
    *   **门店设置**：营业状态切换、店铺信息维护。

*   **🛠 管理端 (Admin Panel)**
    *   **基础数据**：用户管理、商家入驻审核、药品分类管理。
    *   **运营中心**：Banner 轮播图、优惠券/营销活动管理。
    *   **系统监控**：审计日志、系统配置、角色权限控制 (RBAC)。


## 🛠 技术栈 (Tech Stack)

Spring Boot 3, Spring AI, Qwen2.5-1.5B (LoRA), RAG, Prompt Engineering, Redis, Minio, MyBatis-Plus

## 🧠 模型微调与安全增强 (Qwen2.5-1.5B LoRA)

1. **LoRA 微调与评测闭环**：基于 Qwen2.5-1.5B 构建“数据清洗 + 指令重构 + 检索增强”的训练体系，并设计评测闭环；针对医疗高风险问答优化模型幻觉，使幻觉率由 100% 降至 53.5%（内部下降 65.0%，外部下降 30.4%），显著提升模型输出可靠性。
2. **风险识别与分级约束**：在推理阶段引入风险识别与分级约束机制，通过拒答控制与人工兜底限制高风险输出，实现医疗场景下的可控生成与安全边界约束。
3. **医药垂直 RAG Pipeline**：构建分块、向量化、检索增强的一体化 RAG 流程，并结合 Prompt 约束注入证据片段，提升回答的事实一致性与可解释性。

### 🧠 模型服务接入（推荐远端 Qwen2.5-1.5B SFT）

* 推荐使用远端微调服务（OpenAI Compatible）：
    * `base-url`: `http://<server-ip>:8001`
    * `chat-path`: `/v1/chat/completions`
    * `model`: `qwen2.5-1.5b-medical-sft`
* 可选本地 Ollama 方案（开发调试）：
    * 安装 Ollama: https://ollama.com
    * 下载模型: `ollama pull qwen2.5:0.5b`
    * 启动服务: `ollama serve qwen2.5:0.5b --device cpu --threads 4`


### Backend (后端)
*   **核心框架**: Java 17, Spring Boot 3
*   **持久层**: MyBatis-Plus, MySQL 8.0
*   **缓存/消息**: Redis, WebSocket (实时消息)
*   **工具**: Knife4j (API 文档), Lombok, Hutool
*   **AI 集成**: Spring AI + OpenAI Compatible API (Qwen2.5-1.5B LoRA SFT)
*   **云服务**: 阿里云 OSS (文件存储)

### Frontend (前端)
*   **构建工具**: Vite, pnpm (Monorepo 架构)
*   **核心库**: React 18, TypeScript
*   **UI 组件库**: 
    *   **用户端/商家端**: Ant Design Mobile / Custom UI
    *   **管理端**: Ant Design Pro Components
*   **样式方案**: TailwindCSS, CSS Modules



## 🖼️项目实现图 (Project Implementation Diagram)

### 用户端运行截图

<div style="display: flex; flex-wrap: wrap;">
    <img src="./docs/img/web_user/home.png" alt="home" style="width: 25%; padding: 5px; box-sizing: border-box;">
    <img src="./docs/img/web_user/home2.png" alt="home2" style="width: 25%; padding: 5px; box-sizing: border-box;">
    <img src="./docs/img/web_user/medicines.png" alt="medicines" style="width: 25%; padding: 5px; box-sizing: border-box;">
    <img src="./docs/img/web_user/medicines1.png" alt="medicines" style="width: 25%; padding: 5px; box-sizing: border-box;">
    <img src="./docs/img/web_user/medicines2.png" alt="medicines" style="width: 25%; padding: 5px; box-sizing: border-box;">
    <img src="./docs/img/web_user/medicine1.png" alt="medicines" style="width: 25%; padding: 5px; box-sizing: border-box;">
    <img src="./docs/img/web_user/medicine2.png" alt="medicines" style="width: 25%; padding: 5px; box-sizing: border-box;">
    <img src="./docs/img/web_user/medicine-detail-add.png" alt="medicines" style="width: 25%; padding: 5px; box-sizing: border-box;">
    <img src="./docs/img/web_user/start.png" alt="start" style="width: 25%; padding: 5px; box-sizing: border-box;">
    <img src="./docs/img/web_user/medicine-detail-start.png" alt="medicines" style="width: 25%; padding: 5px; box-sizing: border-box;">
    <img src="./docs/img/web_user/buy-car.png" alt="buy-car" style="width: 25%; padding: 5px; box-sizing: border-box;">
    <img src="./docs/img/web_user/buy.png" alt="buy" style="width: 25%; padding: 5px; box-sizing: border-box;">
    <img src="./docs/img/web_user/order1.png" alt="order" style="width: 25%; padding: 5px; box-sizing: border-box;">
    <img src="./docs/img/web_user/order2.png" alt="order" style="width: 25%; padding: 5px; box-sizing: border-box;">
    <img src="./docs/img/web_user/user.png" alt="user" style="width: 25%; padding: 5px; box-sizing: border-box;">
    <img src="./docs/img/web_user/user2.png" alt="user" style="width: 25%; padding: 5px; box-sizing: border-box;">
    <img src="./docs/img/web_user/user3.png" alt="user" style="width: 25%; padding: 5px; box-sizing: border-box;">
    <img src="./docs/img/web_user/chat.png" alt="chat" style="width: 25%; padding: 5px; box-sizing: border-box;">
    <img src="./docs/img/web_user/chat2.png" alt="chat" style="width: 25%; padding: 5px; box-sizing: border-box;">
</div>


### 商家端运行截图

<div style="display: flex; flex-wrap: wrap;">
    <img src="./docs/img/web_merchant/home.png" alt="home" style="width: 25%; padding: 5px; box-sizing: border-box;">
    <img src="./docs/img/web_merchant/medicines-manger.png" alt="medicines-manger" style="width: 25%; padding: 5px; box-sizing: border-box;">
    <img src="./docs/img/web_merchant/medicines-upload.png" alt="medicines-upload" style="width: 25%; padding: 5px; box-sizing: border-box;">
    <img src="./docs/img/web_merchant/order-manger.png" alt="order" style="width: 25%; padding: 5px; box-sizing: border-box;">
    <img src="./docs/img/web_merchant/order-detail.png" alt="order" style="width: 25%; padding: 5px; box-sizing: border-box;">
    <img src="./docs/img/web_merchant/merchant.png" alt="merchant" style="width: 25%; padding: 5px; box-sizing: border-box;">
    <img src="./docs/img/web_merchant/merchant-setting.png" alt="merchant" style="width: 25%; padding: 5px; box-sizing: border-box;">
</div>


### 管理端运行截图

<div style="display: flex; flex-wrap: wrap;">
    <img src="./docs/img/web_admin/home.png" alt="home" style="width: 25%; padding: 5px; box-sizing: border-box;">
    <img src="./docs/img/web_admin/users.png" alt="users" style="width: 25%; padding: 5px; box-sizing: border-box;">
    <img src="./docs/img/web_admin/merchant.png" alt="merchant" style="width: 25%; padding: 5px; box-sizing: border-box;">
    <img src="./docs/img/web_admin/merchant-detail.png" alt="merchant-detail" style="width: 25%; padding: 5px; box-sizing: border-box;">
    <img src="./docs/img/web_admin/riders.png" alt="riders" style="width: 25%; padding: 5px; box-sizing: border-box;">
    <img src="./docs/img/web_admin/medicines.png" alt="medicines" style="width: 25%; padding: 5px; box-sizing: border-box;">
    <img src="./docs/img/web_admin/medicines-manger.png" alt="medicines-manger" style="width: 25%; padding: 5px; box-sizing: border-box;">
    <img src="./docs/img/web_admin/medicines-manger-detail.png" alt="medicines-manger-detail" style="width: 25%; padding: 5px; box-sizing: border-box;">
    <img src="./docs/img/web_admin/order1.png" alt="order1" style="width: 25%; padding: 5px; box-sizing: border-box;">
    <img src="./docs/img/web_admin/order2.png" alt="order2" style="width: 25%; padding: 5px; box-sizing: border-box;">
</div>


## 📂 项目结构 (Project Structure)

```
Zhiyao-System/
├── zhiyao-backend/                # 后端工程 (Maven 多模块)
│   ├── zhiyao-api       # 启动入口 & 全局配置
│   ├── zhiyao-application
│   ├── zhiyao-common
│   ├── zhiyao-domain
│   ├── zhiyao-infrastructure
│   └── ...
├── frontend/               # 前端工程
│   ├── apps/
│   │   ├── zhiyao-web-user        # 用户端 
│   │   ├── zhiyao-web-merchant    # 商家端 
│   │   └── zhiyao-web-admin       # 管理端
│   └── ...
└── docs/                   # 项目文档与 SQL 脚本
```

## ⚡️ 快速开始 (Quick Start)

### 1. 环境准备
*   JDK 17+
*   Node.js 18+ & pnpm
*   MySQL 8.0
*   Redis

### 2. 后端启动
```bash
cd zhiyao-backend
mvn clean package -DskipTests
java -jar zhiyao-start/target/zhiyao-start-0.0.1-beta-SNAPSHOT.jar
```
*   服务端口: `8080`
*   API 文档: `http://localhost:8080/doc.html`

### 3. 前端启动
```bash
cd frontend

# 启动用户端 (Port: 3000)
cd zhiyao-web-user
npm install
npm run dev

# 启动商家端 (Port: 3001)
cd zhiyao-web-merchant
npm install
npm run dev

# 启动管理端 (Port: 3002)
cd zhiyao-web-admin
npm install
npm run dev
```

## � 部署指南 (Deployment)

### 1. 生产环境配置 (Environment Variables)
在生产环境（如宝塔面板）中，建议通过环境变量配置敏感信息，无需修改代码：

| 变量名 | 描述 | 默认值/示例 |
| :--- | :--- | :--- |
| `DB_PASSWORD` | MySQL 数据库密码 | `123456` |
| `REDIS_PASSWORD` | Redis 密码 | 123321 |
| `OPENAI_API_KEY` | AI 服务 API Key | `sk-...` |
| `ALIYUN_OSS_ACCESS_KEY_ID` | 阿里云 OSS Key ID | - |
| `ALIYUN_OSS_ACCESS_KEY_SECRET` | 阿里云 OSS Secret | - |
| `ALIYUN_SMS_ACCESS_KEY_ID` | 阿里云短信 Key ID | - |
| `ALIYUN_SMS_ACCESS_KEY_SECRET` | 阿里云短信 Secret | - |

### 2. 后端部署 (Backend)
1.  **打包**: 在 `backend` 目录下运行 `mvn clean package -DskipTests`。
2.  **产物**: 获取 `backend/zhiyao-start/target/zhiyao-start-*.jar`。
3.  **运行**: 上传到服务器，使用命令启动：
    ```bash
    java -jar -Dspring.profiles.active=prod zhiyao-backend.jar
    ```

### 3. 前端部署 (Frontend)
1.  **构建**: 在 `frontend` 目录下运行 `npm run build:all`。
2.  **产物**: 
    *   管理端: `deploy/frontend/admin/`
    *   商家端: `deploy/frontend/merchant/`
    *   用户端: `deploy/frontend/customer/`
3.  **托管**: 将生成的静态文件上传到 Nginx/宝塔网站目录即可。


## �📝 许可证
本项目采用 MIT 许可证[LICENSE](https://github.com/WillingXu1/Zhiyao-smart-medicine-platform/blob/008818400c012259af068aafdc22d994bbf42eef/LICENSE)。


## 免责声明与用途说明

本项目用于学习研究、竞赛、课程设计与毕业设计，不具备商用资质，项目内的示例数据与资源仅作演示用途。

## 贡献指南

欢迎提交 PR 或 Issue 来优化本项目。

如有问题，可以有些邮箱联系我，也可以进行交流，项目不足之处，还请多多担待。

> **作者**: zxs
> **邮箱**: 2571293150@qq.com  
> **GitHub**: [[Zhiyao]](https://github.com/WillingXu1/Zhiyao-smart-medicine-platform.git)
