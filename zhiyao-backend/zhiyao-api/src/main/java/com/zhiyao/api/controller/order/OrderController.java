package com.zhiyao.api.controller.order;

import com.zhiyao.api.util.SecurityUtils;
import com.zhiyao.application.service.OrderService;
import com.zhiyao.common.result.Result;
import com.zhiyao.common.result.PageResult;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

/**
 * 订单接口
 */
@Tag(name = "订单管理", description = "订单创建、查询、状态管理相关接口")
@RestController
@RequestMapping("/orders")
@RequiredArgsConstructor
public class OrderController {

    private final OrderService orderService;

    @Operation(summary = "创建订单", description = "用户提交订单")
    @PostMapping
    public Result<Long> createOrder(@RequestBody Map<String, Object> orderDTO) {
        Long userId = SecurityUtils.getCurrentUserId();
        Long orderId = orderService.createOrder(userId, orderDTO);
        return Result.success("订单创建成功", orderId);
    }

    @Operation(summary = "获取订单列表", description = "获取用户订单列表")
    @GetMapping
    public Result<PageResult<Map<String, Object>>> getOrderList(
            @Parameter(description = "订单状态") @RequestParam(value = "status", required = false) Integer status,
            @Parameter(description = "页码") @RequestParam(value = "pageNum", defaultValue = "1") Integer pageNum,
            @Parameter(description = "每页条数") @RequestParam(value = "pageSize", defaultValue = "10") Integer pageSize) {
        Long userId = SecurityUtils.getCurrentUserId();
        PageResult<Map<String, Object>> result = orderService.getUserOrders(userId, status, pageNum, pageSize);
        return Result.success(result);
    }

    @Operation(summary = "获取订单详情", description = "根据订单ID获取详细信息")
    @GetMapping("/{id}")
    public Result<Map<String, Object>> getOrderDetail(
            @Parameter(description = "订单ID") @PathVariable("id") Long id) {
        Long userId = SecurityUtils.getCurrentUserId();
        Map<String, Object> detail = orderService.getOrderDetail(id, userId);
        return Result.success(detail);
    }

    @Operation(summary = "取消订单", description = "用户取消订单")
    @PutMapping("/{id}/cancel")
    public Result<Void> cancelOrder(
            @Parameter(description = "订单ID") @PathVariable("id") Long id,
            @Parameter(description = "取消原因") @RequestParam("reason") String reason) {
        Long userId = SecurityUtils.getCurrentUserId();
        orderService.cancelOrder(id, userId, reason);
        return Result.success();
    }

    @Operation(summary = "模拟支付", description = "模拟订单支付")
    @PostMapping("/{id}/pay")
    public Result<Void> payOrder(
            @Parameter(description = "订单ID") @PathVariable("id") Long id) {
        Long userId = SecurityUtils.getCurrentUserId();
        orderService.payOrder(id, userId);
        return Result.success();
    }

    @Operation(summary = "确认收货", description = "用户确认收货")
    @PutMapping("/{id}/confirm")
    public Result<Void> confirmReceive(
            @Parameter(description = "订单ID") @PathVariable("id") Long id) {
        Long userId = SecurityUtils.getCurrentUserId();
        orderService.confirmReceive(id, userId);
        return Result.success();
    }
}
