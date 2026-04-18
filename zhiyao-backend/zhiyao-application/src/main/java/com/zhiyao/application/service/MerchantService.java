package com.zhiyao.application.service;

import com.zhiyao.application.dto.ChangePasswordDTO;
import com.zhiyao.common.result.PageResult;

import java.util.Map;

/**
 * 商家应用服务接口
 */
public interface MerchantService {

    /**
     * 商家入驻申请
     */
    Long applyMerchant(Long userId, Map<String, Object> applyDTO);

    /**
     * 获取商家信息
     */
    Map<String, Object> getMerchantInfo(Long merchantId);

    /**
     * 更新商家信息
     */
    void updateMerchantInfo(Long merchantId, Map<String, Object> merchantDTO);

    /**
     * 商家修改密码
     */
    void changePassword(Long userId, ChangePasswordDTO passwordDTO);

    /**
     * 获取商家订单列表
     */
    PageResult<Map<String, Object>> getMerchantOrders(Long merchantId, Integer status, Integer pageNum, Integer pageSize);

    /**
     * 获取订单详情
     */
    Map<String, Object> getOrderDetail(Long orderId, Long userId);

    /**
     * 商家接单
     */
    void acceptOrder(Long orderId, Long merchantId);

    /**
     * 商家拒单
     */
    void rejectOrder(Long orderId, Long merchantId, String reason);

    /**
     * 获取商家药品列表
     */
    PageResult<Map<String, Object>> getMerchantMedicines(Long merchantId, String keyword, Integer status, Integer pageNum, Integer pageSize);

    /**
     * 商家添加药品
     */
    Long addMedicine(Long merchantId, Map<String, Object> medicineDTO);

    /**
     * 商家更新药品
     */
    void updateMedicine(Long merchantId, Long medicineId, Map<String, Object> medicineDTO);

    /**
     * 商家删除药品
     */
    void deleteMedicine(Long merchantId, Long medicineId);

    /**
     * 商家上下架药品
     */
    void updateMedicineStatus(Long merchantId, Long medicineId, Integer status);

    /**
     * 获取商家统计数据
     */
    Map<String, Object> getMerchantStatistics(Long merchantId);
}
