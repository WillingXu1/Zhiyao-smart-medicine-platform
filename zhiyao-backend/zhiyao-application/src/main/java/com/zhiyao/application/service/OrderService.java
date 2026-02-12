package com.zhiyao.application.service;

import com.zhiyao.common.result.PageResult;

import java.util.Map;

/**
 * 订单应用服务接口
 */
public interface OrderService {

    /**
     * 创建订单
     */
    Long createOrder(Long userId, Map<String, Object> orderDTO);

    /**
     * 获取订单详情
     */
    Map<String, Object> getOrderDetail(Long orderId, Long userId);

    /**
     * 获取用户订单列表
     */
    PageResult<Map<String, Object>> getUserOrders(Long userId, Integer status, Integer pageNum, Integer pageSize);

    /**
     * 取消订单
     */
    void cancelOrder(Long orderId, Long userId, String reason);

    /**
     * 支付订单（模拟支付）
     */
    void payOrder(Long orderId, Long userId);

    /**
     * 确认收货
     */
    void confirmReceive(Long orderId, Long userId);

    /**
     * 商家接单
     */
    void acceptOrder(Long orderId, Long merchantId);

    /**
     * 商家拒单
     */
    void rejectOrder(Long orderId, Long merchantId, String reason);

    /**
     * 获取商家订单列表
     */
    PageResult<Map<String, Object>> getMerchantOrders(Long merchantId, Integer status, Integer pageNum, Integer pageSize);

    /**
     * 骑手接单
     */
    void riderAcceptOrder(Long orderId, Long riderId);

    /**
     * 骑手完成配送
     */
    void riderCompleteDelivery(Long orderId, Long riderId);

    /**
     * 获取骑手待接订单列表
     */
    PageResult<Map<String, Object>> getPendingDeliveryOrders(Integer pageNum, Integer pageSize);

    /**
     * 获取骑手配送中订单列表
     */
    PageResult<Map<String, Object>> getRiderDeliveringOrders(Long riderId, Integer pageNum, Integer pageSize);
}
