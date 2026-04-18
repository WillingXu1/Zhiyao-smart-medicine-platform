package com.zhiyao.application.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.zhiyao.application.dto.LoginDTO;
import com.zhiyao.application.dto.AdminProfileDTO;
import com.zhiyao.application.dto.ChangePasswordDTO;
import com.zhiyao.application.dto.PlatformConfigDTO;
import com.zhiyao.application.service.AdminService;
import com.zhiyao.common.enums.UserRole;
import com.zhiyao.common.result.Result;
import com.zhiyao.infrastructure.persistence.po.UserPO;
import com.zhiyao.infrastructure.persistence.po.MerchantPO;
import com.zhiyao.infrastructure.persistence.po.MedicinePO;
import com.zhiyao.infrastructure.persistence.po.OrderPO;
import com.zhiyao.infrastructure.persistence.po.OrderItemPO;
import com.zhiyao.infrastructure.persistence.po.RiderPO;
import com.zhiyao.infrastructure.persistence.mapper.UserMapper;
import com.zhiyao.infrastructure.persistence.mapper.MerchantMapper;
import com.zhiyao.infrastructure.persistence.mapper.MedicineMapper;
import com.zhiyao.infrastructure.persistence.mapper.OrderMapper;
import com.zhiyao.infrastructure.persistence.mapper.OrderItemMapper;
import com.zhiyao.infrastructure.persistence.mapper.RiderMapper;
import com.zhiyao.infrastructure.security.JwtTokenProvider;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.LocalTime;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.data.redis.core.RedisTemplate;
import jakarta.annotation.PostConstruct;

/**
 * 管理员服务实现类
 */
@Slf4j
@Service
public class AdminServiceImpl implements AdminService {

    private final UserMapper userMapper;
    private final MerchantMapper merchantMapper;
    private final MedicineMapper medicineMapper;
    private final OrderMapper orderMapper;
    private final OrderItemMapper orderItemMapper;
    private final RiderMapper riderMapper;
    private final PasswordEncoder passwordEncoder;
    private final JwtTokenProvider jwtTokenProvider;
    private final RedisTemplate<String, Object> platformConfigRedisTemplate;

    // Redis缓存key
    private static final String PLATFORM_CONFIG_KEY = "platform:config";
    private static final String ADMIN_PROFILE_KEY = "admin:profile";

    public AdminServiceImpl(
            UserMapper userMapper,
            MerchantMapper merchantMapper,
            MedicineMapper medicineMapper,
            OrderMapper orderMapper,
            OrderItemMapper orderItemMapper,
            RiderMapper riderMapper,
            PasswordEncoder passwordEncoder,
            JwtTokenProvider jwtTokenProvider,
            @Qualifier("platformConfigRedisTemplate") RedisTemplate<String, Object> platformConfigRedisTemplate) {
        this.userMapper = userMapper;
        this.merchantMapper = merchantMapper;
        this.medicineMapper = medicineMapper;
        this.orderMapper = orderMapper;
        this.orderItemMapper = orderItemMapper;
        this.riderMapper = riderMapper;
        this.passwordEncoder = passwordEncoder;
        this.jwtTokenProvider = jwtTokenProvider;
        this.platformConfigRedisTemplate = platformConfigRedisTemplate;
    }

    /**
     * 初始化平台配置到Redis（如果不存在）
     */
    @PostConstruct
    public void initPlatformConfig() {
        try {
            // 初始化平台配置
            if (Boolean.FALSE.equals(platformConfigRedisTemplate.hasKey(PLATFORM_CONFIG_KEY))) {
                Map<String, Object> defaultConfig = new HashMap<>();
                defaultConfig.put("platformName", "智健优选");
                defaultConfig.put("contactPhone", "400-888-8888");
                defaultConfig.put("deliveryFee", "5.00");
                defaultConfig.put("minOrderAmount", "20.00");
                defaultConfig.put("deliveryRange", 5);
                platformConfigRedisTemplate.opsForHash().putAll(PLATFORM_CONFIG_KEY, defaultConfig);
                log.info("初始化平台配置到Redis DB10成功");
            }
        } catch (Exception e) {
            log.warn("初始化Redis缓存失败，将在首次访问时初始化: {}", e.getMessage());
        }
    }

