package com.zhiyao.api.controller.rider;

import com.zhiyao.api.util.SecurityUtils;
import com.zhiyao.application.service.RiderService;
import com.zhiyao.common.result.PageResult;
import com.zhiyao.common.result.Result;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

/**
 * 骑手端接口
 */
@Tag(name = "骑手管理", description = "骑手端相关接口")
@RestController
@RequestMapping("/rider")
@RequiredArgsConstructor
public class RiderController {

    private final RiderService riderService;

    @Operation(summary = "获取骑手信息", description = "获取当前骑手信息")
    @GetMapping("/info")
    public Result<Map<String, Object>> getRiderInfo() {
        Long userId = SecurityUtils.getCurrentUserId();
        Map<String, Object> info = riderService.getRiderInfo(userId);
        return Result.success(info);
    }

    @Operation(summary = "更新骑手信息", description = "更新骑手基本信息")
    @PutMapping("/info")
    public Result<Void> updateRiderInfo(@RequestBody Map<String, Object> riderDTO) {
        Long userId = SecurityUtils.getCurrentUserId();
        riderService.updateRiderInfo(userId, riderDTO);
        return Result.success();
    }

    @Operation(summary = "获取骑手统计数据", description = "获取骑手统计信息")
    @GetMapping("/statistics")
    public Result<Map<String, Object>> getStatistics() {
        Long userId = SecurityUtils.getCurrentUserId();
        Map<String, Object> stats = riderService.getRiderStatistics(userId);
        return Result.success(stats);
    }

    @Operation(summary = "获取首页数据", description = "获取骑手首页统计数据")
    @GetMapping("/home")
    public Result<Map<String, Object>> getHomeData() {
        Long userId = SecurityUtils.getCurrentUserId();
        Map<String, Object> data = riderService.getHomeData(userId);
        return Result.success(data);
    }

    @Operation(summary = "获取骑手统计数据别名", description = "个人中心统计信息")
    @GetMapping("/stats")
    public Result<Map<String, Object>> getStats() {
        Long userId = SecurityUtils.getCurrentUserId();
        Map<String, Object> stats = riderService.getRiderStatistics(userId);
        return Result.success(stats);
    }

    @Operation(summary = "骑手上线", description = "骑手开始接单")
    @PutMapping("/online")
    public Result<Void> goOnline() {
        Long userId = SecurityUtils.getCurrentUserId();
        riderService.updateOnlineStatus(userId, 1);
        return Result.success();
    }

    @Operation(summary = "骑手下线", description = "骑手停止接单")
    @PutMapping("/offline")
    public Result<Void> goOffline() {
        Long userId = SecurityUtils.getCurrentUserId();
        riderService.updateOnlineStatus(userId, 0);
        return Result.success();
    }

    @Operation(summary = "获取待配送订单", description = "获取待配送的订单列表")
    @GetMapping("/orders/pending")
    public Result<PageResult<Map<String, Object>>> getPendingOrders(
            @Parameter(description = "页码") @RequestParam(value = "pageNum", defaultValue = "1") Integer pageNum,
            @Parameter(description = "每页条数") @RequestParam(value = "pageSize", defaultValue = "10") Integer pageSize) {
        PageResult<Map<String, Object>> result = riderService.getPendingDeliveryOrders(pageNum, pageSize);
        return Result.success(result);
    }

    @Operation(summary = "获取配送中订单", description = "获取正在配送的订单列表")
    @GetMapping("/orders/delivering")
    public Result<PageResult<Map<String, Object>>> getDeliveringOrders(
            @Parameter(description = "页码") @RequestParam(value = "pageNum", defaultValue = "1") Integer pageNum,
            @Parameter(description = "每页条数") @RequestParam(value = "pageSize", defaultValue = "10") Integer pageSize) {
        Long userId = SecurityUtils.getCurrentUserId();
        PageResult<Map<String, Object>> result = riderService.getDeliveringOrders(userId, pageNum, pageSize);
        return Result.success(result);
    }

    @Operation(summary = "获取已完成订单", description = "获取已完成配送的订单列表")
    @GetMapping("/orders/completed")
    public Result<PageResult<Map<String, Object>>> getCompletedOrders(
            @Parameter(description = "页码") @RequestParam(value = "pageNum", defaultValue = "1") Integer pageNum,
            @Parameter(description = "每页条数") @RequestParam(value = "pageSize", defaultValue = "10") Integer pageSize) {
        Long userId = SecurityUtils.getCurrentUserId();
        PageResult<Map<String, Object>> result = riderService.getCompletedOrders(userId, pageNum, pageSize);
        return Result.success(result);
    }

    @Operation(summary = "骑手接单", description = "骑手接受配送订单")
    @PutMapping("/orders/{id}/accept")
    public Result<Void> acceptOrder(@Parameter(description = "订单ID") @PathVariable("id") Long id) {
        Long userId = SecurityUtils.getCurrentUserId();
        riderService.acceptOrder(id, userId);
        return Result.success();
    }

    @Operation(summary = "开始配送", description = "骑手已取货，开始配送")
    @PutMapping("/orders/{id}/start")
    public Result<Void> startDelivery(@Parameter(description = "订单ID") @PathVariable("id") Long id) {
        Long userId = SecurityUtils.getCurrentUserId();
        riderService.startDelivery(id, userId);
        return Result.success();
    }

    @Operation(summary = "完成配送", description = "骑手完成配送")
    @PutMapping("/orders/{id}/complete")
    public Result<Void> completeDelivery(@Parameter(description = "订单ID") @PathVariable("id") Long id) {
        Long userId = SecurityUtils.getCurrentUserId();
        riderService.completeDelivery(id, userId);
        return Result.success();
    }

    @Operation(summary = "上报配送异常", description = "骑手上报配送异常")
    @PostMapping("/orders/{id}/exception")
    public Result<Void> reportException(
            @Parameter(description = "订单ID") @PathVariable("id") Long id,
            @RequestBody Map<String, Object> exceptionDTO) {
        Long userId = SecurityUtils.getCurrentUserId();
        riderService.reportException(id, userId, exceptionDTO);
        return Result.success();
    }
}
