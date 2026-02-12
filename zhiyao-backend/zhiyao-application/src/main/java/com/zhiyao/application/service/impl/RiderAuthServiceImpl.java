package com.zhiyao.application.service.impl;

import com.zhiyao.application.dto.LoginDTO;
import com.zhiyao.application.dto.RiderRegisterDTO;
import com.zhiyao.application.service.RiderAuthService;
import com.zhiyao.common.enums.UserRole;
import com.zhiyao.common.result.Result;
import com.zhiyao.infrastructure.persistence.mapper.RiderMapper;
import com.zhiyao.infrastructure.persistence.mapper.UserMapper;
import com.zhiyao.infrastructure.persistence.po.RiderPO;
import com.zhiyao.infrastructure.persistence.po.UserPO;
import com.zhiyao.infrastructure.security.JwtTokenProvider;
import lombok.RequiredArgsConstructor;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.HashMap;
import java.util.Map;

/**
 * 骑手认证服务实现类
 */
@Service
@RequiredArgsConstructor
public class RiderAuthServiceImpl implements RiderAuthService {

    private final UserMapper userMapper;
    private final RiderMapper riderMapper;
    private final PasswordEncoder passwordEncoder;
    private final JwtTokenProvider jwtTokenProvider;

    @Override
    public Result<?> login(LoginDTO loginDTO) {
        // 根据手机号查询用户
        UserPO user = userMapper.selectByPhone(loginDTO.getPhone());
        if (user == null) {
            return Result.fail("账号或密码错误");
        }

        // 验证密码
        if (!passwordEncoder.matches(loginDTO.getPassword(), user.getPassword())) {
            return Result.fail("账号或密码错误");
        }

        // 验证角色
        if (user.getRole() != 4) { // 4表示骑手
            return Result.fail("该账号不是骑手账号");
        }

        // 检查状态
        if (user.getStatus() != 1) {
            return Result.fail("账号已被禁用");
        }

        // 查询骑手信息
        RiderPO rider = riderMapper.selectByUserId(user.getId());
        if (rider != null && rider.getAuditStatus() != 1) {
            return Result.fail("骑手资质审核中，请耐心等待");
        }

        // 生成token
        String token = jwtTokenProvider.generateToken(user.getId(), user.getUsername(), UserRole.RIDER);

        Map<String, Object> data = new HashMap<>();
        data.put("token", token);
        data.put("riderInfo", Map.of(
            "id", rider != null ? rider.getId() : 0,
            "userId", user.getId(),
            "name", rider != null ? rider.getRealName() : user.getNickname(), // 从 rider.realName 获取
            "phone", user.getPhone()
        ));

        return Result.success(data);
    }

    @Override
    @Transactional
    public Result<?> register(RiderRegisterDTO registerDTO) {
        // 检查手机号是否已注册
        if (userMapper.countByPhone(registerDTO.getPhone()) > 0) {
            return Result.fail("该手机号已注册");
        }

        // 创建用户账号
        UserPO user = new UserPO();
        user.setPhone(registerDTO.getPhone());
        user.setUsername(registerDTO.getPhone());
        user.setPassword(passwordEncoder.encode(registerDTO.getPassword()));
        user.setNickname(registerDTO.getName());
        user.setRole(4); // 骑手角色
        user.setStatus(1);
        userMapper.insert(user);

        // 创建骑手信息（字段与数据库表一致）
        RiderPO rider = new RiderPO();
        rider.setUserId(user.getId());
        rider.setRealName(registerDTO.getName());  // 真实姓名（必填）
        rider.setIdCard(registerDTO.getIdCard());  // 身份证号
        rider.setStatus(0);  // 0-离线
        rider.setAuditStatus(0);  // 0-待审核
        
        // 业务字段（不会被持久化到数据库）
        rider.setPhone(registerDTO.getPhone());  // 电话从 user 表获取
        rider.setOnlineStatus(0);  // 离线
        rider.setRating(new BigDecimal("5.0"));  // 默认评分
        // 初始化统计字段为 0
        rider.setTodayOrders(0);
        rider.setTotalOrders(0);
        rider.setTodayIncome(BigDecimal.ZERO);
        rider.setTotalIncome(BigDecimal.ZERO);
        
        riderMapper.insert(rider);

        return Result.success("注册成功，请等待管理员审核");
    }
}