    // 管理员账号（实际项目中应该有独立的Admin表）
    private static final String ADMIN_USERNAME = "admin";
    private static final String ADMIN_PASSWORD = "admin123";

    @Override
    public Result<?> login(LoginDTO loginDTO) {
        // 简单的管理员登录验证
        if (!ADMIN_USERNAME.equals(loginDTO.getPhone())) {
            return Result.fail("账号或密码错误");
        }
        
        if (!ADMIN_PASSWORD.equals(loginDTO.getPassword())) {
            return Result.fail("账号或密码错误");
        }

        // 生成token
        String token = jwtTokenProvider.generateToken(0L, "admin", UserRole.ADMIN);
        
        Map<String, Object> data = new HashMap<>();
        data.put("token", token);
        data.put("adminInfo", Map.of(
            "id", 1,
            "username", "admin",
            "name", "系统管理员",
            "role", "ADMIN"
        ));
        
        return Result.success(data);
    }

    @Override
    public Result<?> getCurrentAdmin() {
        // 从数据库查询管理员信息（role=3表示管理员）
        LambdaQueryWrapper<UserPO> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(UserPO::getRole, 3).last("LIMIT 1");
        UserPO admin = userMapper.selectOne(wrapper);
        
        Map<String, Object> adminInfo = new HashMap<>();
        if (admin != null) {
            adminInfo.put("id", admin.getId());
            adminInfo.put("username", admin.getUsername());
            adminInfo.put("name", admin.getNickname() != null ? admin.getNickname() : "系统管理员");
            adminInfo.put("email", admin.getEmail());
            adminInfo.put("phone", admin.getPhone());
            adminInfo.put("avatar", admin.getAvatar());
            adminInfo.put("role", "ADMIN");
        } else {
            // 兜底返回默认值
            adminInfo.put("id", 1);
            adminInfo.put("username", "admin");
            adminInfo.put("name", "系统管理员");
            adminInfo.put("role", "ADMIN");
        }
        return Result.success(adminInfo);
    }

    @Override
    public Result<?> getDashboardStats() {
        Map<String, Object> stats = new HashMap<>();
        
        // 统计总数（字段名匹配前端）
        stats.put("totalUsers", userMapper.selectCount(null));
        stats.put("totalMerchants", merchantMapper.selectCount(null));
        stats.put("totalMedicines", medicineMapper.selectCount(null));
        stats.put("totalOrders", orderMapper.selectCount(null));
        stats.put("totalRiders", riderMapper.selectCount(null));
        
        // 计算今日开始时间
        LocalDateTime todayStart = LocalDate.now().atStartOfDay();
        LocalDateTime todayEnd = LocalDate.now().atTime(LocalTime.MAX);
        
        // 今日订单数
        Long todayOrderCount = orderMapper.selectCount(
            new LambdaQueryWrapper<OrderPO>()
                .ge(OrderPO::getCreateTime, todayStart)
                .le(OrderPO::getCreateTime, todayEnd)
        );
        stats.put("todayOrders", todayOrderCount);
        
        // 今日收入（已完成订单的总金额）
        LambdaQueryWrapper<OrderPO> todayRevenueWrapper = new LambdaQueryWrapper<>();
        todayRevenueWrapper.ge(OrderPO::getCreateTime, todayStart)
                          .le(OrderPO::getCreateTime, todayEnd)
                          .eq(OrderPO::getStatus, 5); // 已完成订单
        List<OrderPO> todayCompletedOrders = orderMapper.selectList(todayRevenueWrapper);
        BigDecimal todayRevenue = todayCompletedOrders.stream()
                .map(o -> o.getPayAmount() != null ? o.getPayAmount() : BigDecimal.ZERO)
                .reduce(BigDecimal.ZERO, BigDecimal::add);
        stats.put("todayRevenue", todayRevenue);
        
        // 本月开始时间
        LocalDateTime monthStart = LocalDate.now().withDayOfMonth(1).atStartOfDay();
        
        // 本月收入
        LambdaQueryWrapper<OrderPO> monthRevenueWrapper = new LambdaQueryWrapper<>();
        monthRevenueWrapper.ge(OrderPO::getCreateTime, monthStart)
                          .le(OrderPO::getCreateTime, todayEnd)
                          .eq(OrderPO::getStatus, 5);
        List<OrderPO> monthCompletedOrders = orderMapper.selectList(monthRevenueWrapper);
        BigDecimal monthRevenue = monthCompletedOrders.stream()
                .map(o -> o.getPayAmount() != null ? o.getPayAmount() : BigDecimal.ZERO)
                .reduce(BigDecimal.ZERO, BigDecimal::add);
        stats.put("monthRevenue", monthRevenue);
        
        // 待处理订单（待接单状态=1）
        Long pendingOrders = orderMapper.selectCount(
            new LambdaQueryWrapper<OrderPO>().eq(OrderPO::getStatus, 1)
        );
        stats.put("pendingOrders", pendingOrders);
        
        // 配送中订单（状态=4）
        Long deliveringOrders = orderMapper.selectCount(
            new LambdaQueryWrapper<OrderPO>().eq(OrderPO::getStatus, 4)
        );
        stats.put("deliveringOrders", deliveringOrders);
        
        // 在线骑手
        Long onlineRiders = riderMapper.selectCount(
            new LambdaQueryWrapper<RiderPO>().eq(RiderPO::getStatus, 1)
        );
        stats.put("onlineRiders", onlineRiders);
        
        // 待审核商家
        stats.put("pendingMerchants", merchantMapper.selectCount(
            new LambdaQueryWrapper<MerchantPO>().eq(MerchantPO::getStatus, 0)
        ));
        
        return Result.success(stats);
    }

