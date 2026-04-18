package com.zhiyao.domain.order.entity;

import com.zhiyao.common.enums.OrderStatus;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import lombok.Builder;

import java.io.Serializable;
import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 订单实体
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Order implements Serializable {

    private static final long serialVersionUID = 1L;

    /** 订单ID */
    private Long id;

    /** 订单编号 */
    private String orderNo;

    /** 用户ID */
    private Long userId;

    /** 商家ID */
    private Long merchantId;

    /** 骑手ID */
    private Long riderId;

    /** 收货地址ID */
    private Long addressId;

    /** 收货人姓名 */
    private String receiverName;

    /** 收货人手机号 */
    private String receiverPhone;

    /** 收货地址 */
    private String receiverAddress;

    /** 经度 */
    private Double longitude;

    /** 纬度 */
    private Double latitude;

    /** 商品总金额 */
    private BigDecimal totalAmount;

    /** 配送费 */
    private BigDecimal deliveryFee;

    /** 优惠金额 */
    private BigDecimal discountAmount;

    /** 实付金额 */
    private BigDecimal payAmount;

    /** 订单状态 */
    private OrderStatus status;

    /** 订单备注 */
    private String remark;

    /** 备药说明 */
    private String preparationNote;

    /** 拒单原因 */
    private String rejectReason;

    /** 取消原因 */
    private String cancelReason;

    /** 支付时间 */
    private LocalDateTime payTime;

    /** 接单时间 */
    private LocalDateTime acceptTime;

    /** 骑手接单时间 */
    private LocalDateTime riderAcceptTime;

    /** 配送开始时间 */
    private LocalDateTime deliveryStartTime;

    /** 完成时间 */
    private LocalDateTime completeTime;

    /** 创建时间 */
    private LocalDateTime createTime;

    /** 更新时间 */
    private LocalDateTime updateTime;

    /** 逻辑删除标识 */
    private Integer deleted;

    /**
     * 判断是否可以取消
     */
    public boolean canCancel() {
        return OrderStatus.PENDING_PAYMENT.equals(this.status) 
            || OrderStatus.PENDING_ACCEPT.equals(this.status);
    }

    /**
     * 判断是否可以接单
     */
    public boolean canAccept() {
        return OrderStatus.PENDING_ACCEPT.equals(this.status);
    }

    /**
     * 判断是否可以配送
     */
    public boolean canDeliver() {
        return OrderStatus.PENDING_DELIVERY.equals(this.status);
    }

    /**
     * 判断是否可以完成
     */
    public boolean canComplete() {
        return OrderStatus.DELIVERING.equals(this.status);
    }

    /**
     * 取消订单
     */
    public void cancel(String reason) {
        this.status = OrderStatus.CANCELLED;
        this.cancelReason = reason;
        this.updateTime = LocalDateTime.now();
    }

    /**
     * 商家接单
     */
    public void accept() {
        this.status = OrderStatus.PENDING_DELIVERY;
        this.acceptTime = LocalDateTime.now();
        this.updateTime = LocalDateTime.now();
    }

    /**
     * 商家拒单
     */
    public void reject(String reason) {
        this.status = OrderStatus.MERCHANT_REJECTED;
        this.rejectReason = reason;
        this.updateTime = LocalDateTime.now();
    }

    /**
     * 骑手接单
     */
    public void riderAccept(Long riderId) {
        this.riderId = riderId;
        this.status = OrderStatus.DELIVERING;
        this.riderAcceptTime = LocalDateTime.now();
        this.deliveryStartTime = LocalDateTime.now();
        this.updateTime = LocalDateTime.now();
    }

    /**
     * 完成配送
     */
    public void complete() {
        this.status = OrderStatus.COMPLETED;
        this.completeTime = LocalDateTime.now();
        this.updateTime = LocalDateTime.now();
    }
}
