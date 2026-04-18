package com.zhiyao.application.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.zhiyao.application.service.OrderService;
import com.zhiyao.application.service.RiderService;
import com.zhiyao.common.enums.OrderStatus;
import com.zhiyao.common.exception.BusinessException;
import com.zhiyao.common.result.PageResult;
import com.zhiyao.common.result.ResultCode;
import com.zhiyao.infrastructure.persistence.mapper.DeliveryExceptionMapper;
import com.zhiyao.infrastructure.persistence.mapper.OrderMapper;
import com.zhiyao.infrastructure.persistence.mapper.RiderMapper;
import com.zhiyao.infrastructure.persistence.mapper.UserMapper;
import com.zhiyao.infrastructure.persistence.po.DeliveryExceptionPO;
import com.zhiyao.infrastructure.persistence.po.OrderPO;
import com.zhiyao.infrastructure.persistence.po.RiderPO;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.LocalTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * 骑手服务实现类
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class RiderServiceImpl implements RiderService {

    private final RiderMapper riderMapper;
    private final OrderMapper orderMapper;
    private final OrderService orderService;
    private final UserMapper userMapper;
    private final DeliveryExceptionMapper deliveryExceptionMapper;

    @Override
    @Transactional
    public Long applyRider(Long userId, Map<String, Object> applyDTO) {
        // 检查是否已经申请过
        RiderPO existing = riderMapper.selectByUserId(userId);
        if (existing != null) {
            throw new BusinessException(ResultCode.FAIL, "您已提交过骑手申请");
        }

        RiderPO rider = new RiderPO();
        rider.setUserId(userId);
        rider.setRealName((String) applyDTO.get("name"));  // 真实姓名
        rider.setIdCard((String) applyDTO.get("idCard"));  // 身份证号
        rider.setStatus(0);  // 未激活
        rider.setAuditStatus(0);  // 待审核
        
        // 业务字段（不会被持久化到数据库）
        rider.setPhone((String) applyDTO.get("phone"));
        rider.setOnlineStatus(0);  // 离线
        rider.setRating(new BigDecimal("5.0"));
        // 初始化统计字段
        rider.setTodayOrders(0);
        rider.setTotalOrders(0);
        rider.setTodayIncome(BigDecimal.ZERO);
        rider.setTotalIncome(BigDecimal.ZERO);
        rider.setDeleted(0);

        riderMapper.insert(rider);
        log.info("骑手入职申请: userId={}, riderId={}, name={}", userId, rider.getId(), applyDTO.get("name"));
        return rider.getId();
    }

    public Map<String, Object> getHomeData(Long userId) {
        // 查询骑手信息
        RiderPO rider = riderMapper.selectByUserId(userId);//32
        if (rider == null) {
            throw new BusinessException(ResultCode.RIDER_NOT_EXIST);
        }

        Map<String, Object> homeData = new HashMap<>();
        
        // 计算今日时间范围
        LocalDateTime todayStart = LocalDate.now().atStartOfDay();
        LocalDateTime todayEnd = LocalDate.now().atTime(LocalTime.MAX);
        
        // 待接单数量（所有待配送状态的订单）
        LambdaQueryWrapper<OrderPO> pendingWrapper = new LambdaQueryWrapper<>();
        pendingWrapper.eq(OrderPO::getStatus, OrderStatus.PENDING_DELIVERY.getCode())
                     .eq(OrderPO::getDeleted, 0);
        Long pendingCount = orderMapper.selectCount(pendingWrapper);
        
        // 配送中订单数量（当前骑手的配送中订单）
        LambdaQueryWrapper<OrderPO> deliveringWrapper = new LambdaQueryWrapper<>();
        deliveringWrapper.eq(OrderPO::getRiderId, rider.getId())
                        .eq(OrderPO::getStatus, OrderStatus.DELIVERING.getCode())
                        .eq(OrderPO::getDeleted, 0);
        Long deliveringCount = orderMapper.selectCount(deliveringWrapper);
        
        // 今日完成订单数（当前骑手，今日完成的订单）- 使用completeTime，如为NULL则使用updateTime作为备选
        LambdaQueryWrapper<OrderPO> completedTodayWrapper = new LambdaQueryWrapper<>();
        completedTodayWrapper.eq(OrderPO::getRiderId, rider.getId())
                            .eq(OrderPO::getStatus, OrderStatus.COMPLETED.getCode())
                            .and(wrapper -> wrapper
                                .between(OrderPO::getCompleteTime, todayStart, todayEnd)
                                .or()
                                .and(w -> w.isNull(OrderPO::getCompleteTime)
                                          .between(OrderPO::getUpdateTime, todayStart, todayEnd))
                            )
                            .eq(OrderPO::getDeleted, 0);
        Long todayCompleted = orderMapper.selectCount(completedTodayWrapper);
        
        // 今日收入 - 实时计算配送费总和
        List<OrderPO> todayOrders = orderMapper.selectList(completedTodayWrapper);
        BigDecimal todayEarnings = todayOrders.stream()
                .map(o -> o.getDeliveryFee() != null ? o.getDeliveryFee() : BigDecimal.ZERO)
                .reduce(BigDecimal.ZERO, BigDecimal::add);
        
        // 累计完成订单数（当前骑手的所有已完成订单）
        LambdaQueryWrapper<OrderPO> totalCompletedWrapper = new LambdaQueryWrapper<>();
        totalCompletedWrapper.eq(OrderPO::getRiderId, rider.getId())
                            .eq(OrderPO::getStatus, OrderStatus.COMPLETED.getCode())
                            .eq(OrderPO::getDeleted, 0);
        Long totalCompleted = orderMapper.selectCount(totalCompletedWrapper);
        
        // 累计收入 - 实时计算
        List<OrderPO> allCompletedOrders = orderMapper.selectList(totalCompletedWrapper);
        BigDecimal totalEarnings = allCompletedOrders.stream()
                .map(o -> o.getDeliveryFee() != null ? o.getDeliveryFee() : BigDecimal.ZERO)
                .reduce(BigDecimal.ZERO, BigDecimal::add);
        
        homeData.put("pendingCount", pendingCount);
        homeData.put("deliveringCount", deliveringCount);
        homeData.put("todayCompleted", todayCompleted);
        homeData.put("todayEarnings", todayEarnings);
        homeData.put("totalCompleted", totalCompleted);
        homeData.put("totalEarnings", totalEarnings);
        
        log.info("骑手首页数据: riderId={}, 待接单={}, 配送中={}, 今日完成={}, 今日收入={}, 累计配送={}, 累计收入={}",
                rider.getId(), pendingCount, deliveringCount, todayCompleted, todayEarnings, totalCompleted, totalEarnings);
        
        return homeData;
    }

    @Override
    public Map<String, Object> getRiderInfo(Long riderId) {
        RiderPO rider = riderMapper.selectById(riderId);
        if (rider == null || rider.getDeleted() == 1) {
            throw new BusinessException(ResultCode.RIDER_NOT_EXIST);
        }
        return convertToMap(rider);
    }

    @Override
    @Transactional
    public void updateRiderInfo(Long riderId, Map<String, Object> riderDTO) {
        RiderPO rider = riderMapper.selectById(riderId);
        if (rider == null) {
            throw new BusinessException(ResultCode.RIDER_NOT_EXIST);
        }

        // 更新真实姓名
        if (riderDTO.containsKey("name")) {
            rider.setRealName((String) riderDTO.get("name"));
        }
        // phone 和 avatar 是非数据库字段，不需要持久化
        if (riderDTO.containsKey("phone")) {
            rider.setPhone((String) riderDTO.get("phone"));
        }
        if (riderDTO.containsKey("avatar")) {
            rider.setAvatar((String) riderDTO.get("avatar"));
        }

        riderMapper.updateById(rider);
        log.info("骑手信息更新: riderId={}", riderId);
    }

    @Override
    @Transactional
    public void updateOnlineStatus(Long userId, Integer status) {
        // 通过 userId 查询骑手
        RiderPO rider = riderMapper.selectByUserId(userId);
        if (rider == null) {
            throw new BusinessException(ResultCode.RIDER_NOT_EXIST);
        }

        // 更新 status 字段（0-离线 1-接单中）
        rider.setStatus(status);
        riderMapper.updateById(rider);
        log.info("骑手{}状态: userId={}, riderId={}", status == 1 ? "上线" : "下线", userId, rider.getId());
    }

    @Override
    public PageResult<Map<String, Object>> getPendingDeliveryOrders(Integer pageNum, Integer pageSize) {
        return orderService.getPendingDeliveryOrders(pageNum, pageSize);
    }

    @Override
    @Transactional
    public void acceptOrder(Long orderId, Long riderId) {
        orderService.riderAcceptOrder(orderId, riderId);

        // 更新骑手统计
        RiderPO rider = riderMapper.selectById(riderId);
        if (rider != null) {
            Integer todayOrders = (rider.getTodayOrders() != null ? rider.getTodayOrders() : 0) + 1;
            Integer totalOrders = (rider.getTotalOrders() != null ? rider.getTotalOrders() : 0) + 1;
            rider.setTodayOrders(todayOrders);
            rider.setTotalOrders(totalOrders);
            riderMapper.updateById(rider);
            log.info("骑手接单统计更新: riderId={}, todayOrders={}, totalOrders={}", riderId, todayOrders, totalOrders);
        }
    }

    @Override
    @Transactional
    public void startDelivery(Long orderId, Long riderId) {
        // 验证订单属于该骑手
        OrderPO order = orderMapper.selectById(orderId);
        if (order == null || !riderId.equals(order.getRiderId())) {
            throw new BusinessException(ResultCode.ORDER_NOT_EXIST);
        }

        // 检查订单状态是否为待配送
        if (!order.getStatus().equals(OrderStatus.PENDING_DELIVERY.getCode())) {
            throw new BusinessException(ResultCode.ORDER_STATUS_ERROR, "订单状态错误");
        }

        // 更新订单状态为配送中
        order.setStatus(OrderStatus.DELIVERING.getCode());
        order.setDeliveryTime(LocalDateTime.now());
        orderMapper.updateById(order);

        log.info("骑手开始配送: orderId={}, riderId={}", orderId, riderId);
    }

    @Override
    @Transactional
    public void completeDelivery(Long orderId, Long riderId) {
        orderService.riderCompleteDelivery(orderId, riderId);

        // 更新骑手收入（配送费）
        OrderPO order = orderMapper.selectById(orderId);
        if (order != null) {
            RiderPO rider = riderMapper.selectById(riderId);
            if (rider != null) {
                BigDecimal deliveryFee = order.getDeliveryFee() != null ? order.getDeliveryFee() : BigDecimal.ZERO;
                BigDecimal todayIncome = (rider.getTodayIncome() != null ? rider.getTodayIncome() : BigDecimal.ZERO).add(deliveryFee);
                BigDecimal totalIncome = (rider.getTotalIncome() != null ? rider.getTotalIncome() : BigDecimal.ZERO).add(deliveryFee);
                rider.setTodayIncome(todayIncome);
                rider.setTotalIncome(totalIncome);
                riderMapper.updateById(rider);
                log.info("骑手完成配送收入更新: riderId={}, deliveryFee={}, todayIncome={}, totalIncome={}", 
                        riderId, deliveryFee, todayIncome, totalIncome);
            }
        }
    }

    @Override
    public PageResult<Map<String, Object>> getDeliveringOrders(Long riderId, Integer pageNum, Integer pageSize) {
        return orderService.getRiderDeliveringOrders(riderId, pageNum, pageSize);
    }

    @Override
    public PageResult<Map<String, Object>> getCompletedOrders(Long riderId, Integer pageNum, Integer pageSize) {
        LambdaQueryWrapper<OrderPO> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(OrderPO::getRiderId, riderId)
               .eq(OrderPO::getStatus, OrderStatus.COMPLETED.getCode())
               .eq(OrderPO::getDeleted, 0)
               .orderByDesc(OrderPO::getCompleteTime);

        Page<OrderPO> page = new Page<>(pageNum, pageSize);
        Page<OrderPO> result = orderMapper.selectPage(page, wrapper);

        List<Map<String, Object>> records = result.getRecords().stream()
                .map(this::convertOrderToMap)
                .collect(Collectors.toList());

        return PageResult.of(result.getTotal(), records, result.getCurrent(), result.getSize());
    }

    @Override
    @Transactional
    public void reportException(Long orderId, Long riderId, Map<String, Object> exceptionDTO) {
        // 验证订单属于该骑手
        OrderPO order = orderMapper.selectById(orderId);
        if (order == null || !riderId.equals(order.getRiderId())) {
            throw new BusinessException(ResultCode.ORDER_NOT_EXIST);
        }

        // 创建配送异常记录
        DeliveryExceptionPO exception = new DeliveryExceptionPO();
        exception.setOrderId(orderId);
        exception.setRiderId(riderId);
        
        // 从前端传递的type字符串映射到数据库类型码
        String typeStr = (String) exceptionDTO.get("type");
        Integer typeCode = mapExceptionType(typeStr);
        exception.setType(typeCode);
        
        exception.setDescription((String) exceptionDTO.get("description"));
        exception.setImages((String) exceptionDTO.get("images"));
        exception.setStatus(0);  // 0-待处理
        
        deliveryExceptionMapper.insert(exception);
        
        log.info("配送异常上报成功: orderId={}, riderId={}, type={}, exceptionId={}", 
                orderId, riderId, typeStr, exception.getId());
    }
    
    /**
     * 将前端传递的异常类型字符串映射为数据库类型码
     * @param typeStr 异常类型字符串
     * @return 类型码：1-无法联系用户 2-地址异常 3-其他
     */
    private Integer mapExceptionType(String typeStr) {
        if (typeStr == null) {
            return 3;  // 默认为其他
        }
        
        switch (typeStr) {
            case "客户不在":
            case "无法联系用户":
                return 1;
            case "地址错误":
            case "地址异常":
                return 2;
            default:
                return 3;  // 其他
        }
    }

    @Override
    public Map<String, Object> getRiderStatistics(Long userId) {
        // 通过 userId 查询骑手
        RiderPO rider = riderMapper.selectByUserId(userId);
        if (rider == null) {
            throw new BusinessException(ResultCode.RIDER_NOT_EXIST);
        }
        
        log.info("开始查询骑手统计数据: userId={}, riderId={}", userId, rider.getId());

        // 计算今日时间范围
        LocalDateTime todayStart = LocalDate.now().atStartOfDay();
        LocalDateTime todayEnd = LocalDate.now().atTime(LocalTime.MAX);
        log.info("今日时间范围: {} 到 {}", todayStart, todayEnd);
        
        // 今日完成订单数 - 实时查询（使用completeTime，如为NULL则使用updateTime作为备选）
        LambdaQueryWrapper<OrderPO> todayCompletedWrapper = new LambdaQueryWrapper<>();
        todayCompletedWrapper.eq(OrderPO::getRiderId, rider.getId())
                            .eq(OrderPO::getStatus, OrderStatus.COMPLETED.getCode())
                            .and(wrapper -> wrapper
                                .between(OrderPO::getCompleteTime, todayStart, todayEnd)
                                .or()
                                .and(w -> w.isNull(OrderPO::getCompleteTime)
                                          .between(OrderPO::getUpdateTime, todayStart, todayEnd))
                            )
                            .eq(OrderPO::getDeleted, 0);
        Long todayCompleted = orderMapper.selectCount(todayCompletedWrapper);
        log.info("今日完成订单数查询结果: {}", todayCompleted);
        
        // 今日收入 - 实时计算
        List<OrderPO> todayOrders = orderMapper.selectList(todayCompletedWrapper);
        log.info("今日订单列表数量: {}", todayOrders.size());
        if (!todayOrders.isEmpty()) {
            for (OrderPO order : todayOrders) {
                log.info("今日订单详情: orderId={}, riderId={}, status={}, completeTime={}, updateTime={}, deliveryFee={}", 
                        order.getId(), order.getRiderId(), order.getStatus(), 
                        order.getCompleteTime(), order.getUpdateTime(), order.getDeliveryFee());
            }
        }
        BigDecimal todayEarnings = todayOrders.stream()
                .map(o -> o.getDeliveryFee() != null ? o.getDeliveryFee() : BigDecimal.ZERO)
                .reduce(BigDecimal.ZERO, BigDecimal::add);
        log.info("今日收入计算结果: {}", todayEarnings);
        
        // 累计订单数 - 实时查询
        LambdaQueryWrapper<OrderPO> totalCompletedWrapper = new LambdaQueryWrapper<>();
        totalCompletedWrapper.eq(OrderPO::getRiderId, rider.getId())
                            .eq(OrderPO::getStatus, OrderStatus.COMPLETED.getCode())
                            .eq(OrderPO::getDeleted, 0);
        Long totalCompleted = orderMapper.selectCount(totalCompletedWrapper);
        log.info("累计完成订单数查询结果: {}", totalCompleted);
        
        // 累计收入 - 实时计算
        List<OrderPO> allCompletedOrders = orderMapper.selectList(totalCompletedWrapper);
        log.info("累计订单列表数量: {}", allCompletedOrders.size());
        if (!allCompletedOrders.isEmpty()) {
            for (OrderPO order : allCompletedOrders) {
                log.info("累计订单详情: orderId={}, riderId={}, status={}, completeTime={}, deliveryFee={}", 
                        order.getId(), order.getRiderId(), order.getStatus(), 
                        order.getCompleteTime(), order.getDeliveryFee());
            }
        }
        BigDecimal totalEarnings = allCompletedOrders.stream()
                .map(o -> o.getDeliveryFee() != null ? o.getDeliveryFee() : BigDecimal.ZERO)
                .reduce(BigDecimal.ZERO, BigDecimal::add);
        log.info("累计收入计算结果: {}", totalEarnings);
        
        // 本月时间范围
        LocalDateTime monthStart = LocalDate.now().withDayOfMonth(1).atStartOfDay();
        
        // 本月订单数和收入（使用completeTime，如为NULL则使用updateTime作为备选）
        LambdaQueryWrapper<OrderPO> monthCompletedWrapper = new LambdaQueryWrapper<>();
        monthCompletedWrapper.eq(OrderPO::getRiderId, rider.getId())
                            .eq(OrderPO::getStatus, OrderStatus.COMPLETED.getCode())
                            .and(wrapper -> wrapper
                                .between(OrderPO::getCompleteTime, monthStart, todayEnd)
                                .or()
                                .and(w -> w.isNull(OrderPO::getCompleteTime)
                                          .between(OrderPO::getUpdateTime, monthStart, todayEnd))
                            )
                            .eq(OrderPO::getDeleted, 0);
        Long monthCompleted = orderMapper.selectCount(monthCompletedWrapper);
        List<OrderPO> monthOrders = orderMapper.selectList(monthCompletedWrapper);
        BigDecimal monthEarnings = monthOrders.stream()
                .map(o -> o.getDeliveryFee() != null ? o.getDeliveryFee() : BigDecimal.ZERO)
                .reduce(BigDecimal.ZERO, BigDecimal::add);

        Map<String, Object> stats = new HashMap<>();
        stats.put("todayOrders", todayCompleted);
        stats.put("totalOrders", totalCompleted);
        stats.put("todayEarnings", todayEarnings);
        stats.put("totalEarnings", totalEarnings);
        stats.put("thisMonthOrders", monthCompleted);
        stats.put("thisMonthEarnings", monthEarnings);
        
        // 完成率（简化计算）
        Integer completionRate = 100;
        stats.put("completionRate", completionRate);
        
        stats.put("rating", rider.getRating() != null ? rider.getRating() : BigDecimal.valueOf(5.0));
        stats.put("onlineStatus", rider.getStatus());
        
        log.info("骑手统计数据最终结果: riderId={}, 今日订单={}, 累计订单={}, 今日收入={}, 累计收入={}",
                rider.getId(), todayCompleted, totalCompleted, todayEarnings, totalEarnings);

        return stats;
    }

    private Map<String, Object> convertToMap(RiderPO rider) {
        Map<String, Object> map = new HashMap<>();
        map.put("id", rider.getId());
        map.put("name", rider.getRealName());  // 从 rider.realName 获取
        map.put("phone", rider.getPhone());
        map.put("avatar", rider.getAvatar());
        map.put("status", rider.getStatus());
        map.put("onlineStatus", rider.getOnlineStatus());
        map.put("todayOrders", rider.getTodayOrders());
        map.put("totalOrders", rider.getTotalOrders());
        map.put("todayIncome", rider.getTodayIncome());
        map.put("totalIncome", rider.getTotalIncome());
        map.put("rating", rider.getRating());
        map.put("auditStatus", rider.getAuditStatus());
        return map;
    }

    private Map<String, Object> convertOrderToMap(OrderPO order) {
        Map<String, Object> map = new HashMap<>();
        map.put("id", order.getId());
        map.put("orderNo", order.getOrderNo());
        map.put("receiverName", order.getReceiverName());
        map.put("receiverPhone", order.getReceiverPhone());
        map.put("receiverAddress", order.getReceiverAddress());
        map.put("customerName", order.getReceiverName());
        map.put("customerPhone", order.getReceiverPhone());
        map.put("customerAddress", order.getReceiverAddress());
        map.put("deliveryFee", order.getDeliveryFee());
        map.put("totalAmount", order.getTotalAmount());
        map.put("status", order.getStatus());
        map.put("completeTime", order.getCompleteTime());
        // TODO: 添加商家信息
        map.put("merchantName", "药店");
        map.put("merchantAddress", "");
        return map;
    }
}