    @Override
    public Result<?> getUserList(Integer page, Integer size, String keyword) {
        Page<UserPO> pageParam = new Page<>(page, size);
        LambdaQueryWrapper<UserPO> wrapper = new LambdaQueryWrapper<>();
        
        if (StringUtils.hasText(keyword)) {
            wrapper.like(UserPO::getPhone, keyword)
                   .or().like(UserPO::getNickname, keyword);
        }
        wrapper.orderByDesc(UserPO::getCreateTime);
        
        Page<UserPO> result = userMapper.selectPage(pageParam, wrapper);
        return Result.success(result);
    }

    @Override
    public Result<?> updateUserStatus(Long userId, Integer status) {
        UserPO user = userMapper.selectById(userId);
        if (user == null) {
            return Result.fail("用户不存在");
        }
        
        user.setStatus(status);
        userMapper.updateById(user);
        return Result.success("操作成功");
    }

    @Override
    public Result<?> getMerchantList(Integer page, Integer size, String keyword, Integer status) {
        Page<MerchantPO> pageParam = new Page<>(page, size);
        LambdaQueryWrapper<MerchantPO> wrapper = new LambdaQueryWrapper<>();
        
        if (StringUtils.hasText(keyword)) {
            wrapper.like(MerchantPO::getShopName, keyword)
                   .or().like(MerchantPO::getContactPhone, keyword);
        }
        // 使用auditStatus筛选审核状态
        if (status != null) {
            wrapper.eq(MerchantPO::getAuditStatus, status);
        }
        wrapper.orderByDesc(MerchantPO::getCreateTime);
        
        Page<MerchantPO> result = merchantMapper.selectPage(pageParam, wrapper);
        
        // 转换为前端需要的格式
        Map<String, Object> data = new HashMap<>();
        data.put("list", result.getRecords().stream().map(m -> {
            Map<String, Object> map = new HashMap<>();
            map.put("id", m.getId());
            map.put("name", m.getShopName());
            map.put("phone", m.getContactPhone());
            map.put("address", m.getAddress());
            map.put("status", m.getAuditStatus()); // 审核状态
            map.put("createTime", m.getCreateTime());
            map.put("businessLicenseImage", m.getBusinessLicenseImage());
            map.put("drugLicenseImage", m.getDrugLicenseImage());
            map.put("businessHours", m.getOpenTime() + "-" + m.getCloseTime());
            map.put("auditRemark", m.getAuditRemark());
            return map;
        }).collect(java.util.stream.Collectors.toList()));
        data.put("total", result.getTotal());
        return Result.success(data);
    }

