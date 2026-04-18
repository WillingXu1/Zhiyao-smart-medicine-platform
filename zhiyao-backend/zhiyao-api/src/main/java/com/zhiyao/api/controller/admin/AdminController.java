package com.zhiyao.api.controller.admin;

import com.zhiyao.application.dto.LoginDTO;
import com.zhiyao.application.dto.AdminProfileDTO;
import com.zhiyao.application.dto.AuditDTO;
import com.zhiyao.application.dto.ChangePasswordDTO;
import com.zhiyao.application.dto.PlatformConfigDTO;
import com.zhiyao.application.service.AdminService;
import com.zhiyao.common.result.Result;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

/**
 * 管理员控制器
 */
@RestController
@RequestMapping("/admin")
@RequiredArgsConstructor
public class AdminController {

    private final AdminService adminService;

    /**
     * 管理员登录
     */
    @PostMapping("/auth/login")
    public Result<?> login(@RequestBody LoginDTO loginDTO) {
        return adminService.login(loginDTO);
    }

    /**
     * 获取管理员信息
     */
    @GetMapping("/info")
    public Result<?> getAdminInfo() {
        return adminService.getCurrentAdmin();
    }

    /**
     * 获取仪表盘统计数据
     */
    @GetMapping("/dashboard/stats")
    public Result<?> getDashboardStats() {
        return adminService.getDashboardStats();
    }

    /**
     * 获取统计数据（别名）
     */
    @GetMapping("/statistics")
    public Result<?> getStatistics() {
        return adminService.getDashboardStats();
    }

    /**
     * 获取用户列表
     */
    @GetMapping("/users")
    public Result<?> getUserList(
            @RequestParam(name = "pageNum", defaultValue = "1") Integer page,
            @RequestParam(name = "pageSize", defaultValue = "10") Integer size,
            @RequestParam(name = "keyword", required = false) String keyword) {
        return adminService.getUserList(page, size, keyword);
    }

    /**
     * 禁用/启用用户
     */
    @PutMapping("/users/{userId}/status")
    public Result<?> updateUserStatus(
            @PathVariable("userId") Long userId,
            @RequestParam(name = "status") Integer status) {
        return adminService.updateUserStatus(userId, status);
    }

    /**
     * 获取商家列表
     */
    @GetMapping("/merchants")
    public Result<?> getMerchantList(
            @RequestParam(name = "pageNum", defaultValue = "1") Integer page,
            @RequestParam(name = "pageSize", defaultValue = "10") Integer size,
            @RequestParam(name = "keyword", required = false) String keyword,
            @RequestParam(name = "status", required = false) Integer status) {
        return adminService.getMerchantList(page, size, keyword, status);
    }

    /**
     * 审核商家
     */
    @PutMapping("/merchants/{merchantId}/audit")
    public Result<?> auditMerchant(
            @PathVariable("merchantId") Long merchantId,
            @RequestBody AuditDTO auditDTO) {
        return adminService.auditMerchant(merchantId, auditDTO.getStatus(), auditDTO.getReason());
    }

    /**
     * 获取药品列表
     */
    @GetMapping("/medicines")
    public Result<?> getMedicineList(
            @RequestParam(name = "pageNum", defaultValue = "1") Integer page,
            @RequestParam(name = "pageSize", defaultValue = "10") Integer size,
            @RequestParam(name = "keyword", required = false) String keyword,
            @RequestParam(name = "categoryId", required = false) Long categoryId) {
        return adminService.getMedicineList(page, size, keyword, categoryId);
    }

    /**
     * 审核药品
     */
    @PutMapping("/medicines/{medicineId}/audit")
    public Result<?> auditMedicine(
            @PathVariable("medicineId") Long medicineId,
            @RequestBody AuditDTO auditDTO) {
        return adminService.auditMedicine(medicineId, auditDTO.getStatus(), auditDTO.getReason(), auditDTO.getCategoryId());
    }

    /**
     * 获取订单列表
     */
    @GetMapping("/orders")
    public Result<?> getOrderList(
            @RequestParam(name = "pageNum", defaultValue = "1") Integer page,
            @RequestParam(name = "pageSize", defaultValue = "10") Integer size,
            @RequestParam(name = "orderNo", required = false) String orderNo,
            @RequestParam(name = "status", required = false) Integer status) {
        return adminService.getOrderList(page, size, orderNo, status);
    }

    /**
     * 获取订单详情
     */
    @GetMapping("/orders/{orderId}")
    public Result<?> getOrderDetail(@PathVariable("orderId") Long orderId) {
        return adminService.getOrderDetail(orderId);
    }

    /**
     * 获取骑手列表
     */
    @GetMapping("/riders")
    public Result<?> getRiderList(
            @RequestParam(name = "pageNum", defaultValue = "1") Integer page,
            @RequestParam(name = "pageSize", defaultValue = "10") Integer size,
            @RequestParam(name = "keyword", required = false) String keyword) {
        return adminService.getRiderList(page, size, keyword);
    }

    /**
     * 审核骑手
     */
    @PutMapping("/riders/{riderId}/audit")
    public Result<?> auditRider(
            @PathVariable("riderId") Long riderId,
            @RequestBody AuditDTO auditDTO) {
        return adminService.auditRider(riderId, auditDTO.getStatus(), auditDTO.getReason());
    }

    // ================== 系统设置相关API ==================

    /**
     * 更新管理员个人信息
     */
    @PutMapping("/profile")
    public Result<?> updateProfile(@RequestBody AdminProfileDTO profileDTO) {
        return adminService.updateProfile(profileDTO);
    }

    /**
     * 修改密码
     */
    @PutMapping("/password")
    public Result<?> changePassword(@RequestBody ChangePasswordDTO passwordDTO) {
        return adminService.changePassword(passwordDTO);
    }

    /**
     * 获取平台配置
     */
    @GetMapping("/config")
    public Result<?> getPlatformConfig() {
        return adminService.getPlatformConfig();
    }

    /**
     * 保存平台配置
     */
    @PutMapping("/config")
    public Result<?> savePlatformConfig(@RequestBody PlatformConfigDTO configDTO) {
        return adminService.savePlatformConfig(configDTO);
    }
}
