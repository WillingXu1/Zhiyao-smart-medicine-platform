package com.zhiyao.application.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.zhiyao.application.dto.ChangePasswordDTO;
import com.zhiyao.application.service.MerchantService;
import com.zhiyao.application.service.MedicineService;
import com.zhiyao.application.service.OrderService;
import com.zhiyao.common.exception.BusinessException;
import com.zhiyao.common.result.PageResult;
import com.zhiyao.common.result.ResultCode;
import com.zhiyao.infrastructure.persistence.mapper.MerchantMapper;
import com.zhiyao.infrastructure.persistence.mapper.MedicineMapper;
import com.zhiyao.infrastructure.persistence.mapper.OrderMapper;
import com.zhiyao.infrastructure.persistence.mapper.UserMapper;
import com.zhiyao.infrastructure.persistence.po.MedicinePO;
import com.zhiyao.infrastructure.persistence.po.MerchantPO;
import com.zhiyao.infrastructure.persistence.po.OrderPO;
import com.zhiyao.infrastructure.persistence.po.UserPO;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.LocalTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * 商家服务实现类
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class MerchantServiceImpl implements MerchantService {

    private final MerchantMapper merchantMapper;
    private final MedicineMapper medicineMapper;
    private final OrderMapper orderMapper;
    private final UserMapper userMapper;
    private final PasswordEncoder passwordEncoder;
    private final OrderService orderService;
    private final MedicineService medicineService;

    @Override
    @Transactional
    public Long applyMerchant(Long userId, Map<String, Object> applyDTO) {
        // 检查是否已经申请过
        MerchantPO existing = merchantMapper.selectByUserId(userId);
        if (existing != null) {
            throw new BusinessException(ResultCode.FAIL, "您已提交过入驻申请");
        }

        MerchantPO merchant = new MerchantPO();
        merchant.setUserId(userId);
        merchant.setShopName((String) applyDTO.get("name"));
        merchant.setContactName((String) applyDTO.get("contactName"));
        merchant.setContactPhone((String) applyDTO.get("phone"));
        merchant.setAddress((String) applyDTO.get("address"));
        merchant.setBusinessLicenseImage((String) applyDTO.get("businessLicense"));
        merchant.setDrugLicenseImage((String) applyDTO.get("pharmacistLicense"));
        // 解析营业时间
        String businessHours = (String) applyDTO.get("businessHours");
        if (businessHours != null && businessHours.contains("-")) {
            String[] times = businessHours.split("-");
            merchant.setOpenTime(times[0].trim());
            merchant.setCloseTime(times.length > 1 ? times[1].trim() : "22:00");
        } else {
            merchant.setOpenTime("08:00");
            merchant.setCloseTime("22:00");
        }
        merchant.setDeliveryFee(new BigDecimal(applyDTO.getOrDefault("deliveryFee", "5").toString()));
        merchant.setMinOrderAmount(new BigDecimal(applyDTO.getOrDefault("minOrderAmount", "20").toString()));
        merchant.setDeliveryRange(Integer.valueOf(applyDTO.getOrDefault("deliveryRange", "5").toString()));
        merchant.setStatus(0);  // 未营业
        merchant.setAuditStatus(0);  // 待审核
        merchant.setRating(new BigDecimal("5.0"));
        merchant.setMonthlySales(0);
        merchant.setDeleted(0);

        merchantMapper.insert(merchant);
        log.info("商家入驻申请: userId={}, merchantId={}, name={}", userId, merchant.getId(), merchant.getShopName());
        return merchant.getId();
    }

    @Override
    public Map<String, Object> getMerchantInfo(Long userId) {
        // 根据userId查询商家信息
        MerchantPO merchant = merchantMapper.selectByUserId(userId);
        if (merchant == null || merchant.getDeleted() == 1) {
            throw new BusinessException(ResultCode.MERCHANT_NOT_EXIST);
        }
        return convertToMap(merchant);
    }

    @Override
    @Transactional
    public void updateMerchantInfo(Long userId, Map<String, Object> merchantDTO) {
        // 根据userId查询商家信息
        MerchantPO merchant = merchantMapper.selectByUserId(userId);
        if (merchant == null) {
            throw new BusinessException(ResultCode.MERCHANT_NOT_EXIST);
        }

        if (merchantDTO.containsKey("name")) {
            merchant.setShopName((String) merchantDTO.get("name"));
        }
        if (merchantDTO.containsKey("phone")) {
            merchant.setContactPhone((String) merchantDTO.get("phone"));
        }
        if (merchantDTO.containsKey("address")) {
            merchant.setAddress((String) merchantDTO.get("address"));
        }
        if (merchantDTO.containsKey("description")) {
            merchant.setDescription((String) merchantDTO.get("description"));
        }
        // 处理openTime和closeTime字段
        if (merchantDTO.containsKey("openTime")) {
            merchant.setOpenTime((String) merchantDTO.get("openTime"));
        }
        if (merchantDTO.containsKey("closeTime")) {
            merchant.setCloseTime((String) merchantDTO.get("closeTime"));
        }
        // 兼容businessHours字段
        if (merchantDTO.containsKey("businessHours")) {
            String businessHours = (String) merchantDTO.get("businessHours");
            if (businessHours != null && businessHours.contains("-")) {
                String[] times = businessHours.split("-");
                merchant.setOpenTime(times[0].trim());
                merchant.setCloseTime(times.length > 1 ? times[1].trim() : "22:00");
            }
        }
        if (merchantDTO.containsKey("logo")) {
            merchant.setLogo((String) merchantDTO.get("logo"));
        }
        if (merchantDTO.containsKey("deliveryFee")) {
            merchant.setDeliveryFee(new BigDecimal(merchantDTO.get("deliveryFee").toString()));
        }

        merchantMapper.updateById(merchant);
        log.info("商家信息更新: userId={}, merchantId={}", userId, merchant.getId());
    }

    @Override
    @Transactional
    public void changePassword(Long userId, ChangePasswordDTO passwordDTO) {
        // 查询用户
        UserPO user = userMapper.selectById(userId);
        if (user == null) {
            throw new BusinessException(ResultCode.FAIL, "用户不存在");
        }

        // 验证原密码
        if (!passwordEncoder.matches(passwordDTO.getOldPassword(), user.getPassword())) {
            throw new BusinessException(ResultCode.FAIL, "原密码错误");
        }

        // 更新密码
        user.setPassword(passwordEncoder.encode(passwordDTO.getNewPassword()));
        userMapper.updateById(user);
        log.info("商家密码修改成功: userId={}", userId);
    }

    @Override
    public PageResult<Map<String, Object>> getMerchantOrders(Long userId, Integer status, Integer pageNum, Integer pageSize) {
        // 根据userId查询商家信息
        MerchantPO merchant = merchantMapper.selectByUserId(userId);
        if (merchant == null) {
            throw new BusinessException(ResultCode.MERCHANT_NOT_EXIST);
        }
        // 使用merchantId查询订单
        return orderService.getMerchantOrders(merchant.getId(), status, pageNum, pageSize);
    }

    @Override
    public Map<String, Object> getOrderDetail(Long orderId, Long userId) {
        // 根据userId查询商家信息
        MerchantPO merchant = merchantMapper.selectByUserId(userId);
        if (merchant == null) {
            throw new BusinessException(ResultCode.MERCHANT_NOT_EXIST);
        }
        // 获取订单详情（不需要userId校验，但需要验证订单属于该商家）
        Map<String, Object> detail = orderService.getOrderDetail(orderId, null);
        // 验证订单属于该商家
        if (detail != null && !merchant.getId().equals(detail.get("merchantId"))) {
            throw new BusinessException(ResultCode.FAIL, "无权查看该订单");
        }
        return detail;
    }

    @Override
    @Transactional
    public void acceptOrder(Long orderId, Long userId) {
        // 根据userId查询商家信息
        MerchantPO merchant = merchantMapper.selectByUserId(userId);
        if (merchant == null) {
            throw new BusinessException(ResultCode.MERCHANT_NOT_EXIST);
        }
        orderService.acceptOrder(orderId, merchant.getId());
    }

    @Override
    @Transactional
    public void rejectOrder(Long orderId, Long userId, String reason) {
        // 根据userId查询商家信息
        MerchantPO merchant = merchantMapper.selectByUserId(userId);
        if (merchant == null) {
            throw new BusinessException(ResultCode.MERCHANT_NOT_EXIST);
        }
        orderService.rejectOrder(orderId, merchant.getId(), reason);
    }

    @Override
    public PageResult<Map<String, Object>> getMerchantMedicines(Long userId, String keyword, Integer status, Integer pageNum, Integer pageSize) {
        // 根据userId查询商家信息
        MerchantPO merchant = merchantMapper.selectByUserId(userId);
        if (merchant == null) {
            throw new BusinessException(ResultCode.MERCHANT_NOT_EXIST);
        }
        Long merchantId = merchant.getId();
        
        LambdaQueryWrapper<MedicinePO> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(MedicinePO::getMerchantId, merchantId)
               .eq(MedicinePO::getDeleted, 0);

        if (StringUtils.hasText(keyword)) {
            wrapper.like(MedicinePO::getName, keyword);
        }
        if (status != null) {
            wrapper.eq(MedicinePO::getStatus, status);
        }

        wrapper.orderByDesc(MedicinePO::getCreateTime);

        Page<MedicinePO> page = new Page<>(pageNum, pageSize);
        Page<MedicinePO> result = medicineMapper.selectPage(page, wrapper);

        List<Map<String, Object>> records = result.getRecords().stream()
                .map(this::convertMedicineToMap)
                .collect(Collectors.toList());

        return PageResult.of(result.getTotal(), records, result.getCurrent(), result.getSize());
    }

    @Override
    @Transactional
    public Long addMedicine(Long userId, Map<String, Object> medicineDTO) {
        // 根据userId查询商家信息
        MerchantPO merchant = merchantMapper.selectByUserId(userId);
        if (merchant == null) {
            throw new BusinessException(ResultCode.MERCHANT_NOT_EXIST);
        }
        return medicineService.addMedicine(merchant.getId(), medicineDTO);
    }

    @Override
    @Transactional
    public void updateMedicine(Long userId, Long medicineId, Map<String, Object> medicineDTO) {
        // 根据userId查询商家信息
        MerchantPO merchant = merchantMapper.selectByUserId(userId);
        if (merchant == null) {
            throw new BusinessException(ResultCode.MERCHANT_NOT_EXIST);
        }
        medicineService.updateMedicine(merchant.getId(), medicineId, medicineDTO);
    }

    @Override
    @Transactional
    public void deleteMedicine(Long userId, Long medicineId) {
        // 根据userId查询商家信息
        MerchantPO merchant = merchantMapper.selectByUserId(userId);
        // 判断商家是否存在
        if (merchant == null) {
            // 返回错误信息
            throw new BusinessException(ResultCode.MERCHANT_NOT_EXIST);
        }
        // 调用删除药品方法
        medicineService.deleteMedicine(merchant.getId(), medicineId);
    }

    @Override
    @Transactional
    public void updateMedicineStatus(Long userId, Long medicineId, Integer status) {
        // 根据userId查询商家信息
        MerchantPO merchant = merchantMapper.selectByUserId(userId);
        if (merchant == null) {
            throw new BusinessException(ResultCode.MERCHANT_NOT_EXIST);
        }
        medicineService.updateMedicineStatus(merchant.getId(), medicineId, status);
    }

    @Override
    public Map<String, Object> getMerchantStatistics(Long userId) {
        // 根据userId查询商家信息
        MerchantPO merchant = merchantMapper.selectByUserId(userId);
        if (merchant == null) {
            throw new BusinessException(ResultCode.MERCHANT_NOT_EXIST);
        }

        // 统计药品数量
        LambdaQueryWrapper<MedicinePO> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(MedicinePO::getMerchantId, merchant.getId())
               .eq(MedicinePO::getDeleted, 0);
        Long medicineCount = medicineMapper.selectCount(wrapper);

        // 统计上架药品数量
        LambdaQueryWrapper<MedicinePO> onSaleWrapper = new LambdaQueryWrapper<>();
        onSaleWrapper.eq(MedicinePO::getMerchantId, merchant.getId())
               .eq(MedicinePO::getDeleted, 0)
               .eq(MedicinePO::getStatus, 1);
        Long onSaleCount = medicineMapper.selectCount(onSaleWrapper);

        // 计算今日时间范围
        LocalDateTime todayStart = LocalDate.now().atStartOfDay();
        LocalDateTime todayEnd = LocalDate.now().atTime(LocalTime.MAX);
        
        // 今日订单数
        Long todayOrderCount = orderMapper.selectCount(
            new LambdaQueryWrapper<OrderPO>()
                .eq(OrderPO::getMerchantId, merchant.getId())
                .ge(OrderPO::getCreateTime, todayStart)
                .le(OrderPO::getCreateTime, todayEnd)
        );
        
        // 今日收入（已完成订单）
        LambdaQueryWrapper<OrderPO> todayRevenueWrapper = new LambdaQueryWrapper<>();
        todayRevenueWrapper.eq(OrderPO::getMerchantId, merchant.getId())
                          .ge(OrderPO::getCreateTime, todayStart)
                          .le(OrderPO::getCreateTime, todayEnd)
                          .eq(OrderPO::getStatus, 5);
        List<OrderPO> todayOrders = orderMapper.selectList(todayRevenueWrapper);
        BigDecimal todayRevenue = todayOrders.stream()
                .map(o -> o.getPayAmount() != null ? o.getPayAmount() : BigDecimal.ZERO)
                .reduce(BigDecimal.ZERO, BigDecimal::add);
        
        // 本月时间范围
        LocalDateTime monthStart = LocalDate.now().withDayOfMonth(1).atStartOfDay();
        
        // 本月收入
        LambdaQueryWrapper<OrderPO> monthRevenueWrapper = new LambdaQueryWrapper<>();
        monthRevenueWrapper.eq(OrderPO::getMerchantId, merchant.getId())
                          .ge(OrderPO::getCreateTime, monthStart)
                          .le(OrderPO::getCreateTime, todayEnd)
                          .eq(OrderPO::getStatus, 5);
        List<OrderPO> monthOrders = orderMapper.selectList(monthRevenueWrapper);
        BigDecimal monthRevenue = monthOrders.stream()
                .map(o -> o.getPayAmount() != null ? o.getPayAmount() : BigDecimal.ZERO)
                .reduce(BigDecimal.ZERO, BigDecimal::add);

        Map<String, Object> stats = new HashMap<>();
        stats.put("totalMedicines", onSaleCount);  // 在售药品数
        stats.put("onSaleMedicines", onSaleCount);
        stats.put("monthSales", merchant.getMonthlySales());
        stats.put("rating", merchant.getRating());
        stats.put("todayOrders", todayOrderCount);
        stats.put("todayRevenue", todayRevenue);
        stats.put("monthRevenue", monthRevenue);

        return stats;
    }

    private Map<String, Object> convertToMap(MerchantPO merchant) {
        Map<String, Object> map = new HashMap<>();
        map.put("id", merchant.getId());
        map.put("name", merchant.getShopName());
        map.put("logo", merchant.getLogo());
        map.put("phone", merchant.getContactPhone());
        map.put("address", merchant.getAddress());
        map.put("description", merchant.getDescription());
        map.put("openTime", merchant.getOpenTime());
        map.put("closeTime", merchant.getCloseTime());
        map.put("businessHours", merchant.getOpenTime() + "-" + merchant.getCloseTime());
        map.put("rating", merchant.getRating());
        map.put("monthSales", merchant.getMonthlySales());
        map.put("deliveryFee", merchant.getDeliveryFee());
        map.put("minOrderAmount", merchant.getMinOrderAmount());
        map.put("deliveryRange", merchant.getDeliveryRange());
        map.put("status", merchant.getStatus());
        map.put("auditStatus", merchant.getAuditStatus());
        return map;
    }

    private Map<String, Object> convertMedicineToMap(MedicinePO medicine) {
        Map<String, Object> map = new HashMap<>();
        map.put("id", medicine.getId());
        map.put("name", medicine.getName());
        map.put("commonName", medicine.getCommonName());
        map.put("image", medicine.getImage());
        map.put("images", medicine.getImages());
        map.put("specification", medicine.getSpecification());
        map.put("manufacturer", medicine.getManufacturer());
        map.put("approvalNumber", medicine.getApprovalNumber());
        map.put("price", medicine.getPrice());
        map.put("originalPrice", medicine.getOriginalPrice());
        map.put("stock", medicine.getStock());
        map.put("sales", medicine.getSales());
        map.put("isPrescription", medicine.getIsPrescription());
        map.put("categoryId", medicine.getCategoryId());
        map.put("status", medicine.getStatus());
        map.put("auditStatus", medicine.getAuditStatus());
        map.put("auditRemark", medicine.getAuditRemark());
        map.put("efficacy", medicine.getEfficacy());
        map.put("dosage", medicine.getDosage());
        map.put("adverseReactions", medicine.getAdverseReactions());
        map.put("contraindications", medicine.getContraindications());
        map.put("precautions", medicine.getPrecautions());
        map.put("riskTips", medicine.getRiskTips());
        // 前端表单使用indications字段，这里做兼容映射
        map.put("indications", medicine.getEfficacy());
        return map;
    }
}