    @Override
    public Result<?> auditMerchant(Long merchantId, Integer auditStatus, String reason) {
        MerchantPO merchant = merchantMapper.selectById(merchantId);
        if (merchant == null) {
            return Result.fail("商家不存在");
        }
        
        // 更新审核状态
        merchant.setAuditStatus(auditStatus);
        if (reason != null) {
            merchant.setAuditRemark(reason);
        }
        // 审核通过后设置营业状态为营业中
        if (auditStatus == 1) {
            merchant.setStatus(1);
        }
        merchantMapper.updateById(merchant);
        return Result.success("审核完成");
    }

    @Override
    public Result<?> getMedicineList(Integer page, Integer size, String keyword, Long categoryId) {
        Page<MedicinePO> pageParam = new Page<>(page, size);
        LambdaQueryWrapper<MedicinePO> wrapper = new LambdaQueryWrapper<>();
        
        // 过滤已删除的药品
        wrapper.eq(MedicinePO::getDeleted, 0);
        
        if (StringUtils.hasText(keyword)) {
            wrapper.like(MedicinePO::getName, keyword);
        }
        if (categoryId != null) {
            wrapper.eq(MedicinePO::getCategoryId, categoryId);
        }
        wrapper.orderByDesc(MedicinePO::getCreateTime);
        
        Page<MedicinePO> result = medicineMapper.selectPage(pageParam, wrapper);
        
        // 转换为前端期望的格式
        java.util.Map<String, Object> data = new java.util.HashMap<>();
        data.put("list", result.getRecords().stream().map(m -> {
            java.util.Map<String, Object> map = new java.util.HashMap<>();
            map.put("id", m.getId());
            map.put("name", m.getName());
            map.put("commonName", m.getCommonName());
            map.put("specification", m.getSpecification());
            map.put("manufacturer", m.getManufacturer());
            map.put("approvalNumber", m.getApprovalNumber());
            map.put("price", m.getPrice());
            map.put("originalPrice", m.getOriginalPrice());
            map.put("stock", m.getStock());
            map.put("isPrescription", m.getIsPrescription());
            map.put("status", m.getStatus());
            map.put("auditStatus", m.getAuditStatus());
            map.put("merchantId", m.getMerchantId());
            map.put("categoryId", m.getCategoryId());
            map.put("image", m.getImage());
            map.put("images", m.getImages());
            map.put("efficacy", m.getEfficacy());
            map.put("dosage", m.getDosage());
            map.put("adverseReactions", m.getAdverseReactions());
            map.put("contraindications", m.getContraindications());
            map.put("precautions", m.getPrecautions());
            map.put("riskTips", m.getRiskTips());
            // 获取商家名称
            MerchantPO merchant = merchantMapper.selectById(m.getMerchantId());
            map.put("merchantName", merchant != null ? merchant.getShopName() : "未知商家");
            return map;
        }).collect(java.util.stream.Collectors.toList()));
        data.put("total", result.getTotal());
        return Result.success(data);
    }

    @Override
    public Result<?> auditMedicine(Long medicineId, Integer status, String reason, Long categoryId) {
        MedicinePO medicine = medicineMapper.selectById(medicineId);
        if (medicine == null) {
            return Result.fail("药品不存在");
        }
        
        // 设置审核状态（0-待审核 1-已通过 2-已拒绝）
        medicine.setAuditStatus(status);
        // 审核拒绝时记录原因
        if (status == 2 && reason != null) {
            medicine.setAuditRemark(reason);
        }
        // 如果传入了分类ID，则更新分类
        if (categoryId != null) {
            medicine.setCategoryId(categoryId);
        }
        medicineMapper.updateById(medicine);
        return Result.success(status == 1 ? "审核通过" : "审核拒绝");
    }

