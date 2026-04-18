package com.zhiyao.api.controller.merchant;

import com.zhiyao.api.util.SecurityUtils;
import com.zhiyao.application.dto.ChangePasswordDTO;
import com.zhiyao.application.service.MerchantService;
import com.zhiyao.common.result.PageResult;
import com.zhiyao.common.result.Result;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

/**
 * 商家端接口
 */
@Tag(name = "商家管理", description = "商家端相关接口")
@RestController
@RequestMapping("/merchant")
@RequiredArgsConstructor
public class MerchantController {

    private final MerchantService merchantService;

    @Operation(summary = "获取商家信息", description = "获取当前商家信息")
    @GetMapping("/info")
    public Result<Map<String, Object>> getMerchantInfo() {
        Long userId = SecurityUtils.getCurrentUserId();
        // TODO: 根据userId获取merchantId
        Map<String, Object> info = merchantService.getMerchantInfo(userId);
        return Result.success(info);
    }

    @Operation(summary = "更新商家信息", description = "更新商家基本信息")
    @PutMapping("/info")
    public Result<Void> updateMerchantInfo(@RequestBody Map<String, Object> merchantDTO) {
        Long userId = SecurityUtils.getCurrentUserId();
        merchantService.updateMerchantInfo(userId, merchantDTO);
        return Result.success();
    }

    @Operation(summary = "修改密码", description = "商家修改登录密码")
    @PutMapping("/password")
    public Result<Void> changePassword(@RequestBody ChangePasswordDTO passwordDTO) {
        Long userId = SecurityUtils.getCurrentUserId();
        merchantService.changePassword(userId, passwordDTO);
        return Result.success();
    }

    @Operation(summary = "获取商家统计数据", description = "获取商家统计信息")
    @GetMapping("/statistics")
    public Result<Map<String, Object>> getStatistics() {
        Long userId = SecurityUtils.getCurrentUserId();
        Map<String, Object> stats = merchantService.getMerchantStatistics(userId);
        return Result.success(stats);
    }

    @Operation(summary = "获取商家订单列表", description = "获取商家的订单列表")
    @GetMapping("/orders")
    public Result<PageResult<Map<String, Object>>> getOrders(
            @Parameter(description = "订单状态") @RequestParam(value = "status", required = false) Integer status,
            @Parameter(description = "页码") @RequestParam(value = "pageNum", defaultValue = "1") Integer pageNum,
            @Parameter(description = "每页条数") @RequestParam(value = "pageSize", defaultValue = "10") Integer pageSize) {
        Long userId = SecurityUtils.getCurrentUserId();
        PageResult<Map<String, Object>> result = merchantService.getMerchantOrders(userId, status, pageNum, pageSize);
        return Result.success(result);
    }

    @Operation(summary = "获取订单详情", description = "获取商家订单详情")
    @GetMapping("/orders/{id}")
    public Result<Map<String, Object>> getOrderDetail(@Parameter(description = "订单ID") @PathVariable("id") Long id) {
        Long userId = SecurityUtils.getCurrentUserId();
        Map<String, Object> detail = merchantService.getOrderDetail(id, userId);
        return Result.success(detail);
    }

    @Operation(summary = "商家接单", description = "商家接受订单")
    @PutMapping("/orders/{id}/accept")
    public Result<Void> acceptOrder(@Parameter(description = "订单ID") @PathVariable("id") Long id) {
        Long userId = SecurityUtils.getCurrentUserId();
        merchantService.acceptOrder(id, userId);
        return Result.success();
    }

    @Operation(summary = "商家拒单", description = "商家拒绝订单")
    @PutMapping("/orders/{id}/reject")
    public Result<Void> rejectOrder(
            @Parameter(description = "订单ID") @PathVariable("id") Long id,
            @Parameter(description = "拒单原因") @RequestParam("reason") String reason) {
        Long userId = SecurityUtils.getCurrentUserId();
        merchantService.rejectOrder(id, userId, reason);
        return Result.success();
    }

    @Operation(summary = "获取商家药品列表", description = "获取商家的药品列表")
    @GetMapping("/medicines")
    public Result<PageResult<Map<String, Object>>> getMedicines(
            @Parameter(description = "搜索关键词") @RequestParam(value = "keyword", required = false) String keyword,
            @Parameter(description = "状态") @RequestParam(value = "status", required = false) Integer status,
            @Parameter(description = "页码") @RequestParam(value = "pageNum", defaultValue = "1") Integer pageNum,
            @Parameter(description = "每页条数") @RequestParam(value = "pageSize", defaultValue = "10") Integer pageSize) {
        Long userId = SecurityUtils.getCurrentUserId();
        PageResult<Map<String, Object>> result = merchantService.getMerchantMedicines(userId, keyword, status, pageNum, pageSize);
        return Result.success(result);
    }

    @Operation(summary = "添加药品", description = "商家添加新药品")
    @PostMapping("/medicines")
    public Result<Long> addMedicine(@RequestBody Map<String, Object> medicineDTO) {
        Long userId = SecurityUtils.getCurrentUserId();
        Long medicineId = merchantService.addMedicine(userId, medicineDTO);
        return Result.success(medicineId);
    }

    @Operation(summary = "更新药品", description = "商家更新药品信息")
    @PutMapping("/medicines/{id}")
    public Result<Void> updateMedicine(
            @Parameter(description = "药品ID") @PathVariable("id") Long id,
            @RequestBody Map<String, Object> medicineDTO) {
        Long userId = SecurityUtils.getCurrentUserId();
        merchantService.updateMedicine(userId, id, medicineDTO);
        return Result.success();
    }

    @Operation(summary = "删除药品", description = "商家删除药品")
    @DeleteMapping("/medicines/{id}")
    public Result<Void> deleteMedicine(@Parameter(description = "药品ID") @PathVariable("id") Long id) {
        Long userId = SecurityUtils.getCurrentUserId();
        merchantService.deleteMedicine(userId, id);
        return Result.success();
    }

    @Operation(summary = "上下架药品", description = "商家上架或下架药品")
    @PutMapping("/medicines/{id}/status")
    public Result<Void> updateMedicineStatus(
            @Parameter(description = "药品ID") @PathVariable("id") Long id,
            @Parameter(description = "状态：0-下架 1-上架") @RequestParam("status") Integer status) {
        Long userId = SecurityUtils.getCurrentUserId();
        merchantService.updateMedicineStatus(userId, id, status);
        return Result.success();
    }
}
