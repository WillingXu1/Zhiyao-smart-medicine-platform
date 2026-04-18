package com.zhiyao.infrastructure.persistence.po;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

import java.io.Serializable;
import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 订单持久化对象
 */
@Data
@TableName("orders")
public class OrderPO implements Serializable {

    private static final long serialVersionUID = 1L;

    @TableId(type = IdType.AUTO)
    private Long id;

    private String orderNo;

    private Long userId;

    private Long merchantId;

    private Long riderId;

    private Long addressId;

    private String receiverName;

    private String receiverPhone;

    private String receiverAddress;

    private BigDecimal totalAmount;

    private BigDecimal deliveryFee;

    private BigDecimal payAmount;

    private Integer status;

    @TableField(exist = false)
    private Integer paymentType;

    private LocalDateTime payTime;

    private LocalDateTime acceptTime;

    @TableField("delivery_start_time")
    private LocalDateTime deliveryTime;

    private LocalDateTime completeTime;

    private String cancelReason;

    private String rejectReason;

    private String remark;

    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;

    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updateTime;

    @TableLogic
    private Integer deleted;
}