    @Override
    public Result<?> getOrderList(Integer page, Integer size, String orderNo, Integer status) {
        Page<OrderPO> pageParam = new Page<>(page, size);
        LambdaQueryWrapper<OrderPO> wrapper = new LambdaQueryWrapper<>();
        
        if (StringUtils.hasText(orderNo)) {
            wrapper.like(OrderPO::getOrderNo, orderNo);
        }
        if (status != null) {
            wrapper.eq(OrderPO::getStatus, status);
        }
        wrapper.eq(OrderPO::getDeleted, 0);
        wrapper.orderByDesc(OrderPO::getCreateTime);
        
        Page<OrderPO> result = orderMapper.selectPage(pageParam, wrapper);
        
        // 转换为前端需要的格式
        Map<String, Object> data = new HashMap<>();
        data.put("records", result.getRecords());
        data.put("total", result.getTotal());
        data.put("pages", result.getPages());
        data.put("current", result.getCurrent());
        
        log.info("管理端订单列表查询: page={}, size={}, status={}, total={}", page, size, status, result.getTotal());
        return Result.success(data);
    }

    @Override
    public Result<?> getOrderDetail(Long orderId) {
        OrderPO order = orderMapper.selectById(orderId);
        if (order == null) {
            return Result.fail("订单不存在");
        }
        
        // 获取订单项
        List<OrderItemPO> orderItems = orderItemMapper.selectByOrderId(orderId);
        
        // 组装返回数据
        Map<String, Object> result = new HashMap<>();
        result.put("id", order.getId());
        result.put("orderNo", order.getOrderNo());
        result.put("userId", order.getUserId());
        result.put("merchantId", order.getMerchantId());
        result.put("riderId", order.getRiderId());
        result.put("receiverName", order.getReceiverName());
        result.put("receiverPhone", order.getReceiverPhone());
        result.put("receiverAddress", order.getReceiverAddress());
        result.put("totalAmount", order.getTotalAmount());
        result.put("deliveryFee", order.getDeliveryFee());
        result.put("payAmount", order.getPayAmount());
        result.put("status", order.getStatus());
        result.put("payTime", order.getPayTime());
        result.put("acceptTime", order.getAcceptTime());
        result.put("deliveryTime", order.getDeliveryTime());
        result.put("completeTime", order.getCompleteTime());
        result.put("cancelReason", order.getCancelReason());
        result.put("rejectReason", order.getRejectReason());
        result.put("remark", order.getRemark());
        result.put("createTime", order.getCreateTime());
        result.put("items", orderItems);
        
        log.info("管理端订单详情查询: orderId={}, items={}", orderId, orderItems.size());
        return Result.success(result);
    }

    @Override
    public Result<?> getRiderList(Integer page, Integer size, String keyword) {
        Page<RiderPO> pageParam = new Page<>(page, size);
        LambdaQueryWrapper<RiderPO> wrapper = new LambdaQueryWrapper<>();
        
        if (StringUtils.hasText(keyword)) {
            // 根据真实姓名或身份证搜索
            wrapper.like(RiderPO::getRealName, keyword)
                   .or().like(RiderPO::getIdCard, keyword);
        }
        wrapper.orderByDesc(RiderPO::getCreateTime);
        
        Page<RiderPO> result = riderMapper.selectPage(pageParam, wrapper);
        
        // 计算今日时间范围
        LocalDateTime todayStart = LocalDate.now().atStartOfDay();
        LocalDateTime todayEnd = LocalDate.now().atTime(LocalTime.MAX);
        
        // 转换为前端需要的格式，关联 user 表获取手机号，并实时计算统计数据
        Map<String, Object> data = new HashMap<>();
        data.put("records", result.getRecords().stream().map(r -> {
            Map<String, Object> map = new HashMap<>();
            map.put("id", r.getId());
            map.put("userId", r.getUserId());
            map.put("realName", r.getRealName());
            map.put("idCard", r.getIdCard());
            map.put("status", r.getStatus());
            map.put("auditStatus", r.getAuditStatus());
            map.put("createTime", r.getCreateTime());
            
            // 从 user 表获取手机号
            UserPO user = userMapper.selectById(r.getUserId());
            map.put("phone", user != null ? user.getPhone() : "");
            
            // 实时计算今日完成订单数
            LambdaQueryWrapper<OrderPO> todayWrapper = new LambdaQueryWrapper<>();
            todayWrapper.eq(OrderPO::getRiderId, r.getId())
                       .eq(OrderPO::getStatus, 5)  // 已完成
                       .ge(OrderPO::getCompleteTime, todayStart)
                       .le(OrderPO::getCompleteTime, todayEnd)
                       .eq(OrderPO::getDeleted, 0);
            Long todayOrders = orderMapper.selectCount(todayWrapper);
            map.put("todayOrders", todayOrders);
            
            // 实时计算今日收入
            List<OrderPO> todayOrderList = orderMapper.selectList(todayWrapper);
            BigDecimal todayIncome = todayOrderList.stream()
                    .map(o -> o.getDeliveryFee() != null ? o.getDeliveryFee() : BigDecimal.ZERO)
                    .reduce(BigDecimal.ZERO, BigDecimal::add);
            map.put("todayIncome", todayIncome);
            
            // 实时计算累计订单数
            LambdaQueryWrapper<OrderPO> totalWrapper = new LambdaQueryWrapper<>();
            totalWrapper.eq(OrderPO::getRiderId, r.getId())
                       .eq(OrderPO::getStatus, 5)  // 已完成
                       .eq(OrderPO::getDeleted, 0);
            Long totalOrders = orderMapper.selectCount(totalWrapper);
            map.put("totalOrders", totalOrders);
            
            // 实时计算累计收入
            List<OrderPO> allOrders = orderMapper.selectList(totalWrapper);
            BigDecimal totalIncome = allOrders.stream()
                    .map(o -> o.getDeliveryFee() != null ? o.getDeliveryFee() : BigDecimal.ZERO)
                    .reduce(BigDecimal.ZERO, BigDecimal::add);
            map.put("totalIncome", totalIncome);

            return map;
        }).collect(java.util.stream.Collectors.toList()));
        data.put("total", result.getTotal());
        
        log.info("管理端骑手列表查询: page={}, size={}, total={}", page, size, result.getTotal());
        return Result.success(data);
    }

