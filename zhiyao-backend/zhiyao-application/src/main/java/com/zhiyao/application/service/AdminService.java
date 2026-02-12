package com.zhiyao.application.service;

import com.zhiyao.application.dto.LoginDTO;
import com.zhiyao.application.dto.AdminProfileDTO;
import com.zhiyao.application.dto.ChangePasswordDTO;
import com.zhiyao.application.dto.PlatformConfigDTO;
import com.zhiyao.common.result.Result;

/**
 * 管理员服务接口
 */
public interface AdminService {

    /**
     * 管理员登录
     */
    Result<?> login(LoginDTO loginDTO);

    /**
     * 获取当前管理员信息
     */
    Result<?> getCurrentAdmin();

    /**
     * 获取仪表盘统计数据
     */
    Result<?> getDashboardStats();

    /**
     * 获取用户列表
     */
    Result<?> getUserList(Integer page, Integer size, String keyword);

    /**
     * 更新用户状态
     */
    Result<?> updateUserStatus(Long userId, Integer status);

    /**
     * 获取商家列表
     */
    Result<?> getMerchantList(Integer page, Integer size, String keyword, Integer status);

    /**
     * 审核商家
     */
    Result<?> auditMerchant(Long merchantId, Integer auditStatus, String reason);

    /**
     * 获取药品列表
     */
    Result<?> getMedicineList(Integer page, Integer size, String keyword, Long categoryId);

    /**
     * 审核药品
     */
    Result<?> auditMedicine(Long medicineId, Integer status, String reason, Long categoryId);

    /**
     * 获取订单列表
     */
    Result<?> getOrderList(Integer page, Integer size, String orderNo, Integer status);

    /**
     * 获取订单详情
     */
    Result<?> getOrderDetail(Long orderId);

    /**
     * 获取骑手列表
     */
    Result<?> getRiderList(Integer page, Integer size, String keyword);

    /**
     * 审核骑手
     */
    Result<?> auditRider(Long riderId, Integer status, String reason);

    /**
     * 更新管理员个人信息
     */
    Result<?> updateProfile(AdminProfileDTO profileDTO);

    /**
     * 修改密码
     */
    Result<?> changePassword(ChangePasswordDTO passwordDTO);

    /**
     * 获取平台配置
     */
    Result<?> getPlatformConfig();

    /**
     * 保存平台配置
     */
    Result<?> savePlatformConfig(PlatformConfigDTO configDTO);
}
