package com.zhiyao.application.service.impl;

import com.zhiyao.application.dto.LoginDTO;
import com.zhiyao.application.dto.MerchantRegisterDTO;
import com.zhiyao.application.service.MerchantAuthService;
import com.zhiyao.common.enums.UserRole;
import com.zhiyao.common.result.Result;
import com.zhiyao.infrastructure.persistence.mapper.MerchantMapper;
import com.zhiyao.infrastructure.persistence.mapper.UserMapper;
import com.zhiyao.infrastructure.persistence.po.MerchantPO;
import com.zhiyao.infrastructure.persistence.po.UserPO;
import com.zhiyao.infrastructure.security.JwtTokenProvider;
import lombok.RequiredArgsConstructor;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.HashMap;
import java.util.Map;

/**
 * 商家认证服务实现类
 */
@Service
@RequiredArgsConstructor
public class MerchantAuthServiceImpl implements MerchantAuthService {

    private final UserMapper userMapper;
    private final MerchantMapper merchantMapper;
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
        if (user.getRole() != 2) { // 2表示商家
            return Result.fail("该账号不是商家账号");
        }

        // 检查状态
        if (user.getStatus() != 1) {
            return Result.fail("账号已被禁用");
        }

        // 查询商家信息
        MerchantPO merchant = merchantMapper.selectByUserId(user.getId());
        if (merchant != null && merchant.getAuditStatus() != 1) {
            return Result.fail("商家资质审核中，请耐心等待");
        }

        // 生成token
        String token = jwtTokenProvider.generateToken(user.getId(), user.getUsername(), UserRole.MERCHANT);

        Map<String, Object> data = new HashMap<>();
        data.put("token", token);
        data.put("merchantInfo", Map.of(
            "id", merchant != null ? merchant.getId() : 0,
            "userId", user.getId(),
            "name", merchant != null ? merchant.getShopName() : "",
            "phone", user.getPhone()
        ));

        return Result.success(data);
    }

    @Override
    @Transactional
    public Result<?> register(MerchantRegisterDTO registerDTO) {
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
        user.setRole(2); // 商家角色
        user.setStatus(1);
        userMapper.insert(user);

        // 创建商家信息
        MerchantPO merchant = new MerchantPO();
        merchant.setUserId(user.getId());
        merchant.setShopName(registerDTO.getName());
        merchant.setContactName(registerDTO.getContactName() != null ? registerDTO.getContactName() : registerDTO.getName());
        merchant.setContactPhone(registerDTO.getPhone());
        merchant.setAddress(registerDTO.getAddress());
        // 解析营业时间 如：09:00-22:00
        String businessHours = registerDTO.getBusinessHours();
        if (businessHours != null && businessHours.contains("-")) {
            String[] times = businessHours.split("-");
            merchant.setOpenTime(times[0].trim());
            merchant.setCloseTime(times.length > 1 ? times[1].trim() : "22:00");
        } else {
            merchant.setOpenTime("08:00");
            merchant.setCloseTime("22:00");
        }
        merchant.setBusinessLicenseImage(registerDTO.getBusinessLicenseValue());
        merchant.setDrugLicenseImage(registerDTO.getPharmacistLicenseValue());
        merchant.setLogo(registerDTO.getLogo());
        merchant.setStatus(1); // 营业中
        merchant.setAuditStatus(0); // 待审核
        merchantMapper.insert(merchant);

        return Result.success("注册成功，请等待管理员审核");
    }
}
