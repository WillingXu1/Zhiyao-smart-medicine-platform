/*
 Navicat Premium Dump SQL

 Source Server         : localhost
 Source Server Type    : MySQL
 Source Server Version : 80017 (8.0.17)
 Source Host           : localhost:3306
 Source Schema         : zhiyao

 Target Server Type    : MySQL
 Target Server Version : 80017 (8.0.17)
 File Encoding         : 65001

 Date: 27/12/2025 16:25:51
*/
-- table name : zhiyao
create schema zhiyao;


SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for address
-- ----------------------------
DROP TABLE IF EXISTS `address`;
CREATE TABLE `address`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `user_id` bigint(20) NOT NULL,
  `name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  `phone` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  `province` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  `city` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  `district` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  `detail` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  `is_default` tinyint(4) NULL DEFAULT 0,
  `create_time` datetime NULL DEFAULT NULL,
  `update_time` datetime NULL DEFAULT NULL,
  `deleted` tinyint(4) NULL DEFAULT 0,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 7 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for cart
-- ----------------------------
DROP TABLE IF EXISTS `cart`;
CREATE TABLE `cart`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '购物车ID',
  `user_id` bigint(20) NOT NULL COMMENT '用户ID',
  `merchant_id` bigint(20) NOT NULL COMMENT '商家ID',
  `medicine_id` bigint(20) NOT NULL COMMENT '药品ID',
  `quantity` int(11) NOT NULL DEFAULT 1 COMMENT '数量',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_user_medicine`(`user_id` ASC, `medicine_id` ASC) USING BTREE,
  INDEX `idx_user_id`(`user_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '购物车表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for consultation
-- ----------------------------
DROP TABLE IF EXISTS `consultation`;
CREATE TABLE `consultation`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `user_id` bigint(20) NULL DEFAULT NULL COMMENT '用户ID',
  `session_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '会话ID',
  `role` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '消息角色：user/assistant',
  `content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '消息内容',
  `consult_type` int(11) NULL DEFAULT 1 COMMENT '咨询类型：1-用药咨询',
  `create_time` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted` int(11) NULL DEFAULT 0,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_session_id`(`session_id` ASC) USING BTREE,
  INDEX `idx_user_id`(`user_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 21 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '用药咨询记录表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for delivery_exception
-- ----------------------------
DROP TABLE IF EXISTS `delivery_exception`;
CREATE TABLE `delivery_exception`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '异常ID',
  `order_id` bigint(20) NOT NULL COMMENT '订单ID',
  `rider_id` bigint(20) NOT NULL COMMENT '骑手ID',
  `type` tinyint(4) NOT NULL COMMENT '异常类型：1-无法联系用户 2-地址异常 3-其他',
  `description` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '异常描述',
  `images` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '图片凭证JSON',
  `status` tinyint(4) NOT NULL DEFAULT 0 COMMENT '状态：0-待处理 1-已处理',
  `handle_result` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '处理结果',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_order_id`(`order_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '配送异常表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for favorite
-- ----------------------------
DROP TABLE IF EXISTS `favorite`;
CREATE TABLE `favorite`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `user_id` bigint(20) NOT NULL,
  `medicine_id` bigint(20) NOT NULL,
  `create_time` datetime NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 5 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for medicine
-- ----------------------------
DROP TABLE IF EXISTS `medicine`;
CREATE TABLE `medicine`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '药品ID',
  `merchant_id` bigint(20) NOT NULL COMMENT '商家ID',
  `category_id` bigint(20) NULL DEFAULT NULL COMMENT '分类ID',
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '药品名称',
  `common_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '通用名',
  `image` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '主图',
  `images` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '图片列表JSON',
  `specification` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '规格',
  `manufacturer` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '生产厂家',
  `approval_number` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '批准文号',
  `price` decimal(10, 2) NOT NULL COMMENT '售价',
  `original_price` decimal(10, 2) NULL DEFAULT NULL COMMENT '原价',
  `stock` int(11) NOT NULL DEFAULT 0 COMMENT '库存',
  `sales` int(11) NULL DEFAULT 0 COMMENT '销量',
  `is_prescription` tinyint(4) NOT NULL DEFAULT 0 COMMENT '处方药：0-非处方 1-处方',
  `efficacy` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '功效说明',
  `dosage` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '用法用量',
  `adverse_reactions` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '不良反应',
  `contraindications` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '禁忌',
  `precautions` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '注意事项',
  `risk_tips` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '用药风险提示',
  `tags` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '标签JSON',
  `status` tinyint(4) NOT NULL DEFAULT 0 COMMENT '状态：0-下架 1-上架 2-审核中',
  `audit_status` tinyint(4) NOT NULL DEFAULT 0 COMMENT '审核状态：0-待审核 1-通过 2-拒绝',
  `audit_remark` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '审核备注',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted` tinyint(4) NOT NULL DEFAULT 0 COMMENT '删除标识',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_merchant_id`(`merchant_id` ASC) USING BTREE,
  INDEX `idx_category_id`(`category_id` ASC) USING BTREE,
  INDEX `idx_name`(`name` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 33 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '药品表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for medicine_category
-- ----------------------------
DROP TABLE IF EXISTS `medicine_category`;
CREATE TABLE `medicine_category`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '分类ID',
  `parent_id` bigint(20) NULL DEFAULT 0 COMMENT '父分类ID',
  `name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '分类名称',
  `icon` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '分类图标',
  `level` tinyint(4) NULL DEFAULT 1 COMMENT '层级',
  `sort` int(11) NULL DEFAULT 0 COMMENT '排序',
  `status` tinyint(4) NOT NULL DEFAULT 1 COMMENT '状态：0-禁用 1-启用',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted` tinyint(4) NOT NULL DEFAULT 0 COMMENT '删除标识',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_parent_id`(`parent_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 9 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '药品分类表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for merchant
-- ----------------------------
DROP TABLE IF EXISTS `merchant`;
CREATE TABLE `merchant`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '商家ID',
  `user_id` bigint(20) NOT NULL COMMENT '用户ID',
  `shop_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '店铺名称',
  `logo` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '店铺Logo',
  `cover_image` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '封面图',
  `contact_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '联系人姓名',
  `contact_phone` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '联系电话',
  `province` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '省份',
  `city` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '城市',
  `district` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '区县',
  `address` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '详细地址',
  `full_address` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '完整地址',
  `longitude` decimal(10, 7) NULL DEFAULT NULL COMMENT '经度',
  `latitude` decimal(10, 7) NULL DEFAULT NULL COMMENT '纬度',
  `business_license` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '营业执照号',
  `business_license_image` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '营业执照图片',
  `drug_license` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '药品经营许可证号',
  `drug_license_image` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '药品经营许可证图片',
  `open_time` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT '08:00' COMMENT '营业开始时间',
  `close_time` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT '22:00' COMMENT '营业结束时间',
  `delivery_fee` decimal(10, 2) NULL DEFAULT 0.00 COMMENT '配送费',
  `min_order_amount` decimal(10, 2) NULL DEFAULT 0.00 COMMENT '起送金额',
  `delivery_range` int(11) NULL DEFAULT 5 COMMENT '配送范围（公里）',
  `rating` decimal(2, 1) NULL DEFAULT 5.0 COMMENT '评分',
  `monthly_sales` int(11) NULL DEFAULT 0 COMMENT '月销量',
  `status` tinyint(4) NOT NULL DEFAULT 1 COMMENT '状态：0-关闭 1-营业中',
  `audit_status` tinyint(4) NOT NULL DEFAULT 0 COMMENT '审核状态：0-待审核 1-通过 2-拒绝',
  `audit_remark` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '审核备注',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted` tinyint(4) NOT NULL DEFAULT 0 COMMENT '删除标识',
  `description` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '店铺简介',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_user_id`(`user_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 9 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '商家表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for order_item
-- ----------------------------
DROP TABLE IF EXISTS `order_item`;
CREATE TABLE `order_item`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '订单项ID',
  `order_id` bigint(20) NOT NULL COMMENT '订单ID',
  `medicine_id` bigint(20) NOT NULL COMMENT '药品ID',
  `medicine_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '药品名称',
  `medicine_image` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '药品图片',
  `specification` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '规格',
  `price` decimal(10, 2) NOT NULL COMMENT '单价',
  `quantity` int(11) NOT NULL COMMENT '数量',
  `subtotal` decimal(10, 2) NOT NULL COMMENT '小计',
  `is_prescription` tinyint(4) NULL DEFAULT 0 COMMENT '是否处方药',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_order_id`(`order_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 38 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '订单项表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for orders
-- ----------------------------
DROP TABLE IF EXISTS `orders`;
CREATE TABLE `orders`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '订单ID',
  `order_no` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '订单编号',
  `user_id` bigint(20) NOT NULL COMMENT '用户ID',
  `merchant_id` bigint(20) NOT NULL COMMENT '商家ID',
  `rider_id` bigint(20) NULL DEFAULT NULL COMMENT '骑手ID',
  `address_id` bigint(20) NULL DEFAULT NULL COMMENT '地址ID',
  `receiver_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '收货人姓名',
  `receiver_phone` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '收货人手机号',
  `receiver_address` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '收货地址',
  `longitude` decimal(10, 7) NULL DEFAULT NULL COMMENT '经度',
  `latitude` decimal(10, 7) NULL DEFAULT NULL COMMENT '纬度',
  `total_amount` decimal(10, 2) NOT NULL COMMENT '商品总金额',
  `delivery_fee` decimal(10, 2) NULL DEFAULT 0.00 COMMENT '配送费',
  `discount_amount` decimal(10, 2) NULL DEFAULT 0.00 COMMENT '优惠金额',
  `pay_amount` decimal(10, 2) NOT NULL COMMENT '实付金额',
  `status` tinyint(4) NOT NULL DEFAULT 0 COMMENT '状态：0-待支付 1-待接单 2-拒单 3-待配送 4-配送中 5-已完成 6-已取消',
  `remark` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '订单备注',
  `preparation_note` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '备药说明',
  `reject_reason` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '拒单原因',
  `cancel_reason` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '取消原因',
  `pay_time` datetime NULL DEFAULT NULL COMMENT '支付时间',
  `accept_time` datetime NULL DEFAULT NULL COMMENT '接单时间',
  `rider_accept_time` datetime NULL DEFAULT NULL COMMENT '骑手接单时间',
  `delivery_start_time` datetime NULL DEFAULT NULL COMMENT '配送开始时间',
  `complete_time` datetime NULL DEFAULT NULL COMMENT '完成时间',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted` tinyint(4) NOT NULL DEFAULT 0 COMMENT '删除标识',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_order_no`(`order_no` ASC) USING BTREE,
  INDEX `idx_user_id`(`user_id` ASC) USING BTREE,
  INDEX `idx_merchant_id`(`merchant_id` ASC) USING BTREE,
  INDEX `idx_rider_id`(`rider_id` ASC) USING BTREE,
  INDEX `idx_status`(`status` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 36 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '订单表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for platform_config
-- ----------------------------
DROP TABLE IF EXISTS `platform_config`;
CREATE TABLE `platform_config`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '配置ID',
  `config_key` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '配置键',
  `config_value` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '配置值',
  `config_desc` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '配置说明',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_config_key`(`config_key` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 6 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '平台配置表' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Table structure for rider
-- ----------------------------
DROP TABLE IF EXISTS `rider`;
CREATE TABLE `rider`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '骑手ID',
  `user_id` bigint(20) NOT NULL COMMENT '用户ID',
  `real_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '真实姓名',
  `id_card` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '身份证号',
  `id_card_front` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '身份证正面',
  `id_card_back` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '身份证背面',
  `status` tinyint(4) NOT NULL DEFAULT 0 COMMENT '状态：0-离线 1-接单中',
  `audit_status` tinyint(4) NOT NULL DEFAULT 0 COMMENT '审核状态：0-待审核 1-通过 2-拒绝',
  `today_orders` int(11) NULL DEFAULT 0 COMMENT '今日订单数',
  `today_income` decimal(10, 2) NULL DEFAULT 0.00 COMMENT '今日收入',
  `total_orders` int(11) NULL DEFAULT 0 COMMENT '累计订单数',
  `total_income` decimal(10, 2) NULL DEFAULT 0.00 COMMENT '累计收入',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted` tinyint(4) NOT NULL DEFAULT 0 COMMENT '删除标识',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_user_id`(`user_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 6 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '骑手表' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Table structure for sys_user
-- ----------------------------
DROP TABLE IF EXISTS `sys_user`;
CREATE TABLE `sys_user`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '用户ID',
  `username` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '用户名',
  `password` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '密码',
  `phone` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '手机号',
  `email` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '邮箱',
  `nickname` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '昵称',
  `avatar` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '头像URL',
  `role` tinyint(4) NOT NULL DEFAULT 1 COMMENT '角色：1-用户 2-商家 3-管理员 4-骑手',
  `status` tinyint(4) NOT NULL DEFAULT 1 COMMENT '状态：0-禁用 1-启用',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted` tinyint(4) NOT NULL DEFAULT 0 COMMENT '删除标识：0-未删除 1-已删除',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_username`(`username` ASC) USING BTREE,
  UNIQUE INDEX `uk_phone`(`phone` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 39 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '用户表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for user_address
-- ----------------------------
DROP TABLE IF EXISTS `user_address`;
CREATE TABLE `user_address`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '地址ID',
  `user_id` bigint(20) NOT NULL COMMENT '用户ID',
  `receiver_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '收货人姓名',
  `receiver_phone` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '收货人手机号',
  `province` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '省份',
  `city` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '城市',
  `district` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '区县',
  `detail_address` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '详细地址',
  `full_address` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '完整地址',
  `longitude` decimal(10, 7) NULL DEFAULT NULL COMMENT '经度',
  `latitude` decimal(10, 7) NULL DEFAULT NULL COMMENT '纬度',
  `is_default` tinyint(4) NOT NULL DEFAULT 0 COMMENT '是否默认：0-否 1-是',
  `tag` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '标签',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted` tinyint(4) NOT NULL DEFAULT 0 COMMENT '删除标识',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_user_id`(`user_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '用户地址表' ROW_FORMAT = Dynamic;




-- 清空现有分类数据（可选）
TRUNCATE TABLE medicine_category;

-- 插入药品分类数据
INSERT INTO `medicine_category` (`id`, `parent_id`, `name`, `icon`, `level`, `sort`, `status`, `create_time`, `update_time`, `deleted`) VALUES
-- 第一级分类（主分类）
(1, 0, '感冒发烧', '', 1, 1, 1, NOW(), NOW(), 0),
(2, 0, '肠胃用药', '', 1, 2, 1, NOW(), NOW(), 0),
(3, 0, '皮肤用药', '', 1, 3, 1, NOW(), NOW(), 0),
(4, 0, '心脑血管', '', 1, 4, 1, NOW(), NOW(), 0),
(5, 0, '糖尿病用药', '', 1, 5, 1, NOW(), NOW(), 0),
(6, 0, '维生素', '', 1, 6, 1, NOW(), NOW(), 0),
(7, 0, '儿童用药', '', 1, 7, 1, NOW(), NOW(), 0),
(8, 0, '更多分类', '', 1, 8, 1, NOW(), NOW(), 0);


-- 插入药品数据
INSERT INTO `medicine` (
    `merchant_id`, `category_id`, `name`, `common_name`, `image`, `specification`,
    `manufacturer`, `approval_number`, `price`, `original_price`, `stock`, `sales`,
    `is_prescription`, `efficacy`, `dosage`, `adverse_reactions`, `contraindications`,
    `precautions`, `status`, `audit_status`
) VALUES
-- 1. 感冒发烧类药品
(1, 1, '连花清瘟胶囊', '连花清瘟胶囊', '/medicines/lianhuaqingwen.jpg', '0.35g*24粒',
 '以岭药业股份有限公司', '国药准字Z20040063', 25.80, 28.00, 100, 500, 0,
 '清瘟解毒，宣肺泄热。用于治疗流行性感冒属热毒袭肺证。', '口服。一次4粒，一日3次。',
 '偶见胃肠道不适、恶心、腹泻等。', '对本品及所含成分过敏者禁用。',
 '1. 忌烟、酒及辛辣、生冷、油腻食物。2. 不宜在服药期间同时服用滋补性中药。', 1, 1),

(1, 1, '布洛芬缓释胶囊', '布洛芬缓释胶囊', '/medicines/buluofen.jpg', '0.3g*20粒',
 '中美天津史克制药有限公司', '国药准字H20013062', 18.50, 22.00, 150, 800, 0,
 '用于缓解轻至中度疼痛如头痛、关节痛、偏头痛、牙痛、肌肉痛、神经痛、痛经。也用于普通感冒或流行性感冒引起的发热。',
 '成人一次1粒，一日2次（早晚各一次）。', '少数病人可出现恶心、呕吐、胃烧灼感或轻度消化不良、胃肠道溃疡及出血、转氨酶升高、头痛、头晕、耳鸣、视力模糊、精神紧张、嗜睡、下肢水肿或体重骤增。',
 '1. 对阿司匹林或其他非甾体抗炎药过敏者禁用。2. 孕妇及哺乳期妇女禁用。',
 '1. 本品为对症治疗药，不宜长期或大量使用。2. 不能同时服用其他含有解热镇痛药的药品。', 1, 1),

(1, 1, '999感冒灵颗粒', '感冒灵颗粒', '/medicines/999ganmaoling.jpg', '10g*9袋',
 '华润三九医药股份有限公司', '国药准字Z44021940', 15.60, 18.00, 200, 1200, 0,
 '解热镇痛。用于感冒引起的头痛，发热，鼻塞，流涕，咽痛。', '开水冲服。一次1袋，一日3次。',
 '偶见皮疹、荨麻疹、药热及粒细胞减少；长期大量用药会导致肝肾功能异常。',
 '严重肝肾功能不全者禁用。', '用药期间不宜驾驶车辆、管理机器及高空作业等。', 1, 1),

-- 2. 肠胃用药类药品
(1, 2, '蒙脱石散', '蒙脱石散', '/medicines/mengtuoshi.jpg', '3g*10袋',
 '博福-益普生(天津)制药有限公司', '国药准字H20000690', 28.00, 32.00, 80, 300, 0,
 '用于成人及儿童急、慢性腹泻。', '将本品倒入50毫升温水中，摇匀后服用。成人：一次1袋，一日3次。',
 '偶见便秘，大便干结。', '对本品过敏者禁用，过敏体质者慎用。',
 '治疗急性腹泻时，应注意纠正脱水。', 1, 1),

(1, 2, '奥美拉唑肠溶胶囊', '奥美拉唑肠溶胶囊', '/medicines/aomeilazuo.jpg', '20mg*14粒',
 '阿斯利康制药有限公司', '国药准字H20033500', 45.00, 50.00, 60, 200, 1,
 '适用于胃溃疡、十二指肠溃疡、应激性溃疡、反流性食管炎和卓-艾综合征(胃泌素瘤)。',
 '每日早晨吞服20mg，不可咀嚼。', '偶见头晕、失眠、嗜睡、恶心、腹泻、便秘、皮疹等。',
 '对本品过敏者、严重肾功能不全者禁用。', '治疗胃溃疡时，应首先排除溃疡型胃癌的可能。', 1, 1),

-- 3. 皮肤用药类药品
(1, 3, '莫匹罗星软膏', '莫匹罗星软膏', '/medicines/mopiluoxing.jpg', '5g:0.1g',
 '中美天津史克制药有限公司', '国药准字H10930064', 22.50, 25.00, 120, 400, 0,
 '用于革兰阳性球菌引起的皮肤感染，例如：脓疱病、疖肿、毛囊炎等原发性皮肤感染。',
 '局部涂于患处。必要时，患处可用敷料包扎或敷盖，每日3次，5天一疗程。',
 '局部应用一般无不良反应，偶见局部烧灼感、蜇刺感及瘙痒等。',
 '对本品及含聚乙二醇基质的其他软膏过敏者禁用。', '仅供皮肤给药，请勿用于眼、鼻、口等黏膜部位。', 1, 1),

(1, 3, '糠酸莫米松乳膏', '糠酸莫米松乳膏', '/medicines/kangsuanmomisong.jpg', '10g:10mg',
 '上海先灵葆雅制药有限公司', '国药准字H19991418', 19.80, 22.00, 90, 350, 0,
 '用于湿疹、神经性皮炎、异位性皮炎及皮肤瘙痒症。',
 '局部外用。取适量本品涂于患处，每日1次。',
 '使用本品的局部不良反应极少见，如烧灼感、瘙痒刺激和皮肤萎缩等。',
 '对本品任何成份过敏者禁用。', '不宜长期大量使用。', 1, 1),

-- 4. 心脑血管类药品
(1, 4, '阿司匹林肠溶片', '阿司匹林肠溶片', '/medicines/asipilin.jpg', '100mg*30片',
 '拜耳医药保健有限公司', '国药准字J20130078', 18.00, 20.00, 150, 600, 0,
 '降低急性心肌梗死疑似患者的发病风险；预防心肌梗死复发；中风的二级预防等。',
 '口服。肠溶片应饭前用适量水送服。',
 '较常见的有恶心、呕吐、上腹部不适或疼痛等胃肠道反应。',
 '对阿司匹林或其他水杨酸盐，或药品的任何其他成份过敏者禁用。',
 '与抗凝药同用时，可增加出血风险。', 1, 1),

(1, 4, '硝苯地平控释片', '硝苯地平控释片', '/medicines/xiaobendiping.jpg', '30mg*7片',
 '拜耳医药保健有限公司', '国药准字H20000079', 35.00, 40.00, 70, 250, 1,
 '用于治疗高血压、冠心病、慢性稳定型心绞痛(劳累性心绞痛)。',
 '整片吞服，不可掰开、压碎或咀嚼。',
 '常见下肢及踝部水肿、头晕、头痛、恶心、乏力和面部潮红。',
 '对硝苯地平或药品中任何成份过敏者禁用。',
 '服药期间必须经常监测血压，在开始用药、增加剂量时尤其注意。', 1, 1),

-- 5. 糖尿病用药类药品
(1, 5, '二甲双胍缓释片', '二甲双胍缓释片', '/medicines/erjiashuanggua.jpg', '0.5g*30片',
 '中美上海施贵宝制药有限公司', '国药准字H20023370', 28.50, 32.00, 100, 400, 1,
 '用于单纯饮食控制不满意的2型糖尿病患者。',
 '口服，进食时或餐后服。',
 '偶有恶心、呕吐、腹泻、口中有金属味。',
 '2型糖尿病伴有酮症酸中毒、肝及肾功能不全、心力衰竭、急性心肌梗死等情况禁用。',
 '定期检查肾功能，可以减少乳酸中毒的发生。', 1, 1),

-- 6. 维生素类药品
(1, 6, '维生素C泡腾片', '维生素C泡腾片', '/medicines/vitamin_c.jpg', '1g*20片',
 '拜耳医药保健有限公司', '国药准字H20090099', 25.00, 28.00, 200, 800, 0,
 '用于预防坏血病，也可用于各种急慢性传染疾病及紫癜等的辅助治疗。',
 '用温水冲服。成人，一日0.5-1g。',
 '长期服用每日2-3g可引起停药后坏血病。',
 '对本品过敏者禁用，过敏体质者慎用。',
 '不宜长期过量服用本品，否则，突然停药有可能出现坏血病症状。', 1, 1),

(1, 6, '维生素D滴剂', '维生素D滴剂', '/medicines/vitamin_d.jpg', '400单位*30粒',
 '青岛双鲸药业股份有限公司', '国药准字H20113033', 45.00, 50.00, 120, 350, 0,
 '用于预防和治疗维生素D缺乏症，如佝偻病等。',
 '口服。成人与儿童一日1-2粒。',
 '长期过量服用，可出现中毒，早期表现为骨关节疼痛、肿胀、皮肤瘙痒等。',
 '维生素D增多症、高钙血症、高磷血症伴肾性佝偻病患者禁用。',
 '对本品过敏者禁用，过敏体质者慎用。', 1, 1),

-- 7. 儿童用药类药品
(1, 7, '小儿氨酚黄那敏颗粒', '小儿氨酚黄那敏颗粒', '/medicines/xiaoeranfenhuangnamin.jpg', '4g*12袋',
 '哈药集团制药六厂', '国药准字H23023348', 12.50, 15.00, 150, 600, 0,
 '适用于缓解儿童普通感冒及流行性感冒引起的发热、头痛、四肢酸痛、打喷嚏、流鼻涕、鼻塞、咽痛等症状。',
 '温水冲服。1-3岁，一次0.5-1袋，一日3次。',
 '有时有轻度头晕、乏力、恶心、上腹不适、口干、食欲缺乏和皮疹等。',
 '严重肝肾功能不全者禁用。', '用药3-7天，症状未缓解，请咨询医师或药师。', 1, 1),

(1, 7, '布洛芬混悬液', '布洛芬混悬液', '/medicines/buluofen_hunxuanye.jpg', '100ml:2g',
 '上海强生制药有限公司', '国药准字H19991011', 28.00, 32.00, 80, 300, 0,
 '用于儿童普通感冒或流行性感冒引起的发热。也用于缓解儿童轻至中度疼痛。',
 '口服。需要时每6-8小时可重复使用，每24小时不超过4次。',
 '少数病人可出现恶心、呕吐、胃烧灼感或轻度消化不良、胃肠道溃疡及出血等。',
 '对阿司匹林或其他非甾体抗炎药过敏者禁用。',
 '本品为对症治疗药，不宜长期或大量使用。', 1, 1);


-- 先插入一个系统管理员用户
INSERT INTO `sys_user` (`username`, `password`, `phone`, `email`, `nickname`, `avatar`, `role`, `status`) VALUES
                                                                                                              ('admin', '$2a$10$6UhzLZwb9O.eX0/cOCMinO1mvz195Yf9KatyKEH0LqKphQp.LzofC', '13800138000', 'admin@zhiyao.com', '系统管理员', '/avatars/admin.png', 3, 1),

-- 插入一个商家用户
                                                                                                              ('merchant1', '$2a$10$6UhzLZwb9O.eX0/cOCMinO1mvz195Yf9KatyKEH0LqKphQp.LzofC', '13900139000', 'merchant1@zhiyao.com', '知药大药房', '/avatars/merchant1.png', 2, 1),

-- 插入一个普通用户
                                                                                                              ('user1', '$2a$10$6UhzLZwb9O.eX0/cOCMinO1mvz195Yf9KatyKEH0LqKphQp.LzofC', '13700137000', 'user1@example.com', '张先生', '/avatars/user1.png', 1, 1);

-- 插入商家信息（关联上面的商家用户）
INSERT INTO `merchant` (
    `user_id`, `shop_name`, `logo`, `contact_name`, `contact_phone`,
    `province`, `city`, `district`, `address`, `business_license`,
    `drug_license`, `delivery_fee`, `min_order_amount`, `delivery_range`,
    `status`, `audit_status`, `description`
) VALUES
    (2, '知药大药房旗舰店', '/shop/logo1.png', '李经理', '13900139000',
     '广东省', '深圳市', '南山区', '科技园南区1001号',
     '91440300MA5G9QW8XX', '粤AA44030500123',
     3.00, 20.00, 5, 1, 1, '24小时营业，专业药师在线咨询，30分钟送达');



-- 插入平台基础配置
INSERT INTO `platform_config` (`config_key`, `config_value`, `config_desc`) VALUES
                                                                                ('platform_name', '知药优选', '平台名称'),
                                                                                ('customer_service_phone', '400-123-4567', '客服电话'),
                                                                                ('delivery_free_threshold', '49.00', '免配送费门槛'),
                                                                                ('order_timeout_minutes', '15', '订单支付超时时间(分钟)'),
                                                                                ('refund_days', '7', '支持退换货天数');




-- 1. 用户地址表 (user_address)
INSERT INTO `user_address` (
    `user_id`, `receiver_name`, `receiver_phone`,
    `province`, `city`, `district`, `detail_address`, `full_address`,
    `longitude`, `latitude`, `is_default`, `tag`
) VALUES
      (3, '张三', '13700137000', '广东省', '深圳市', '南山区', '科技园南区1001号', '广东省深圳市南山区科技园南区1001号', 113.9538000, 22.5350000, 1, '家'),
      (3, '李四', '13700137001', '广东省', '深圳市', '福田区', '华强北路2008号', '广东省深圳市福田区华强北路2008号', 114.0833000, 22.5431000, 0, '公司');

-- 2. 购物车表 (cart)
INSERT INTO `cart` (`user_id`, `merchant_id`, `medicine_id`, `quantity`) VALUES
                                                                             (3, 1, 1, 2),  -- 用户3在商家1的购物车：连花清瘟胶囊 x2
                                                                             (3, 1, 2, 1),  -- 布洛芬缓释胶囊 x1
                                                                             (3, 1, 4, 3);  -- 蒙脱石散 x3

-- 3. 收藏表 (favorite)
INSERT INTO `favorite` (`user_id`, `medicine_id`, `create_time`) VALUES
                                                                     (3, 1, NOW()),  -- 用户3收藏连花清瘟胶囊
                                                                     (3, 5, NOW()),  -- 用户3收藏奥美拉唑肠溶胶囊
                                                                     (3, 8, NOW());  -- 用户3收藏阿司匹林肠溶片

-- 4. 骑手表 (rider)
INSERT INTO `rider` (
    `user_id`, `real_name`, `id_card`, `status`, `audit_status`
) VALUES
    (4, '王骑手', '440301199001011234', 1, 1);  -- 需要先添加骑手用户到sys_user表

-- 先添加骑手用户
INSERT INTO `sys_user` (`username`, `password`, `phone`, `nickname`, `role`) VALUES
    ('rider1', '$2a$10$6UhzLZwb9O.eX0/cOCMinO1mvz195Yf9KatyKEH0LqKphQp.LzofC', '13600136000', '王骑手', 4);

-- 5. 咨询记录表 (consultation) - 示例用药咨询
INSERT INTO `consultation` (`user_id`, `session_id`, `role`, `content`, `consult_type`) VALUES
                                                                                            (3, 'sess_001', 'user', '感冒发烧吃什么药比较好？', 1),
                                                                                            (3, 'sess_001', 'assistant', '建议使用连花清瘟胶囊或布洛芬缓释胶囊，具体用药请遵医嘱。', 1),
                                                                                            (3, 'sess_002', 'user', '胃不舒服应该吃什么药？', 1),
                                                                                            (3, 'sess_002', 'assistant', '可以尝试奥美拉唑肠溶胶囊，如症状持续请及时就医。', 1);

-- 6. 订单相关表 (orders + order_item) - 示例订单
INSERT INTO `orders` (
    `order_no`, `user_id`, `merchant_id`, `rider_id`, `address_id`,
    `receiver_name`, `receiver_phone`, `receiver_address`,
    `total_amount`, `delivery_fee`, `pay_amount`, `status`, `pay_time`
) VALUES
    ('ORDER202412270001', 3, 1, 1, 1,
     '张三', '13700137000', '广东省深圳市南山区科技园南区1001号',
     68.90, 3.00, 71.90, 5, NOW());

INSERT INTO `order_item` (`order_id`, `medicine_id`, `medicine_name`, `price`, `quantity`, `subtotal`) VALUES
                                                                                                           (1, 1, '连花清瘟胶囊', 25.80, 2, 51.60),
                                                                                                           (1, 2, '布洛芬缓释胶囊', 18.50, 1, 18.50);

-- 先清空表数据
TRUNCATE TABLE `medicine_category`;
TRUNCATE TABLE `medicine`;

-- 插入药品分类数据
INSERT INTO `medicine_category` (`id`, `parent_id`, `name`, `icon`, `level`, `sort`, `status`) VALUES
                                                                                                   (1, 0, '感冒发烧', '/icons/cold_fever.png', 1, 1, 1),
                                                                                                   (2, 0, '肠胃用药', '/icons/stomach_medicine.png', 1, 2, 1),
                                                                                                   (3, 0, '皮肤用药', '/icons/skin_medicine.png', 1, 3, 1),
                                                                                                   (4, 0, '心脑血管', '/icons/heart_vascular.png', 1, 4, 1),
                                                                                                   (5, 0, '糖尿病用药', '/icons/diabetes_medicine.png', 1, 5, 1),
                                                                                                   (6, 0, '维生素', '/icons/vitamin_orange.png', 1, 6, 1),
                                                                                                   (7, 0, '儿童用药', '/icons/baby_medicine.png', 1, 7, 1),
                                                                                                   (8, 0, '更多分类', '/icons/more_category.png', 1, 8, 1);


-- 插入药品数据，为每个分类添加5-8个真实药品
INSERT INTO `medicine` (`merchant_id`, `category_id`, `name`, `common_name`, `image`, `specification`, `manufacturer`, `price`, `original_price`, `stock`, `sales`, `is_prescription`, `efficacy`, `dosage`, `status`, `audit_status`) VALUES
-- 1. 感冒发烧类 (5个药品)
(1, 1, '连花清瘟胶囊', '连花清瘟胶囊', '/images/medicines/lianhuaqingwen.jpg', '0.35g*24粒', '以岭药业股份有限公司', 25.80, 28.00, 100, 500, 0, '清瘟解毒，宣肺泄热。用于治疗流行性感冒属热毒袭肺证。', '口服。一次4粒，一日3次。', 1, 1),
(1, 1, '布洛芬缓释胶囊', '布洛芬缓释胶囊', '/images/medicines/buluofen.jpg', '0.3g*20粒', '中美天津史克制药有限公司', 18.50, 22.00, 150, 800, 0, '用于缓解轻至中度疼痛如头痛、关节痛、偏头痛、牙痛、肌肉痛、神经痛、痛经。也用于普通感冒或流行性感冒引起的发热。', '成人一次1粒，一日2次（早晚各一次）。', 1, 1),
(1, 1, '999感冒灵颗粒', '感冒灵颗粒', '/images/medicines/999ganmaoling.jpg', '10g*9袋', '华润三九医药股份有限公司', 15.60, 18.00, 200, 1200, 0, '解热镇痛。用于感冒引起的头痛，发热，鼻塞，流涕，咽痛。', '开水冲服。一次1袋，一日3次。', 1, 1),
(1, 1, '复方氨酚烷胺片', '复方氨酚烷胺片', '/images/medicines/fufanganfenwanan.jpg', '12片', '哈药集团制药六厂', 12.80, 15.00, 180, 600, 0, '适用于缓解普通感冒及流行性感冒引起的发热、头痛、四肢酸痛、打喷嚏、流鼻涕、鼻塞、咽痛等症状。', '口服。成人，一次1片，一日2次。', 1, 1),
(1, 1, '阿莫西林胶囊', '阿莫西林胶囊', '/images/medicines/amoxilin.jpg', '0.25g*24粒', '珠海联邦制药股份有限公司', 16.50, 20.00, 120, 400, 0, '用于敏感菌所致的感染，如中耳炎、鼻窦炎、咽炎、扁桃体炎等上呼吸道感染。', '口服。成人一次0.5g，每6～8小时1次。', 1, 1),

-- 2. 肠胃用药类 (6个药品)
(1, 2, '蒙脱石散', '蒙脱石散', '/images/medicines/mengtuoshi.jpg', '3g*10袋', '博福-益普生(天津)制药有限公司', 28.00, 32.00, 80, 300, 0, '用于成人及儿童急、慢性腹泻。', '将本品倒入50毫升温水中，摇匀后服用。成人：一次1袋，一日3次。', 1, 1),
(1, 2, '奥美拉唑肠溶胶囊', '奥美拉唑肠溶胶囊', '/images/medicines/aomeilazuo.jpg', '20mg*14粒', '阿斯利康制药有限公司', 45.00, 50.00, 60, 200, 1, '适用于胃溃疡、十二指肠溃疡、应激性溃疡、反流性食管炎和卓-艾综合征(胃泌素瘤)。', '每日早晨吞服20mg，不可咀嚼。', 1, 1),
(1, 2, '多潘立酮片', '多潘立酮片', '/images/medicines/duopanlitong.jpg', '10mg*30片', '西安杨森制药有限公司', 22.00, 25.00, 100, 350, 0, '用于消化不良、腹胀、嗳气、恶心、呕吐、腹部胀痛。', '口服。成人一次1片，一日3-4次，饭前15-30分钟服用。', 1, 1),
(1, 2, '双歧杆菌三联活菌肠溶胶囊', '双歧杆菌三联活菌肠溶胶囊', '/images/medicines/shuangqiganjun.jpg', '210mg*24粒', '晋城海斯制药有限公司', 38.50, 42.00, 70, 150, 0, '用于肠道菌群失调引起的急慢性腹泻、便秘，也可用于治疗轻、中型急性腹泻，慢性腹泻及消化不良、腹胀。', '口服。成人一次2-4粒，一日2次。', 1, 1),
(1, 2, '铝碳酸镁咀嚼片', '铝碳酸镁咀嚼片', '/images/medicines/lutansuanmei.jpg', '0.5g*20片', '拜耳医药保健有限公司', 26.00, 30.00, 120, 280, 0, '用于急、慢性胃炎，胃、十二指肠溃疡，反流性食管炎，与胃酸有关的胃部不适症状。', '咀嚼后咽下。一次1-2片，一日3次。餐后1-2小时、睡前或胃部不适时服用。', 1, 1),
(1, 2, '黄连素片', '盐酸小檗碱片', '/images/medicines/huangliansu.jpg', '0.1g*100片', '天津力生制药股份有限公司', 8.50, 10.00, 200, 500, 0, '用于肠道感染，如胃肠炎。', '口服。成人：一次1-3片，一日3次。', 1, 1),

-- 3. 皮肤用药类 (6个药品)
(1, 3, '莫匹罗星软膏', '莫匹罗星软膏', '/images/medicines/mopiluoxing.jpg', '5g:0.1g', '中美天津史克制药有限公司', 22.50, 25.00, 120, 400, 0, '用于革兰阳性球菌引起的皮肤感染，例如：脓疱病、疖肿、毛囊炎等原发性皮肤感染。', '局部涂于患处。必要时，患处可用敷料包扎或敷盖，每日3次，5天一疗程。', 1, 1),
(1, 3, '糠酸莫米松乳膏', '糠酸莫米松乳膏', '/images/medicines/kangsuanmomisong.jpg', '10g:10mg', '上海先灵葆雅制药有限公司', 19.80, 22.00, 90, 350, 0, '用于湿疹、神经性皮炎、异位性皮炎及皮肤瘙痒症。', '局部外用。取适量本品涂于患处，每日1次。', 1, 1),
(1, 3, '红霉素软膏', '红霉素软膏', '/images/medicines/hongmeisu.jpg', '10g:100mg', '天津药业集团股份有限公司', 6.50, 8.00, 150, 600, 0, '用于脓疱疮等化脓性皮肤病、小面积烧伤、溃疡面的感染和寻常痤疮。', '局部外用。取适量本品涂于患处，一日2次。', 1, 1),
(1, 3, '炉甘石洗剂', '炉甘石洗剂', '/images/medicines/luganshi.jpg', '100ml', '北京双鹤药业股份有限公司', 12.00, 15.00, 100, 300, 0, '用于急性瘙痒性皮肤病，如荨麻疹和痱子。', '局部外用，用时摇匀，取适量涂于患处，每日2-3次。', 1, 1),
(1, 3, '曲安奈德益康唑乳膏', '曲安奈德益康唑乳膏', '/images/medicines/quannadide.jpg', '15g', '西安杨森制药有限公司', 28.00, 32.00, 80, 200, 0, '用于伴有真菌感染或有真菌感染倾向的皮炎、湿疹；由皮肤癣菌、酵母菌和霉菌所致的炎症性皮肤真菌病。', '局部外用。取适量本品涂于患处，每日早晚各1次。', 1, 1),
(1, 3, '阿昔洛韦乳膏', '阿昔洛韦乳膏', '/images/medicines/axiluowei.jpg', '10g:0.3g', '湖北科益药业股份有限公司', 15.00, 18.00, 110, 250, 0, '用于单纯疱疹或带状疱疹感染。', '局部外用。取适量本品涂患处，成人与小儿均为白天每2小时1次，一日6次，共7日。', 1, 1),

-- 4. 心脑血管类 (7个药品)
(1, 4, '阿司匹林肠溶片', '阿司匹林肠溶片', '/images/medicines/asipilin.jpg', '100mg*30片', '拜耳医药保健有限公司', 18.00, 20.00, 150, 600, 0, '降低急性心肌梗死疑似患者的发病风险；预防心肌梗死复发；中风的二级预防等。', '口服。肠溶片应饭前用适量水送服。', 1, 1),
(1, 4, '硝苯地平控释片', '硝苯地平控释片', '/images/medicines/xiaobendiping.jpg', '30mg*7片', '拜耳医药保健有限公司', 35.00, 40.00, 70, 250, 1, '用于治疗高血压、冠心病、慢性稳定型心绞痛(劳累性心绞痛)。', '整片吞服，不可掰开、压碎或咀嚼。', 1, 1),
(1, 4, '缬沙坦胶囊', '缬沙坦胶囊', '/images/medicines/xieshatan.jpg', '80mg*7粒', '北京诺华制药有限公司', 32.00, 36.00, 90, 200, 1, '治疗轻、中度原发性高血压。', '推荐剂量为80mg，每日一次。', 1, 1),
(1, 4, '苯磺酸氨氯地平片', '苯磺酸氨氯地平片', '/images/medicines/anlüdiping.jpg', '5mg*7片', '辉瑞制药有限公司', 28.50, 32.00, 85, 180, 1, '高血压、冠心病的治疗。', '通常口服起始剂量为5mg，每日一次。', 1, 1),
(1, 4, '单硝酸异山梨酯缓释片', '单硝酸异山梨酯缓释片', '/images/medicines/danxiaosuan.jpg', '40mg*20片', '珠海联邦制药股份有限公司', 42.00, 48.00, 60, 120, 1, '冠心病的长期治疗；心绞痛的预防。', '每日清晨服1片。', 1, 1),
(1, 4, '华法林钠片', '华法林钠片', '/images/medicines/hufalin.jpg', '2.5mg*60片', '上海信谊药厂有限公司', 45.00, 50.00, 50, 100, 1, '预防及治疗深静脉血栓及肺栓塞；预防心肌梗塞后血栓栓塞并发症。', '口服。避免冲击治疗，常用剂量：每日2.5mg-5mg。', 1, 1),
(1, 4, '氯吡格雷片', '硫酸氢氯吡格雷片', '/images/medicines/lübigelei.jpg', '75mg*7片', '赛诺菲(杭州)制药有限公司', 68.00, 75.00, 40, 80, 1, '预防动脉粥样硬化血栓形成事件，如近期心肌梗死、缺血性卒中。', '推荐剂量为每天75mg，与或不与食物同服。', 1, 1),

-- 5. 糖尿病用药类 (6个药品)
(1, 5, '二甲双胍缓释片', '二甲双胍缓释片', '/images/medicines/erjiashuanggua.jpg', '0.5g*30片', '中美上海施贵宝制药有限公司', 28.50, 32.00, 100, 400, 1, '用于单纯饮食控制不满意的2型糖尿病患者。', '口服，进食时或餐后服。', 1, 1),
(1, 5, '格列美脲片', '格列美脲片', '/images/medicines/geliemeiniai.jpg', '2mg*15片', '赛诺菲(北京)制药有限公司', 36.00, 40.00, 80, 200, 1, '用于2型糖尿病。', '起始剂量为每日1mg，每日1次。', 1, 1),
(1, 5, '阿卡波糖片', '阿卡波糖片', '/images/medicines/akabotang.jpg', '50mg*30片', '拜耳医药保健有限公司', 42.00, 48.00, 70, 150, 1, '配合饮食控制治疗2型糖尿病。', '用餐前即刻整片吞服或与前几口食物一起咀嚼服用。', 1, 1),
(1, 5, '瑞格列奈片', '瑞格列奈片', '/images/medicines/ruigelienai.jpg', '1mg*30片', '诺和诺德(中国)制药有限公司', 58.00, 65.00, 60, 120, 1, '用于饮食控制、降低体重及运动锻炼不能有效控制高血糖的2型糖尿病患者。', '通常在餐前15分钟内服用。推荐起始剂量为0.5mg。', 1, 1),
(1, 5, '西格列汀片', '磷酸西格列汀片', '/images/medicines/xigelieting.jpg', '100mg*7片', '默沙东制药有限公司', 85.00, 95.00, 40, 80, 1, '用于2型糖尿病。', '推荐剂量为100mg每日一次。', 1, 1),
(1, 5, '达格列净片', '达格列净片', '/images/medicines/dageliejing.jpg', '10mg*14片', '阿斯利康制药有限公司', 92.00, 105.00, 35, 60, 1, '用于2型糖尿病成人患者改善血糖控制。', '推荐起始剂量为5mg，每日一次，晨服。', 1, 1),

-- 6. 维生素类 (8个药品)
(1, 6, '维生素C泡腾片', '维生素C泡腾片', '/images/medicines/vitamin_c.jpg', '1g*20片', '拜耳医药保健有限公司', 25.00, 28.00, 200, 800, 0, '用于预防坏血病，也可用于各种急慢性传染疾病及紫癜等的辅助治疗。', '用温水冲服。成人，一日0.5-1g。', 1, 1),
(1, 6, '维生素D滴剂', '维生素D滴剂', '/images/medicines/vitamin_d.jpg', '400单位*30粒', '青岛双鲸药业股份有限公司', 45.00, 50.00, 120, 350, 0, '用于预防和治疗维生素D缺乏症，如佝偻病等。', '口服。成人与儿童一日1-2粒。', 1, 1),
(1, 6, '维生素B族片', '复合维生素B片', '/images/medicines/vitamin_b.jpg', '100片', '北京同仁堂科技发展股份有限公司', 28.00, 32.00, 150, 400, 0, '用于预防和治疗B族维生素缺乏所致的营养不良、厌食、脚气病、糙皮病等。', '口服。成人一次1-3片，一日3次。', 1, 1),
(1, 6, '维生素E软胶囊', '维生素E软胶囊', '/images/medicines/vitamin_e.jpg', '100mg*60粒', '养生堂药业有限公司', 36.00, 42.00, 100, 250, 0, '用于心、脑血管疾病及习惯性流产、不孕症的辅助治疗。', '口服。成人一次1粒，一日2-3次。', 1, 1),
(1, 6, '叶酸片', '叶酸片', '/images/medicines/yesusuan.jpg', '0.4mg*31片', '北京斯利安药业有限公司', 12.00, 15.00, 180, 300, 0, '预防胎儿先天性神经管畸形；妊娠期、哺乳期妇女预防用药。', '口服。育龄妇女从计划怀孕时起至怀孕后三个月末，一次0.4mg，一日一次。', 1, 1),
(1, 6, '维生素AD滴剂', '维生素AD滴剂', '/images/medicines/vitamin_ad.jpg', '10ml', '伊可新制药有限公司', 25.00, 30.00, 120, 280, 0, '用于预防和治疗维生素A及D的缺乏症。如佝偻病、夜盲症及小儿手足抽搐症。', '口服。1岁以下儿童，一次1粒，一日1次。', 1, 1),
(1, 6, '多维元素片', '多维元素片', '/images/medicines/duoweiyuansu.jpg', '30片', '惠氏制药有限公司', 85.00, 95.00, 80, 150, 0, '用于预防和治疗因维生素与矿物质缺乏所引起的各种疾病。', '口服。成人一日1片，饭时或饭后服用。', 1, 1),
(1, 6, '碳酸钙D3片', '碳酸钙D3片', '/images/medicines/tansuangai.jpg', '600mg*60片', '惠氏制药有限公司', 48.00, 55.00, 100, 200, 0, '用于妊娠和哺乳期妇女、更年期妇女、老年人等的钙补充剂。', '口服。一次1片，一日1-2次。', 1, 1),

-- 7. 儿童用药类 (6个药品)
(1, 7, '小儿氨酚黄那敏颗粒', '小儿氨酚黄那敏颗粒', '/images/medicines/xiaoeranfenhuangnamin.jpg', '4g*12袋', '哈药集团制药六厂', 12.50, 15.00, 150, 600, 0, '适用于缓解儿童普通感冒及流行性感冒引起的发热、头痛、四肢酸痛、打喷嚏、流鼻涕、鼻塞、咽痛等症状。', '温水冲服。1-3岁，一次0.5-1袋，一日3次。', 1, 1),
(1, 7, '布洛芬混悬液', '布洛芬混悬液', '/images/medicines/buluofen_hunxuanye.jpg', '100ml:2g', '上海强生制药有限公司', 28.00, 32.00, 80, 300, 0, '用于儿童普通感冒或流行性感冒引起的发热。也用于缓解儿童轻至中度疼痛。', '口服。需要时每6-8小时可重复使用，每24小时不超过4次。', 1, 1),
(1, 7, '头孢克洛干混悬剂', '头孢克洛干混悬剂', '/images/medicines/toubaokeluo.jpg', '0.125g*6袋', '苏州中化药品工业有限公司', 32.00, 36.00, 60, 120, 1, '用于敏感菌所致的呼吸系统、泌尿系统、耳鼻喉科及皮肤、软组织感染等。', '口服。按体重一日20-40mg/kg，分3次给予。', 1, 1),
(1, 7, '小儿豉翘清热颗粒', '小儿豉翘清热颗粒', '/images/medicines/xiaoerchiqiao.jpg', '2g*6袋', '济川药业集团有限公司', 38.00, 42.00, 70, 150, 0, '疏风解表，清热导滞。用于小儿风热感冒挟滞证。', '开水冲服。6个月-1岁：一次1-2g；1-3岁：一次2-3g。', 1, 1),
(1, 7, '蒙脱石散(儿童型)', '蒙脱石散', '/images/medicines/mengtuoshi_children.jpg', '3g*10袋', '博福-益普生(天津)制药有限公司', 26.00, 30.00, 90, 200, 0, '用于儿童急、慢性腹泻。', '将本品倒入50毫升温水中，摇匀后服用。1岁以下：每日1袋；1-2岁：每日1-2袋。', 1, 1),
(1, 7, '小儿肺热咳喘口服液', '小儿肺热咳喘口服液', '/images/medicines/xiaoerfeire.jpg', '10ml*6支', '黑龙江葵花药业股份有限公司', 24.00, 28.00, 80, 180, 0, '清热解毒，宣肺化痰，用于热邪犯于肺卫所致发热、汗出、微恶风寒、咳嗽、痰黄。', '口服。1-3岁，一次10ml，一日3次。', 1, 1),

-- 8. 更多分类 - 这里放置一些其他常见药品 (6个药品)
(1, 8, '眼药水', '复方门冬维甘滴眼液', '/images/medicines/yanyaoshui.jpg', '13ml', '曼秀雷敦(中国)药业有限公司', 18.00, 22.00, 120, 300, 0, '用于抗眼疲劳，减轻结膜充血症状。', '滴眼。一次1-2滴，一日4-6次。', 1, 1),
(1, 8, '创可贴', '创可贴', '/images/medicines/chuangketie.jpg', '100片', '云南白药集团股份有限公司', 12.00, 15.00, 200, 500, 0, '用于小创伤、擦伤等患处，有助于防止细菌和异物侵入，保持伤口卫生，预防伤口感染。', '外用。撕开包装，将中间的吸收垫敷在创伤处，然后撕去两端的覆盖膜并用胶带固定位置。', 1, 1),
(1, 8, '退热贴', '退热贴', '/images/medicines/tuiretie.jpg', '4片', '小林制药株式会社', 25.00, 30.00, 150, 400, 0, '适用于小儿感冒、感染等引起的发烧的辅助治疗及应急物理降温。', '外用。撕开透明胶片，将胶面贴敷于额头或太阳穴。', 1, 1),
(1, 8, '体温计', '电子体温计', '/images/medicines/tiwenji.jpg', '1支', '欧姆龙健康医疗(中国)有限公司', 45.00, 55.00, 80, 120, 0, '用于测量人体体温。', '置于腋下、口腔或肛门测量。', 1, 1),
(1, 8, '医用口罩', '一次性使用医用口罩', '/images/medicines/kouzhao.jpg', '50只', '3M中国有限公司', 35.00, 45.00, 300, 800, 0, '用于普通医疗环境中佩戴，阻隔口腔和鼻腔呼出或喷出污染物。', '佩戴覆盖口、鼻及下颌，将双手指尖放在鼻夹上，从中间位置开始，用手指向内按压，并逐步向两侧移动，根据鼻梁形状塑造鼻夹。', 1, 1),
(1, 8, '碘伏消毒液', '碘伏消毒液', '/images/medicines/dianfu.jpg', '100ml', '稳健医疗用品股份有限公司', 8.50, 12.00, 150, 350, 0, '适用于皮肤、黏膜的消毒。', '外用。用无菌棉拭子蘸取本品直接涂擦患处。', 1, 1);



-- 清空address表
TRUNCATE TABLE `address`;

-- 为不同用户添加收货地址示例数据
INSERT INTO `address` (`user_id`, `name`, `phone`, `province`, `city`, `district`, `detail`, `is_default`, `create_time`, `update_time`) VALUES
-- 用户1的地址
(1, '张三', '13800138000', '北京市', '北京市', '海淀区', '中关村大街1号科技大厦A座501', 1, NOW(), NOW()),
(1, '张三', '13800138000', '北京市', '北京市', '朝阳区', '建国门外大街1号国贸三期', 0, NOW(), NOW()),
-- 用户2的地址
(2, '李四', '13900139000', '上海市', '上海市', '浦东新区', '陆家嘴环路100号金茂大厦', 1, NOW(), NOW()),
(2, '李四', '13900139000', '上海市', '上海市', '徐汇区', '淮海中路999号', 0, NOW(), NOW()),
-- 用户3的地址
(3, '王五', '13700137000', '广东省', '深圳市', '南山区', '科技园南区1001号腾讯大厦', 1, NOW(), NOW()),
(3, '王五', '13700137000', '广东省', '广州市', '天河区', '天河路208号天河城', 0, NOW(), NOW());


-- 清空delivery_exception表
TRUNCATE TABLE `delivery_exception`;

-- 插入配送异常示例数据
INSERT INTO `delivery_exception` (`order_id`, `rider_id`, `type`, `description`, `images`, `status`, `handle_result`, `create_time`, `update_time`) VALUES
-- 示例1：无法联系用户
(1001, 1, 1, '配送时多次拨打用户电话均无人接听，尝试联系3次', '["exception1.jpg", "exception2.jpg"]', 1, '已通过短信联系用户，用户表示会注意接听电话', DATE_SUB(NOW(), INTERVAL 2 DAY), DATE_SUB(NOW(), INTERVAL 1 DAY)),
-- 示例2：地址异常
(1002, 2, 2, '配送地址不准确，实际位置与地图显示有偏差，无法找到具体门牌号', '["address_error.jpg"]', 0, NULL, DATE_SUB(NOW(), INTERVAL 1 DAY), DATE_SUB(NOW(), INTERVAL 1 DAY)),
-- 示例3：其他异常
(1003, 3, 3, '配送途中电动车发生故障，需要维修', '["vehicle_fault.jpg"]', 1, '已安排其他骑手接单，预计延迟30分钟送达', DATE_SUB(NOW(), INTERVAL 3 DAY), DATE_SUB(NOW(), INTERVAL 2 DAY)),
-- 示例4：无法联系用户
(1004, 1, 1, '用户手机关机，无法联系确认收货', '[]', 0, NULL, DATE_SUB(NOW(), INTERVAL 5 HOUR), DATE_SUB(NOW(), INTERVAL 5 HOUR)),
-- 示例5：地址异常
(1005, 2, 2, '用户填写的地址小区已拆迁，实际不存在', '["demolished.jpg"]', 1, '联系用户后重新确认地址，已安排重新配送', DATE_SUB(NOW(), INTERVAL 6 HOUR), DATE_SUB(NOW(), INTERVAL 4 HOUR));

SET FOREIGN_KEY_CHECKS = 1;




-- ============================================
-- 为药店商家添加测试订单数据
-- ============================================

-- 设置变量，方便修改
SET @merchant_id = 10;  -- 你要为其添加订单的商家ID
SET @user_id = 1;      -- 下单用户ID，需要是普通用户(role=1)
SET @order_status = 3; -- 订单状态: 0-待支付 1-待接单 2-拒单 3-待配送 4-配送中 5-已完成 6-已取消

-- 第一步：查看商家信息
SELECT
    m.id as merchant_id,
    m.shop_name,
    m.contact_name,
    m.contact_phone,
    m.address,
    COUNT(med.id) as medicine_count
FROM merchant m
         LEFT JOIN medicine med ON m.id = med.merchant_id AND med.deleted = 0 AND med.status = 1
WHERE m.id = @merchant_id AND m.deleted = 0
GROUP BY m.id;

-- 第二步：查看该商家的可用药品
SELECT
    id as medicine_id,
    name as medicine_name,
    price,
    stock,
    specification
FROM medicine
WHERE merchant_id = @merchant_id
  AND deleted = 0
  AND status = 1
  AND stock > 0
LIMIT 5;

-- 第三步：生成订单数据
-- 假设我们选择前2个药品下单
SET @medicine1_id = (SELECT id FROM medicine WHERE merchant_id = @merchant_id AND deleted = 0 AND status = 1 AND stock > 0 LIMIT 1);
SET @medicine2_id = (SELECT id FROM medicine WHERE merchant_id = @merchant_id AND deleted = 0 AND status = 1 AND stock > 0 LIMIT 1 OFFSET 1);

-- 获取药品信息
SELECT
    @medicine1_price := price,
    @medicine1_name := name
FROM medicine WHERE id = @medicine1_id;

SELECT
    @medicine2_price := price,
    @medicine2_name := name
FROM medicine WHERE id = @medicine2_id;

-- 生成订单号（使用时间戳+随机数）
SET @order_no = CONCAT('DD', DATE_FORMAT(NOW(), '%Y%m%d%H%i%s'), FLOOR(RAND() * 1000));

-- 第四步：插入订单主表
INSERT INTO orders (
    order_no,
    user_id,
    merchant_id,
    receiver_name,
    receiver_phone,
    receiver_address,
    total_amount,
    delivery_fee,
    discount_amount,
    pay_amount,
    status,
    create_time,
    update_time
) VALUES (
             @order_no,
             @user_id,
             @merchant_id,
             '测试用户',
             '13800138000',
             '北京市海淀区测试地址',
             0, -- total_amount 先填0，后面计算
             5.00, -- 配送费
             2.00, -- 优惠金额
             0, -- pay_amount 先填0，后面计算
             @order_status,
             DATE_SUB(NOW(), INTERVAL 2 DAY), -- 创建时间设为2天前
             DATE_SUB(NOW(), INTERVAL 2 DAY)
         );

-- 获取刚插入的订单ID
SET @order_id = LAST_INSERT_ID();

-- 第五步：计算商品总金额并插入订单项
SET @quantity1 = 2; -- 第一个商品数量
SET @quantity2 = 1; -- 第二个商品数量

SET @subtotal1 = @medicine1_price * @quantity1;
SET @subtotal2 = @medicine2_price * @quantity2;
SET @total_amount = @subtotal1 + @subtotal2;
SET @pay_amount = @total_amount + 5.00 - 2.00; -- 商品总价 + 配送费 - 优惠

-- 插入订单项1
INSERT INTO order_item (
    order_id,
    medicine_id,
    medicine_name,
    price,
    quantity,
    subtotal,
    create_time
) VALUES (
             @order_id,
             @medicine1_id,
             @medicine1_name,
             @medicine1_price,
             @quantity1,
             @subtotal1,
             DATE_SUB(NOW(), INTERVAL 2 DAY)
         );

-- 插入订单项2
INSERT INTO order_item (
    order_id,
    medicine_id,
    medicine_name,
    price,
    quantity,
    subtotal,
    create_time
) VALUES (
             @order_id,
             @medicine2_id,
             @medicine2_name,
             @medicine2_price,
             @quantity2,
             @subtotal2,
             DATE_SUB(NOW(), INTERVAL 2 DAY)
         );

-- 第六步：更新订单总金额
UPDATE orders
SET
    total_amount = @total_amount,
    pay_amount = @pay_amount,
    update_time = NOW()
WHERE id = @order_id;

-- 第七步：更新药品销量和库存（如果需要）
UPDATE medicine SET
                    sales = sales + @quantity1,
                    stock = stock - @quantity1
WHERE id = @medicine1_id;

UPDATE medicine SET
                    sales = sales + @quantity2,
                    stock = stock - @quantity2
WHERE id = @medicine2_id;

-- 第八步：验证插入结果
SELECT '订单创建成功!' as message;

SELECT
    o.id as order_id,
    o.order_no,
    o.status,
    CASE o.status
        WHEN 0 THEN '待支付'
        WHEN 1 THEN '待接单'
        WHEN 2 THEN '已拒单'
        WHEN 3 THEN '待配送'
        WHEN 4 THEN '配送中'
        WHEN 5 THEN '已完成'
        WHEN 6 THEN '已取消'
        END as status_name,
    o.total_amount,
    o.delivery_fee,
    o.discount_amount,
    o.pay_amount,
    o.create_time,
    m.shop_name
FROM orders o
         JOIN merchant m ON o.merchant_id = m.id
WHERE o.id = @order_id;

SELECT
    oi.medicine_name,
    oi.price,
    oi.quantity,
    oi.subtotal
FROM order_item oi
WHERE oi.order_id = @order_id;







-- ============================================
-- 为商家ID=10创建已完成的创可贴订单
-- 药品ID: 54 (创可贴)
-- 订单状态: 5 (已完成)
-- ============================================

-- 1. 首先检查药品是否存在
SELECT
    id as medicine_id,
    name as medicine_name,
    price,
    stock,
    merchant_id,
    specification
FROM medicine
WHERE id = 54 AND deleted = 0;

-- 2. 检查商家ID=10是否存在
SELECT
    id as merchant_id,
    shop_name,
    contact_name,
    contact_phone
FROM merchant
WHERE id = 10 AND deleted = 0;

-- 3. 检查普通用户是否存在
SELECT
    id as user_id,
    username,
    nickname,
    phone
FROM sys_user
WHERE role = 1 AND deleted = 0
ORDER BY id
LIMIT 1;

-- 4. 创建已完成的订单
SET @merchant_id = 10;
SET @medicine_id = 54;
SET @user_id = (SELECT id FROM sys_user WHERE role = 1 AND deleted = 0 LIMIT 1);
SET @medicine_price = (SELECT price FROM medicine WHERE id = @medicine_id);
SET @medicine_name = (SELECT name FROM medicine WHERE id = @medicine_id);
SET @order_quantity = 3; -- 购买3盒创可贴
SET @order_status = 5; -- 5=已完成

-- 生成订单号
SET @order_no = CONCAT('DD', DATE_FORMAT(NOW(), '%Y%m%d%H%i%s'), FLOOR(RAND() * 1000));

-- 计算金额
SET @subtotal = @medicine_price * @order_quantity;
SET @delivery_fee = 5.00;
SET @discount_amount = 2.00;
SET @total_amount = @subtotal;
SET @pay_amount = @total_amount + @delivery_fee - @discount_amount;

-- 创建订单时间（设为昨天）
SET @order_time = DATE_SUB(NOW(), INTERVAL 1 DAY);
-- 完成时间（设为下单后1小时）
SET @complete_time = DATE_ADD(@order_time, INTERVAL 1 HOUR);

-- 5. 插入订单主表
INSERT INTO orders (
    order_no,
    user_id,
    merchant_id,
    receiver_name,
    receiver_phone,
    receiver_address,
    total_amount,
    delivery_fee,
    discount_amount,
    pay_amount,
    status,
    create_time,
    update_time,
    pay_time,
    accept_time,
    rider_accept_time,
    delivery_start_time,
    complete_time
) VALUES (
             @order_no,
             @user_id,
             @merchant_id,
             '王小明',
             '13812345678',
             '上海市浦东新区张江高科技园区',
             @total_amount,
             @delivery_fee,
             @discount_amount,
             @pay_amount,
             @order_status,
             @order_time,  -- 创建时间
             @complete_time, -- 更新时间
             DATE_ADD(@order_time, INTERVAL 5 MINUTE),  -- 支付时间（5分钟后）
             DATE_ADD(@order_time, INTERVAL 10 MINUTE), -- 接单时间（10分钟后）
             DATE_ADD(@order_time, INTERVAL 15 MINUTE), -- 骑手接单时间（15分钟后）
             DATE_ADD(@order_time, INTERVAL 20 MINUTE), -- 配送开始时间（20分钟后）
             @complete_time  -- 完成时间
         );

-- 获取订单ID
SET @order_id = LAST_INSERT_ID();

-- 6. 插入订单项
INSERT INTO order_item (
    order_id,
    medicine_id,
    medicine_name,
    medicine_image,
    specification,
    price,
    quantity,
    subtotal,
    is_prescription,
    create_time
) VALUES (
             @order_id,
             @medicine_id,
             @medicine_name,
             (SELECT image FROM medicine WHERE id = @medicine_id),
             (SELECT specification FROM medicine WHERE id = @medicine_id),
             @medicine_price,
             @order_quantity,
             @subtotal,
             (SELECT is_prescription FROM medicine WHERE id = @medicine_id),
             @order_time
         );

-- 7. 更新药品销量和库存
UPDATE medicine
SET
    sales = sales + @order_quantity,
    stock = CASE
                WHEN stock >= @order_quantity THEN stock - @order_quantity
                ELSE stock
        END
WHERE id = @medicine_id;

-- 8. 更新商家月销量
UPDATE merchant
SET monthly_sales = monthly_sales + 1
WHERE id = @merchant_id;

-- 9. 查看创建结果
SELECT '✅ 订单创建成功！' as message;
SELECT
    CONCAT('订单号: ', order_no) as 订单信息,
    CONCAT('药品: ', @medicine_name) as 药品信息,
    CONCAT('数量: ', @order_quantity) as 购买数量,
    CONCAT('状态: 已完成') as 订单状态,
    CONCAT('下单时间: ', DATE_FORMAT(create_time, '%Y-%m-%d %H:%i:%s')) as 下单时间,
    CONCAT('完成时间: ', DATE_FORMAT(complete_time, '%Y-%m-%d %H:%i:%s')) as 完成时间
FROM orders
WHERE id = @order_id;

-- 10. 查看订单详情（对应网页表格显示的数据）
SELECT
    o.order_no as '订单号',
    o.receiver_name as '收货人',
    CONCAT('¥', FORMAT(o.pay_amount, 2)) as '金额',
    CASE o.status
        WHEN 0 THEN '待支付'
        WHEN 1 THEN '待接单'
        WHEN 2 THEN '已拒单'
        WHEN 3 THEN '待配送'
        WHEN 4 THEN '配送中'
        WHEN 5 THEN '已完成'
        WHEN 6 THEN '已取消'
        END as '状态',
    DATE_FORMAT(o.create_time, '%Y-%m-%d %H:%i') as '下单时间',
    oi.medicine_name as '商品名称',
    oi.quantity as '数量',
    CONCAT('¥', FORMAT(oi.price, 2)) as '单价',
    CONCAT('¥', FORMAT(oi.subtotal, 2)) as '小计'
FROM orders o
         JOIN order_item oi ON o.id = oi.order_id
         JOIN merchant m ON o.merchant_id = m.id
WHERE o.id = @order_id;