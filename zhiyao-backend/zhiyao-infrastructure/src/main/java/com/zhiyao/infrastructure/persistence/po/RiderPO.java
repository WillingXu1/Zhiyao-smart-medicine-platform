package com.zhiyao.infrastructure.persistence.po;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

import java.io.Serializable;
import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 骑手持久化对象
 * 字段与数据库表 rider 一致
 */
@Data
@TableName("rider")
public class RiderPO implements Serializable {

    private static final long serialVersionUID = 1L;

    @TableId(type = IdType.AUTO)
    private Long id;

    private Long userId;

    private String realName;  // 真实姓名（数据库字段）

    private String idCard;  // 身份证号

    private String idCardFront;  // 身份证正面

    private String idCardBack;  // 身份证背面

    private Integer status;  // 状态：0-离线 1-接单中

    private Integer auditStatus;  // 审核状态：0-待审核 1-通过 2-拒绝

    private Integer todayOrders;  // 今日订单数

    private BigDecimal todayIncome;  // 今日收入

    private Integer totalOrders;  // 累计订单数

    private BigDecimal totalIncome;  // 累计收入

    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;

    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updateTime;

    @TableLogic
    private Integer deleted;

    // 以下字段不在数据库中，但保留供业务逻辑使用
    @TableField(exist = false)
    private String phone;  // 电话（从 user 表获取）

    @TableField(exist = false)
    private String avatar;  // 头像（从 user 表获取）

    @TableField(exist = false)
    private Integer onlineStatus;  // 在线状态（业务字段）

    @TableField(exist = false)
    private BigDecimal longitude;  // 经度

    @TableField(exist = false)
    private BigDecimal latitude;  // 纬度

    @TableField(exist = false)
    private BigDecimal rating;  // 评分

    @TableField(exist = false)
    private String auditRemark;  // 审核备注
}
