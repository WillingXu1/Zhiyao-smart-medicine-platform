package com.zhiyao.infrastructure.persistence.po;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

import java.io.Serializable;
import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 订单项持久化对象
 */
@Data
@TableName("order_item")
public class OrderItemPO implements Serializable {

    private static final long serialVersionUID = 1L;

    @TableId(type = IdType.AUTO)
    private Long id;

    private Long orderId;

    private Long medicineId;

    private String medicineName;

    private String medicineImage;

    private String specification;

    private BigDecimal price;

    private Integer quantity;

    private BigDecimal subtotal;

    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;
}
