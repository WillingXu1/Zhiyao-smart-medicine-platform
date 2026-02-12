package com.zhiyao.common.enums;

import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * 订单状态枚举
 */
@Getter
@AllArgsConstructor
public enum OrderStatus {

    PENDING_PAYMENT(0, "待支付"),
    PENDING_ACCEPT(1, "待商家接单"),
    MERCHANT_REJECTED(2, "商家拒单"),
    PENDING_DELIVERY(3, "待配送"),
    DELIVERING(4, "配送中"),
    COMPLETED(5, "已完成"),
    CANCELLED(6, "已取消");

    private final Integer code;
    private final String desc;

    public static OrderStatus fromCode(Integer code) {
        for (OrderStatus status : values()) {
            if (status.code.equals(code)) {
                return status;
            }
        }
        return null;
    }
}
