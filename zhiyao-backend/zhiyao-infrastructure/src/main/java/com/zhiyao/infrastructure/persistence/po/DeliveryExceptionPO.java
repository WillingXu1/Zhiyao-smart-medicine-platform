package com.zhiyao.infrastructure.persistence.po;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

import java.io.Serializable;
import java.time.LocalDateTime;

/**
 * 配送异常持久化对象
 * 字段与数据库表 delivery_exception 一致
 */
@Data
@TableName("delivery_exception")
public class DeliveryExceptionPO implements Serializable {

    private static final long serialVersionUID = 1L;

    @TableId(type = IdType.AUTO)
    private Long id;

    private Long orderId;

    private Long riderId;

    private Integer type;  // 异常类型：1-无法联系用户 2-地址异常 3-其他

    private String description;  // 异常描述

    private String images;  // 图片凭证JSON

    private Integer status;  // 状态：0-待处理 1-已处理

    private String handleResult;  // 处理结果

    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;

    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updateTime;
}
