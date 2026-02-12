package com.zhiyao.domain.order.entity;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import lombok.Builder;

import java.io.Serializable;
import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 订单项实体
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class OrderItem implements Serializable {

    private static final long serialVersionUID = 1L;

    /** 订单项ID */
    private Long id;

    /** 订单ID */
    private Long orderId;

    /** 药品ID */
    private Long medicineId;

    /** 药品名称 */
    private String medicineName;

    /** 药品图片 */
    private String medicineImage;

    /** 药品规格 */
    private String specification;

    /** 单价 */
    private BigDecimal price;

    /** 数量 */
    private Integer quantity;

    /** 小计金额 */
    private BigDecimal subtotal;

    /** 是否处方药 */
    private Integer isPrescription;

    /** 创建时间 */
    private LocalDateTime createTime;

    /**
     * 计算小计金额
     */
    public BigDecimal calculateSubtotal() {
        if (this.price != null && this.quantity != null) {
            this.subtotal = this.price.multiply(BigDecimal.valueOf(this.quantity));
        }
        return this.subtotal;
    }
}