    @Override
    public Result<?> auditRider(Long riderId, Integer status, String reason) {
        RiderPO rider = riderMapper.selectById(riderId);
        if (rider == null) {
            return Result.fail("骑手不存在");
        }
        
        // 设置审核状态（0-待审核 1-通过 2-拒绝）
        rider.setAuditStatus(status);
        // 审核通过后设置账号状态为正常
        if (status == 1) {
            rider.setStatus(1);
        }
        riderMapper.updateById(rider);
        return Result.success(status == 1 ? "审核通过" : "审核拒绝");
    }

    @Override
    public Result<?> updateProfile(AdminProfileDTO profileDTO) {
        // 查询管理员用户（role=3表示管理员）
        LambdaQueryWrapper<UserPO> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(UserPO::getRole, 3).last("LIMIT 1");
        UserPO admin = userMapper.selectOne(wrapper);
        
        if (admin == null) {
            return Result.fail("管理员不存在");
        }
        
        // 更新管理员信息到数据库
        boolean updated = false;
        if (profileDTO.getName() != null) {
            admin.setNickname(profileDTO.getName());
            updated = true;
        }
        if (profileDTO.getEmail() != null) {
            admin.setEmail(profileDTO.getEmail());
            updated = true;
        }
        if (profileDTO.getPhone() != null) {
            admin.setPhone(profileDTO.getPhone());
            updated = true;
        }
        if (profileDTO.getAvatar() != null) {
            admin.setAvatar(profileDTO.getAvatar());
            updated = true;
        }
        
        if (updated) {
            userMapper.updateById(admin);
            // 同时更新Redis缓存中的管理员信息
            try {
                Map<String, Object> adminProfileCache = new HashMap<>();
                adminProfileCache.put("name", admin.getNickname());
                adminProfileCache.put("email", admin.getEmail());
                adminProfileCache.put("phone", admin.getPhone());
                adminProfileCache.put("avatar", admin.getAvatar() != null ? admin.getAvatar() : "");
                platformConfigRedisTemplate.opsForHash().putAll(ADMIN_PROFILE_KEY, adminProfileCache);
                log.info("管理员信息已更新到数据库和Redis缓存");
            } catch (Exception e) {
                log.warn("更新Redis缓存失败，但数据库更新成功: {}", e.getMessage());
            }
        }
        
        // 返回更新后的管理员信息
        Map<String, Object> adminInfo = new HashMap<>();
        adminInfo.put("id", admin.getId());
        adminInfo.put("username", admin.getUsername());
        adminInfo.put("name", admin.getNickname() != null ? admin.getNickname() : "系统管理员");
        adminInfo.put("email", admin.getEmail());
        adminInfo.put("phone", admin.getPhone());
        adminInfo.put("avatar", admin.getAvatar());
        adminInfo.put("role", "ADMIN");
        
        return Result.success(adminInfo);
    }

