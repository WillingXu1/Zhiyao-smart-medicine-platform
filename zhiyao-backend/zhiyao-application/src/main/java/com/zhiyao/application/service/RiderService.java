package com.zhiyao.application.service;

import com.zhiyao.common.result.PageResult;

import java.util.Map;

/**
 * 骑手应用服务接口
 */
public interface RiderService {

    /**
     * 骑手入职申请
     */
    Long applyRider(Long userId, Map<String, Object> applyDTO);

    /**
     * 获取骑手信息
     */
    Map<String, Object> getRiderInfo(Long riderId);

    /**
     * 更新骑手信息
     */
    void updateRiderInfo(Long riderId, Map<String, Object> riderDTO);

    /**
     * 骑手上线/下线
     */
    void updateOnlineStatus(Long riderId, Integer status);

    /**
     * 获取待配送订单列表
     */
    PageResult<Map<String, Object>> getPendingDeliveryOrders(Integer pageNum, Integer pageSize);

    /**
     * 骑手接单
     */
    void acceptOrder(Long orderId, Long riderId);

    /**
     * 开始配送（已取货）
     */
    void startDelivery(Long orderId, Long riderId);

    /**
     * 完成配送
     */
    void completeDelivery(Long orderId, Long riderId);

    /**
     * 获取骑手配送中订单
     */
    PageResult<Map<String, Object>> getDeliveringOrders(Long riderId, Integer pageNum, Integer pageSize);

    /**
     * 获取骑手历史订单
     */
    PageResult<Map<String, Object>> getCompletedOrders(Long riderId, Integer pageNum, Integer pageSize);

    /**
     * 上报配送异常
     */
    void reportException(Long orderId, Long riderId, Map<String, Object> exceptionDTO);

    /**
     * 获取骑手统计数据
     */
    Map<String, Object> getRiderStatistics(Long riderId);

    /**
     * 获取首页数据
     */
    Map<String, Object> getHomeData(Long userId);
}
