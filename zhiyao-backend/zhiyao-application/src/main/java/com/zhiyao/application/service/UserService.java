package com.zhiyao.application.service;

import com.zhiyao.application.dto.LoginVO;
import com.zhiyao.application.dto.UserLoginDTO;
import com.zhiyao.application.dto.UserRegisterDTO;

import java.util.List;
import java.util.Map;

/**
 * 用户应用服务接口
 */
public interface UserService {

    /**
     * 用户注册
     */
    Long register(UserRegisterDTO dto);

    /**
     * 用户登录
     */
    LoginVO login(UserLoginDTO dto);

    /**
     * 商家登录
     */
    LoginVO merchantLogin(UserLoginDTO dto);

    /**
     * 管理员登录
     */
    LoginVO adminLogin(UserLoginDTO dto);

    /**
     * 骑手登录
     */
    LoginVO riderLogin(UserLoginDTO dto);

    /**
     * 获取当前用户信息
     */
    LoginVO getCurrentUser(Long userId);

    /**
     * 修改密码
     */
    void changePassword(Long userId, String oldPassword, String newPassword);

    /**
     * 更新用户信息
     */
    void updateUserInfo(Long userId, String nickname, String avatar, String email);

    // ==================== 收货地址相关 ====================

    /**
     * 获取收货地址列表
     */
    List<Map<String, Object>> getAddresses(Long userId);

    /**
     * 添加收货地址
     */
    Long addAddress(Long userId, Map<String, Object> data);

    /**
     * 更新收货地址
     */
    void updateAddress(Long userId, Long addressId, Map<String, Object> data);

    /**
     * 删除收货地址
     */
    void deleteAddress(Long userId, Long addressId);

    /**
     * 设置默认地址
     */
    void setDefaultAddress(Long userId, Long addressId);

    // ==================== 商品收藏相关 ====================

    /**
     * 获取收藏列表
     */
    List<Map<String, Object>> getFavorites(Long userId);

    /**
     * 添加收藏
     */
    void addFavorite(Long userId, Long medicineId);

    /**
     * 取消收藏
     */
    void removeFavorite(Long userId, Long medicineId);

    /**
     * 检查是否收藏
     */
    boolean isFavorite(Long userId, Long medicineId);
}