    @Override
    public Result<?> changePassword(ChangePasswordDTO passwordDTO) {
        // 查询管理员用户
        LambdaQueryWrapper<UserPO> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(UserPO::getRole, 3).last("LIMIT 1");
        UserPO admin = userMapper.selectOne(wrapper);
        
        if (admin == null) {
            return Result.fail("管理员不存在");
        }
        
        // 验证原密码
        if (!passwordEncoder.matches(passwordDTO.getOldPassword(), admin.getPassword())) {
            return Result.fail("原密码错误");
        }
        
        // 验证两次密码一致
        if (!passwordDTO.getNewPassword().equals(passwordDTO.getConfirmPassword())) {
            return Result.fail("两次输入的密码不一致");
        }
        
        // 更新数据库中的密码
        admin.setPassword(passwordEncoder.encode(passwordDTO.getNewPassword()));
        userMapper.updateById(admin);
        log.info("管理员密码已更新");
        
        return Result.success("密码修改成功");
    }

    @Override
    public Result<?> getPlatformConfig() {
        try {
            Map<Object, Object> config = platformConfigRedisTemplate.opsForHash().entries(PLATFORM_CONFIG_KEY);
            if (config.isEmpty()) {
                // 如果Redis中没有，初始化默认值
                Map<String, Object> defaultConfig = new HashMap<>();
                defaultConfig.put("platformName", "智健优选");
                defaultConfig.put("contactPhone", "400-888-8888");
                defaultConfig.put("deliveryFee", "5.00");
                defaultConfig.put("minOrderAmount", "20.00");
                defaultConfig.put("deliveryRange", 5);
                platformConfigRedisTemplate.opsForHash().putAll(PLATFORM_CONFIG_KEY, defaultConfig);
                return Result.success(defaultConfig);
            }
            return Result.success(config);
        } catch (Exception e) {
            log.error("获取平台配置失败: {}", e.getMessage());
            // 返回默认配置
            Map<String, Object> defaultConfig = new HashMap<>();
            defaultConfig.put("platformName", "智健优选");
            defaultConfig.put("contactPhone", "400-888-8888");
            defaultConfig.put("deliveryFee", "5.00");
            defaultConfig.put("minOrderAmount", "20.00");
            defaultConfig.put("deliveryRange", 5);
            return Result.success(defaultConfig);
        }
    }

    @Override
    public Result<?> savePlatformConfig(PlatformConfigDTO configDTO) {
        try {
            Map<String, Object> configToSave = new HashMap<>();
            if (configDTO.getPlatformName() != null) {
                configToSave.put("platformName", configDTO.getPlatformName());
            }
            if (configDTO.getContactPhone() != null) {
                configToSave.put("contactPhone", configDTO.getContactPhone());
            }
            if (configDTO.getDeliveryFee() != null) {
                configToSave.put("deliveryFee", configDTO.getDeliveryFee().toString());
            }
            if (configDTO.getMinOrderAmount() != null) {
                configToSave.put("minOrderAmount", configDTO.getMinOrderAmount().toString());
            }
            if (configDTO.getDeliveryRange() != null) {
                configToSave.put("deliveryRange", configDTO.getDeliveryRange());
            }
            
            if (!configToSave.isEmpty()) {
                platformConfigRedisTemplate.opsForHash().putAll(PLATFORM_CONFIG_KEY, configToSave);
                log.info("平台配置已保存到Redis DB10");
            }
            return Result.success("平台配置保存成功");
        } catch (Exception e) {
            log.error("保存平台配置失败: {}", e.getMessage());
            return Result.fail("保存平台配置失败");
        }
    }
}
