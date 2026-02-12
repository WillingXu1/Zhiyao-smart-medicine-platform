package com.zhiyao.api.controller.user;

import com.zhiyao.application.service.UserService;
import com.zhiyao.common.result.Result;
import com.zhiyao.api.util.SecurityUtils;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

/**
 * 用户接口
 */
@Tag(name = "用户中心", description = "用户信息、地址、收藏等接口")
@RestController
@RequestMapping("/user")
@RequiredArgsConstructor
public class UserController {

    private final UserService userService;

    @Operation(summary = "获取当前用户信息")
    @GetMapping("/info")
    public Result<?> getUserInfo() {
        Long userId = SecurityUtils.getCurrentUserId();
        return Result.success(userService.getCurrentUser(userId));
    }

    @Operation(summary = "更新用户信息")
    @PutMapping("/info")
    public Result<?> updateUserInfo(@RequestBody Map<String, Object> data) {
        Long userId = SecurityUtils.getCurrentUserId();
        String nickname = (String) data.get("nickname");
        String avatar = (String) data.get("avatar");
        String email = (String) data.get("email");
        userService.updateUserInfo(userId, nickname, avatar, email);
        return Result.success("更新成功");
    }

    @Operation(summary = "修改密码")
    @PutMapping("/password")
    public Result<?> changePassword(@RequestBody Map<String, String> data) {
        Long userId = SecurityUtils.getCurrentUserId();
        String oldPassword = data.get("oldPassword");
        String newPassword = data.get("newPassword");
        userService.changePassword(userId, oldPassword, newPassword);
        return Result.success("密码修改成功");
    }

    // ==================== 收货地址 ====================
    
    @Operation(summary = "获取收货地址列表")
    @GetMapping("/addresses")
    public Result<List<Map<String, Object>>> getAddresses() {
        Long userId = SecurityUtils.getCurrentUserId();
        return Result.success(userService.getAddresses(userId));
    }

    @Operation(summary = "添加收货地址")
    @PostMapping("/addresses")
    public Result<Long> addAddress(@RequestBody Map<String, Object> data) {
        Long userId = SecurityUtils.getCurrentUserId();
        Long addressId = userService.addAddress(userId, data);
        return Result.success(addressId);
    }

    @Operation(summary = "更新收货地址")
    @PutMapping("/addresses/{id}")
    public Result<?> updateAddress(@PathVariable("id") Long id, @RequestBody Map<String, Object> data) {
        Long userId = SecurityUtils.getCurrentUserId();
        userService.updateAddress(userId, id, data);
        return Result.success("更新成功");
    }

    @Operation(summary = "删除收货地址")
    @DeleteMapping("/addresses/{id}")
    public Result<?> deleteAddress(@PathVariable("id") Long id) {
        Long userId = SecurityUtils.getCurrentUserId();
        userService.deleteAddress(userId, id);
        return Result.success("删除成功");
    }

    @Operation(summary = "设置默认地址")
    @PutMapping("/addresses/{id}/default")
    public Result<?> setDefaultAddress(@PathVariable("id") Long id) {
        Long userId = SecurityUtils.getCurrentUserId();
        userService.setDefaultAddress(userId, id);
        return Result.success("设置成功");
    }

    // ==================== 商品收藏 ====================
    
    @Operation(summary = "获取收藏列表")
    @GetMapping("/favorites")
    public Result<List<Map<String, Object>>> getFavorites() {
        Long userId = SecurityUtils.getCurrentUserId();
        return Result.success(userService.getFavorites(userId));
    }

    @Operation(summary = "添加收藏")
    @PostMapping("/favorites/{medicineId}")
    public Result<?> addFavorite(@PathVariable("medicineId") Long medicineId) {
        Long userId = SecurityUtils.getCurrentUserId();
        userService.addFavorite(userId, medicineId);
        return Result.success("收藏成功");
    }

    @Operation(summary = "取消收藏")
    @DeleteMapping("/favorites/{medicineId}")
    public Result<?> removeFavorite(@PathVariable("medicineId") Long medicineId) {
        Long userId = SecurityUtils.getCurrentUserId();
        userService.removeFavorite(userId, medicineId);
        return Result.success("取消收藏成功");
    }
}
