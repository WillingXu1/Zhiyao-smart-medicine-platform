package com.zhiyao.common.result;

import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * 响应状态码枚举
 */
@Getter
@AllArgsConstructor
public enum ResultCode {

    // 成功
    SUCCESS(200, "操作成功"),

    // 客户端错误 4xx
    FAIL(400, "操作失败"),
    PARAM_ERROR(400, "参数错误"),
    UNAUTHORIZED(401, "未登录或登录已过期"),
    FORBIDDEN(403, "无权限访问"),
    NOT_FOUND(404, "资源不存在"),
    METHOD_NOT_ALLOWED(405, "请求方法不允许"),

    // 业务错误 5xx
    SYSTEM_ERROR(500, "系统异常"),
    SERVICE_UNAVAILABLE(503, "服务不可用"),

    // 用户相关 1xxx
    USER_NOT_EXIST(1001, "用户不存在"),
    USER_PASSWORD_ERROR(1002, "密码错误"),
    USER_DISABLED(1003, "账号已被禁用"),
    USER_EXIST(1004, "用户已存在"),
    PHONE_EXIST(1005, "手机号已注册"),

    // 商家相关 2xxx
    MERCHANT_NOT_EXIST(2001, "商家不存在"),
    MERCHANT_NOT_APPROVED(2002, "商家未审核通过"),
    MERCHANT_DISABLED(2003, "商家已被禁用"),

    // 药品相关 3xxx
    MEDICINE_NOT_EXIST(3001, "药品不存在"),
    MEDICINE_OFF_SHELF(3002, "药品已下架"),
    MEDICINE_STOCK_NOT_ENOUGH(3003, "药品库存不足"),
    PRESCRIPTION_REQUIRED(3004, "处方药需要咨询后购买"),

    // 订单相关 4xxx
    ORDER_NOT_EXIST(4001, "订单不存在"),
    ORDER_STATUS_ERROR(4002, "订单状态异常"),
    ORDER_CANCEL_FAIL(4003, "订单取消失败"),
    ORDER_PAY_TIMEOUT(4004, "订单支付超时"),
    ORDER_ITEM_EMPTY(4005, "订单项不能为空"),
    ORDER_MULTI_MERCHANT(4006, "订单只能包含同一商家的商品"),

    // 配送相关 5xxx
    RIDER_NOT_EXIST(5001, "骑手不存在"),
    DELIVERY_ERROR(5002, "配送异常"),

    // 咨询相关 6xxx
    CONSULT_NOT_EXIST(6001, "咨询记录不存在");

    private final Integer code;
    private final String message;
}
