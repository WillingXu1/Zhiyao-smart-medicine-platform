package com.zhiyao.application.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.zhiyao.application.service.OrderService;
import com.zhiyao.common.enums.OrderStatus;
import com.zhiyao.common.exception.BusinessException;
import com.zhiyao.common.result.PageResult;
import com.zhiyao.common.result.ResultCode;
import com.zhiyao.infrastructure.persistence.mapper.MedicineMapper;
import com.zhiyao.infrastructure.persistence.mapper.MerchantMapper;
import com.zhiyao.infrastructure.persistence.mapper.OrderItemMapper;
import com.zhiyao.infrastructure.persistence.mapper.OrderMapper;
import com.zhiyao.infrastructure.persistence.po.MedicinePO;
import com.zhiyao.infrastructure.persistence.po.MerchantPO;
import com.zhiyao.infrastructure.persistence.po.OrderItemPO;
import com.zhiyao.infrastructure.persistence.po.OrderPO;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.stream.Collectors;

/**
 * 订单服务实现类
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class OrderServiceImpl implements OrderService {

    private final OrderMapper orderMapper;
    private final OrderItemMapper orderItemMapper;
    private final MedicineMapper medicineMapper;
    private final MerchantMapper merchantMapper;

    private static final BigDecimal DELIVERY_FEE = new BigDecimal("5.00");

    @Override
    @Transactional
    public Long createOrder(Long userId, Map<String, Object> orderDTO) {
        // 生成订单号
        String orderNo = generateOrderNo();

        // 获取订单项
        @SuppressWarnings("unchecked")
        List<Map<String, Object>> items = (List<Map<String, Object>>) orderDTO.get("items");
        if (items == null || items.isEmpty()) {
            throw new BusinessException(ResultCode.ORDER_ITEM_EMPTY);
        }

        // 计算总金额
        BigDecimal totalAmount = BigDecimal.ZERO;
        Long merchantId = null;
        List<OrderItemPO> orderItems = new ArrayList<>();

        for (Map<String, Object> item : items) {
            Long medicineId = Long.valueOf(item.get("medicineId").toString());
            Integer quantity = Integer.valueOf(item.get("quantity").toString());

            MedicinePO medicine = medicineMapper.selectById(medicineId);
            if (medicine == null || medicine.getStatus() != 1) {
                throw new BusinessException(ResultCode.MEDICINE_NOT_EXIST);
            }

            if (medicine.getStock() < quantity) {
                throw new BusinessException(ResultCode.MEDICINE_STOCK_NOT_ENOUGH);
            }

            // 设置商家ID（所有药品必须来自同一商家）
            if (merchantId == null) {
                merchantId = medicine.getMerchantId();
            } else if (!merchantId.equals(medicine.getMerchantId())) {
                throw new BusinessException(ResultCode.ORDER_MULTI_MERCHANT);
            }

            BigDecimal subtotal = medicine.getPrice().multiply(new BigDecimal(quantity));
            totalAmount = totalAmount.add(subtotal);

            OrderItemPO orderItem = new OrderItemPO();
            orderItem.setMedicineId(medicineId);
            orderItem.setMedicineName(medicine.getName());
            orderItem.setMedicineImage(medicine.getImage());
            orderItem.setSpecification(medicine.getSpecification());
            orderItem.setPrice(medicine.getPrice());
            orderItem.setQuantity(quantity);
            orderItem.setSubtotal(subtotal);
            orderItems.add(orderItem);

            // 扣减库存
            medicine.setStock(medicine.getStock() - quantity);
            medicine.setSales(medicine.getSales() + quantity);
            medicineMapper.updateById(medicine);
        }

        // 创建订单
        OrderPO order = new OrderPO();
        order.setOrderNo(orderNo);
        order.setUserId(userId);
        order.setMerchantId(merchantId);
        order.setAddressId(Long.valueOf(orderDTO.get("addressId").toString()));
        order.setReceiverName((String) orderDTO.get("receiverName"));
        order.setReceiverPhone((String) orderDTO.get("receiverPhone"));
        order.setReceiverAddress((String) orderDTO.get("receiverAddress"));
        order.setTotalAmount(totalAmount);
        order.setDeliveryFee(DELIVERY_FEE);
        order.setPayAmount(totalAmount.add(DELIVERY_FEE));
        order.setStatus(OrderStatus.PENDING_PAYMENT.getCode());
        order.setRemark((String) orderDTO.get("remark"));
        order.setDeleted(0);

        orderMapper.insert(order);

        // 创建订单项
        for (OrderItemPO orderItem : orderItems) {
            orderItem.setOrderId(order.getId());
            orderItemMapper.insert(orderItem);
        }

        log.info("订单创建成功: orderId={}, orderNo={}, userId={}, totalAmount={}", 
                order.getId(), orderNo, userId, order.getPayAmount());

        return order.getId();
    }

    @Override
    public Map<String, Object> getOrderDetail(Long orderId, Long userId) {
        OrderPO order = orderMapper.selectById(orderId);
        if (order == null || order.getDeleted() == 1) {
            throw new BusinessException(ResultCode.ORDER_NOT_EXIST);
        }

        // 验证订单归属（如果传入了userId）
        if (userId != null && !order.getUserId().equals(userId)) {
            throw new BusinessException(ResultCode.ORDER_NOT_EXIST);
        }

        // 获取订单项
        List<OrderItemPO> items = orderItemMapper.selectByOrderId(orderId);

        return convertToDetailMap(order, items);
    }

    @Override
    public PageResult<Map<String, Object>> getUserOrders(Long userId, Integer status, Integer pageNum, Integer pageSize) {
        LambdaQueryWrapper<OrderPO> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(OrderPO::getUserId, userId)
               .eq(OrderPO::getDeleted, 0)
               .orderByDesc(OrderPO::getCreateTime);

        if (status != null && status >= 0) {
            wrapper.eq(OrderPO::getStatus, status);
        }

        Page<OrderPO> page = new Page<>(pageNum, pageSize);
        Page<OrderPO> result = orderMapper.selectPage(page, wrapper);

        List<Map<String, Object>> records = result.getRecords().stream()
                .map(order -> {
                    List<OrderItemPO> items = orderItemMapper.selectByOrderId(order.getId());
                    return convertToListMap(order, items);
                })
                .collect(Collectors.toList());

        return PageResult.of(result.getTotal(), records, result.getCurrent(), result.getSize());
    }

    @Override
    @Transactional
    public void cancelOrder(Long orderId, Long userId, String reason) {
        OrderPO order = orderMapper.selectById(orderId);
        validateOrder(order, userId);

        if (order.getStatus() > OrderStatus.PENDING_ACCEPT.getCode()) {
            throw new BusinessException(ResultCode.ORDER_STATUS_ERROR, "当前状态不可取消");
        }

        order.setStatus(OrderStatus.CANCELLED.getCode());
        order.setCancelReason(reason);
        orderMapper.updateById(order);

        // 恢复库存
        restoreStock(orderId);

        log.info("订单取消: orderId={}, userId={}, reason={}", orderId, userId, reason);
    }

    @Override
    @Transactional
    public void payOrder(Long orderId, Long userId) {
        OrderPO order = orderMapper.selectById(orderId);
        validateOrder(order, userId);

        if (!order.getStatus().equals(OrderStatus.PENDING_PAYMENT.getCode())) {
            throw new BusinessException(ResultCode.ORDER_STATUS_ERROR, "订单状态错误");
        }

        order.setStatus(OrderStatus.PENDING_ACCEPT.getCode());
        order.setPayTime(LocalDateTime.now());
        order.setPaymentType(1);  // 模拟支付
        orderMapper.updateById(order);

        log.info("订单支付成功（模拟）: orderId={}, userId={}", orderId, userId);
    }

    @Override
    @Transactional
    public void confirmReceive(Long orderId, Long userId) {
        OrderPO order = orderMapper.selectById(orderId);
        validateOrder(order, userId);

        if (!order.getStatus().equals(OrderStatus.DELIVERING.getCode())) {
            throw new BusinessException(ResultCode.ORDER_STATUS_ERROR, "订单状态错误");
        }

        order.setStatus(OrderStatus.COMPLETED.getCode());
        order.setCompleteTime(LocalDateTime.now());
        orderMapper.updateById(order);

        log.info("订单确认收货: orderId={}, userId={}", orderId, userId);
    }

    @Override
    @Transactional
    public void acceptOrder(Long orderId, Long merchantId) {
        OrderPO order = orderMapper.selectById(orderId);
        if (order == null || !order.getMerchantId().equals(merchantId)) {
            throw new BusinessException(ResultCode.ORDER_NOT_EXIST);
        }

        if (!order.getStatus().equals(OrderStatus.PENDING_ACCEPT.getCode())) {
            throw new BusinessException(ResultCode.ORDER_STATUS_ERROR, "订单状态错误");
        }

        order.setStatus(OrderStatus.PENDING_DELIVERY.getCode());
        order.setAcceptTime(LocalDateTime.now());
        orderMapper.updateById(order);

        log.info("商家接单: orderId={}, merchantId={}", orderId, merchantId);
    }

    @Override
    @Transactional
    public void rejectOrder(Long orderId, Long merchantId, String reason) {
        OrderPO order = orderMapper.selectById(orderId);
        if (order == null || !order.getMerchantId().equals(merchantId)) {
            throw new BusinessException(ResultCode.ORDER_NOT_EXIST);
        }

        if (!order.getStatus().equals(OrderStatus.PENDING_ACCEPT.getCode())) {
            throw new BusinessException(ResultCode.ORDER_STATUS_ERROR, "订单状态错误");
        }

        order.setStatus(OrderStatus.MERCHANT_REJECTED.getCode());
        order.setRejectReason(reason);
        orderMapper.updateById(order);

        // 恢复库存
        restoreStock(orderId);

        log.info("商家拒单: orderId={}, merchantId={}, reason={}", orderId, merchantId, reason);
    }

    @Override
    public PageResult<Map<String, Object>> getMerchantOrders(Long merchantId, Integer status, Integer pageNum, Integer pageSize) {
        LambdaQueryWrapper<OrderPO> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(OrderPO::getMerchantId, merchantId)
               .eq(OrderPO::getDeleted, 0)
               .orderByDesc(OrderPO::getCreateTime);

        if (status != null && status >= 0) {
            wrapper.eq(OrderPO::getStatus, status);
        }

        Page<OrderPO> page = new Page<>(pageNum, pageSize);
        Page<OrderPO> result = orderMapper.selectPage(page, wrapper);

        List<Map<String, Object>> records = result.getRecords().stream()
                .map(order -> {
                    List<OrderItemPO> items = orderItemMapper.selectByOrderId(order.getId());
                    return convertToListMap(order, items);
                })
                .collect(Collectors.toList());

        return PageResult.of(result.getTotal(), records, result.getCurrent(), result.getSize());
    }

    @Override
    @Transactional
    public void riderAcceptOrder(Long orderId, Long riderId) {
        OrderPO order = orderMapper.selectById(orderId);
        if (order == null) {
            throw new BusinessException(ResultCode.ORDER_NOT_EXIST);
        }

        if (!order.getStatus().equals(OrderStatus.PENDING_DELIVERY.getCode())) {
            throw new BusinessException(ResultCode.ORDER_STATUS_ERROR, "订单状态错误");
        }

        // 骑手接单，仅分配骑手，状态保持为待配送（3）
        // 待骑手取货后调用 startDelivery 才变为配送中（4）
        order.setRiderId(riderId);
        order.setAcceptTime(LocalDateTime.now());  // 记录接单时间
        orderMapper.updateById(order);

        log.info("骑手接单: orderId={}, riderId={}, status={}", orderId, riderId, order.getStatus());
    }

    @Override
    @Transactional
    public void riderCompleteDelivery(Long orderId, Long riderId) {
        OrderPO order = orderMapper.selectById(orderId);
        if (order == null || !order.getRiderId().equals(riderId)) {
            throw new BusinessException(ResultCode.ORDER_NOT_EXIST);
        }

        if (!order.getStatus().equals(OrderStatus.DELIVERING.getCode())) {
            throw new BusinessException(ResultCode.ORDER_STATUS_ERROR, "订单状态错误");
        }

        order.setStatus(OrderStatus.COMPLETED.getCode());
        order.setCompleteTime(LocalDateTime.now());
        orderMapper.updateById(order);

        log.info("骑手完成配送: orderId={}, riderId={}", orderId, riderId);
    }

    @Override
    public PageResult<Map<String, Object>> getPendingDeliveryOrders(Integer pageNum, Integer pageSize) {
        LambdaQueryWrapper<OrderPO> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(OrderPO::getStatus, OrderStatus.PENDING_DELIVERY.getCode())
               .eq(OrderPO::getDeleted, 0)
               .orderByAsc(OrderPO::getAcceptTime);

        Page<OrderPO> page = new Page<>(pageNum, pageSize);
        Page<OrderPO> result = orderMapper.selectPage(page, wrapper);

        List<Map<String, Object>> records = result.getRecords().stream()
                .map(order -> {
                    List<OrderItemPO> items = orderItemMapper.selectByOrderId(order.getId());
                    return convertToListMap(order, items);
                })
                .collect(Collectors.toList());

        return PageResult.of(result.getTotal(), records, result.getCurrent(), result.getSize());
    }

    @Override
    public PageResult<Map<String, Object>> getRiderDeliveringOrders(Long riderId, Integer pageNum, Integer pageSize) {
        LambdaQueryWrapper<OrderPO> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(OrderPO::getRiderId, riderId)
               .in(OrderPO::getStatus, OrderStatus.PENDING_DELIVERY.getCode(), OrderStatus.DELIVERING.getCode())  // 同时查询待配送和配送中
               .eq(OrderPO::getDeleted, 0)
               .orderByDesc(OrderPO::getAcceptTime);  // 按接单时间排序

        Page<OrderPO> page = new Page<>(pageNum, pageSize);
        Page<OrderPO> result = orderMapper.selectPage(page, wrapper);

        List<Map<String, Object>> records = result.getRecords().stream()
                .map(order -> {
                    List<OrderItemPO> items = orderItemMapper.selectByOrderId(order.getId());
                    return convertToListMap(order, items);
                })
                .collect(Collectors.toList());

        return PageResult.of(result.getTotal(), records, result.getCurrent(), result.getSize());
    }

    // ============ 私有方法 ============

    private void validateOrder(OrderPO order, Long userId) {
        if (order == null || order.getDeleted() == 1) {
            throw new BusinessException(ResultCode.ORDER_NOT_EXIST);
        }
        if (userId != null && !order.getUserId().equals(userId)) {
            throw new BusinessException(ResultCode.ORDER_NOT_EXIST);
        }
    }

    private void restoreStock(Long orderId) {
        List<OrderItemPO> items = orderItemMapper.selectByOrderId(orderId);
        for (OrderItemPO item : items) {
            MedicinePO medicine = medicineMapper.selectById(item.getMedicineId());
            if (medicine != null) {
                medicine.setStock(medicine.getStock() + item.getQuantity());
                medicine.setSales(medicine.getSales() - item.getQuantity());
                medicineMapper.updateById(medicine);
            }
        }
    }

    private String generateOrderNo() {
        String timestamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMddHHmmss"));
        String random = String.format("%06d", new Random().nextInt(999999));
        return timestamp + random;
    }

    private Map<String, Object> convertToListMap(OrderPO order, List<OrderItemPO> items) {
        Map<String, Object> map = new HashMap<>();
        map.put("id", order.getId());
        map.put("orderNo", order.getOrderNo());
        map.put("status", order.getStatus());
        map.put("statusText", OrderStatus.fromCode(order.getStatus()).getDesc());
        map.put("payAmount", order.getPayAmount());
        map.put("totalAmount", order.getTotalAmount());
        map.put("deliveryFee", order.getDeliveryFee());
        map.put("createTime", order.getCreateTime());
        map.put("itemCount", items.size());
        
        // 添加地址信息（骑手端需要）
        map.put("receiverName", order.getReceiverName());
        map.put("receiverPhone", order.getReceiverPhone());
        map.put("receiverAddress", order.getReceiverAddress());
        map.put("customerName", order.getReceiverName());
        map.put("customerPhone", order.getReceiverPhone());
        map.put("customerAddress", order.getReceiverAddress());
        
        // 添加药品信息
        List<Map<String, Object>> medicines = items.stream().map(item -> {
            Map<String, Object> medicine = new HashMap<>();
            medicine.put("name", item.getMedicineName());
            medicine.put("quantity", item.getQuantity());
            medicine.put("specification", item.getSpecification());
            medicine.put("price", item.getPrice());
            return medicine;
        }).collect(Collectors.toList());
        map.put("medicines", medicines);
        map.put("items", items.stream().map(this::convertItemToMap).collect(Collectors.toList()));
        
        // 查询商家信息
        if (order.getMerchantId() != null) {
            MerchantPO merchant = merchantMapper.selectById(order.getMerchantId());
            if (merchant != null) {
                map.put("merchantName", merchant.getShopName());
                map.put("merchantAddress", merchant.getFullAddress() != null ? merchant.getFullAddress() : merchant.getAddress());
                map.put("merchantPhone", merchant.getContactPhone());
            } else {
                map.put("merchantName", "未知商家");
                map.put("merchantAddress", "");
                map.put("merchantPhone", "");
            }
        } else {
            map.put("merchantName", "未知商家");
            map.put("merchantAddress", "");
            map.put("merchantPhone", "");
        }
        
        return map;
    }

    private Map<String, Object> convertToDetailMap(OrderPO order, List<OrderItemPO> items) {
        Map<String, Object> map = convertToListMap(order, items);
        map.put("userId", order.getUserId());
        map.put("merchantId", order.getMerchantId());
        map.put("riderId", order.getRiderId());
        map.put("receiverName", order.getReceiverName());
        map.put("receiverPhone", order.getReceiverPhone());
        map.put("receiverAddress", order.getReceiverAddress());
        map.put("totalAmount", order.getTotalAmount());
        map.put("deliveryFee", order.getDeliveryFee());
        map.put("payTime", order.getPayTime());
        map.put("acceptTime", order.getAcceptTime());
        map.put("deliveryTime", order.getDeliveryTime());
        map.put("completeTime", order.getCompleteTime());
        map.put("cancelReason", order.getCancelReason());
        map.put("rejectReason", order.getRejectReason());
        map.put("remark", order.getRemark());
        return map;
    }

    private Map<String, Object> convertItemToMap(OrderItemPO item) {
        Map<String, Object> map = new HashMap<>();
        map.put("id", item.getId());
        map.put("medicineId", item.getMedicineId());
        map.put("medicineName", item.getMedicineName());
        map.put("medicineImage", item.getMedicineImage());
        map.put("specification", item.getSpecification());
        map.put("price", item.getPrice());
        map.put("quantity", item.getQuantity());
        map.put("subtotal", item.getSubtotal());
        return map;
    }
}
