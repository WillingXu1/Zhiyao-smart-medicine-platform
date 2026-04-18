package com.zhiyao.application.service.impl;

import com.zhiyao.application.dto.LoginVO;
import com.zhiyao.application.dto.UserLoginDTO;
import com.zhiyao.application.dto.UserRegisterDTO;
import com.zhiyao.application.service.UserService;
import com.zhiyao.common.enums.UserRole;
import com.zhiyao.common.exception.BusinessException;
import com.zhiyao.common.result.ResultCode;
import com.zhiyao.infrastructure.persistence.mapper.AddressMapper;
import com.zhiyao.infrastructure.persistence.mapper.FavoriteMapper;
import com.zhiyao.infrastructure.persistence.mapper.MedicineMapper;
import com.zhiyao.infrastructure.persistence.mapper.UserMapper;
import com.zhiyao.infrastructure.persistence.po.AddressPO;
import com.zhiyao.infrastructure.persistence.po.FavoritePO;
import com.zhiyao.infrastructure.persistence.po.MedicinePO;
import com.zhiyao.infrastructure.persistence.po.UserPO;
import com.zhiyao.infrastructure.security.JwtTokenProvider;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * 用户服务实现类
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class UserServiceImpl implements UserService {

    private final UserMapper userMapper;
    private final AddressMapper addressMapper;
    private final FavoriteMapper favoriteMapper;
    private final MedicineMapper medicineMapper;
    private final PasswordEncoder passwordEncoder;
    private final JwtTokenProvider jwtTokenProvider;

    @Override
    @Transactional
    public Long register(UserRegisterDTO dto) {
        // 检查用户名是否已存在
        if (userMapper.countByUsername(dto.getUsername()) > 0) {
            throw new BusinessException(ResultCode.USER_EXIST);
        }

        // 检查手机号是否已存在
        if (userMapper.countByPhone(dto.getPhone()) > 0) {
            throw new BusinessException(ResultCode.PHONE_EXIST);
        }

        // 创建用户
        UserPO user = new UserPO();
        user.setUsername(dto.getUsername());
        user.setPassword(passwordEncoder.encode(dto.getPassword()));
        user.setPhone(dto.getPhone());
        user.setNickname(dto.getNickname() != null ? dto.getNickname() : dto.getUsername());
        user.setRole(UserRole.USER.getCode());
        user.setStatus(1);
        user.setDeleted(0);

        userMapper.insert(user);
        log.info("用户注册成功: userId={}, username={}", user.getId(), user.getUsername());

        return user.getId();
    }

    @Override
    public LoginVO login(UserLoginDTO dto) {
        return doLogin(dto, UserRole.USER);
    }

    @Override
    public LoginVO merchantLogin(UserLoginDTO dto) {
        return doLogin(dto, UserRole.MERCHANT);
    }

    @Override
    public LoginVO adminLogin(UserLoginDTO dto) {
        return doLogin(dto, UserRole.ADMIN);
    }

    @Override
    public LoginVO riderLogin(UserLoginDTO dto) {
        return doLogin(dto, UserRole.RIDER);
    }

    /**
     * 通用登录逻辑
     */
    private LoginVO doLogin(UserLoginDTO dto, UserRole requiredRole) {
        // 先尝试用户名登录，再尝试手机号登录
        UserPO user = userMapper.selectByUsername(dto.getUsername());
        if (user == null) {
            user = userMapper.selectByPhone(dto.getUsername());
        }

        // 用户不存在
        if (user == null) {
            throw new BusinessException(ResultCode.USER_NOT_EXIST);
        }

        // 验证密码
        if (!passwordEncoder.matches(dto.getPassword(), user.getPassword())) {
            throw new BusinessException(ResultCode.USER_PASSWORD_ERROR);
        }

        // 检查账号状态
        if (user.getStatus() != 1) {
            throw new BusinessException(ResultCode.USER_DISABLED);
        }

        // 检查角色权限
        UserRole userRole = UserRole.fromCode(user.getRole());
        if (requiredRole != null && !requiredRole.equals(userRole)) {
            throw new BusinessException(ResultCode.FORBIDDEN, "无权限访问该端口");
        }

        // 生成Token
        String token = jwtTokenProvider.generateToken(user.getId(), user.getUsername(), userRole);

        log.info("用户登录成功: userId={}, username={}, role={}", user.getId(), user.getUsername(), userRole);

        return LoginVO.builder()
                .token(token)
                .userId(user.getId())
                .username(user.getUsername())
                .nickname(user.getNickname())
                .avatar(user.getAvatar())
                .role(user.getRole())
                .build();
    }

    @Override
    public LoginVO getCurrentUser(Long userId) {
        UserPO user = userMapper.selectById(userId);
        if (user == null) {
            throw new BusinessException(ResultCode.USER_NOT_EXIST);
        }

        return LoginVO.builder()
                .userId(user.getId())
                .username(user.getUsername())
                .nickname(user.getNickname())
                .avatar(user.getAvatar())
                .email(user.getEmail())
                .role(user.getRole())
                .build();
    }

    @Override
    @Transactional
    public void changePassword(Long userId, String oldPassword, String newPassword) {
        UserPO user = userMapper.selectById(userId);
        if (user == null) {
            throw new BusinessException(ResultCode.USER_NOT_EXIST);
        }

        // 验证旧密码
        if (!passwordEncoder.matches(oldPassword, user.getPassword())) {
            throw new BusinessException(ResultCode.USER_PASSWORD_ERROR, "原密码错误");
        }

        // 更新密码
        user.setPassword(passwordEncoder.encode(newPassword));
        userMapper.updateById(user);

        log.info("用户修改密码成功: userId={}", userId);
    }

    @Override
    @Transactional
    public void updateUserInfo(Long userId, String nickname, String avatar, String email) {
        UserPO user = userMapper.selectById(userId);
        if (user == null) {
            throw new BusinessException(ResultCode.USER_NOT_EXIST);
        }

        if (StringUtils.hasText(nickname)) {
            user.setNickname(nickname);
        }
        if (StringUtils.hasText(avatar)) {
            user.setAvatar(avatar);
        }
        if (StringUtils.hasText(email)) {
            user.setEmail(email);
        }
        userMapper.updateById(user);
        log.info("用户信息更新成功: userId={}", userId);
    }

    // ==================== 收货地址相关 ====================

    @Override
    public List<Map<String, Object>> getAddresses(Long userId) {
        List<AddressPO> addresses = addressMapper.selectByUserId(userId);
        return addresses.stream()
                .map(this::convertAddressToMap)
                .collect(Collectors.toList());
    }

    @Override
    @Transactional
    public Long addAddress(Long userId, Map<String, Object> data) {
        AddressPO address = new AddressPO();
        address.setUserId(userId);
        address.setName((String) data.get("name"));
        address.setPhone((String) data.get("phone"));
        address.setProvince((String) data.get("province"));
        address.setCity((String) data.get("city"));
        address.setDistrict((String) data.get("district"));
        address.setDetail((String) data.get("detail"));
        
        // 处理默认地址
        Object isDefaultObj = data.get("isDefault");
        boolean isDefault = false;
        if (isDefaultObj instanceof Boolean) {
            isDefault = (Boolean) isDefaultObj;
        } else if (isDefaultObj != null) {
            isDefault = "1".equals(isDefaultObj.toString()) || "true".equalsIgnoreCase(isDefaultObj.toString());
        }
        
        if (isDefault) {
            // 重置其他地址为非默认
            addressMapper.resetDefault(userId);
        }
        address.setIsDefault(isDefault ? 1 : 0);
        address.setDeleted(0);

        addressMapper.insert(address);
        log.info("用户添加收货地址: userId={}, addressId={}", userId, address.getId());
        return address.getId();
    }

    @Override
    @Transactional
    public void updateAddress(Long userId, Long addressId, Map<String, Object> data) {
        AddressPO address = addressMapper.selectById(addressId);
        if (address == null || !address.getUserId().equals(userId) || address.getDeleted() == 1) {
            throw new BusinessException(ResultCode.FAIL, "地址不存在");
        }

        if (data.containsKey("name")) {
            address.setName((String) data.get("name"));
        }
        if (data.containsKey("phone")) {
            address.setPhone((String) data.get("phone"));
        }
        if (data.containsKey("province")) {
            address.setProvince((String) data.get("province"));
        }
        if (data.containsKey("city")) {
            address.setCity((String) data.get("city"));
        }
        if (data.containsKey("district")) {
            address.setDistrict((String) data.get("district"));
        }
        if (data.containsKey("detail")) {
            address.setDetail((String) data.get("detail"));
        }
        if (data.containsKey("isDefault")) {
            Object isDefaultObj = data.get("isDefault");
            boolean isDefault = false;
            if (isDefaultObj instanceof Boolean) {
                isDefault = (Boolean) isDefaultObj;
            } else if (isDefaultObj != null) {
                isDefault = "1".equals(isDefaultObj.toString()) || "true".equalsIgnoreCase(isDefaultObj.toString());
            }
            if (isDefault) {
                addressMapper.resetDefault(userId);
            }
            address.setIsDefault(isDefault ? 1 : 0);
        }

        addressMapper.updateById(address);
        log.info("用户更新收货地址: userId={}, addressId={}", userId, addressId);
    }

    @Override
    @Transactional
    public void deleteAddress(Long userId, Long addressId) {
        AddressPO address = addressMapper.selectById(addressId);
        if (address == null || !address.getUserId().equals(userId)) {
            throw new BusinessException(ResultCode.FAIL, "地址不存在");
        }

        address.setDeleted(1);
        addressMapper.updateById(address);
        log.info("用户删除收货地址: userId={}, addressId={}", userId, addressId);
    }

    @Override
    @Transactional
    public void setDefaultAddress(Long userId, Long addressId) {
        AddressPO address = addressMapper.selectById(addressId);
        if (address == null || !address.getUserId().equals(userId) || address.getDeleted() == 1) {
            throw new BusinessException(ResultCode.FAIL, "地址不存在");
        }

        // 重置所有地址为非默认
        addressMapper.resetDefault(userId);
        // 设置当前地址为默认
        address.setIsDefault(1);
        addressMapper.updateById(address);
        log.info("用户设置默认地址: userId={}, addressId={}", userId, addressId);
    }

    private Map<String, Object> convertAddressToMap(AddressPO address) {
        Map<String, Object> map = new HashMap<>();
        map.put("id", address.getId());
        map.put("name", address.getName());
        map.put("phone", address.getPhone());
        map.put("province", address.getProvince());
        map.put("city", address.getCity());
        map.put("district", address.getDistrict());
        map.put("detail", address.getDetail());
        map.put("isDefault", address.getIsDefault() == 1);
        return map;
    }

    // ==================== 商品收藏相关 ====================

    @Override
    public List<Map<String, Object>> getFavorites(Long userId) {
        List<FavoritePO> favorites = favoriteMapper.selectByUserId(userId);
        return favorites.stream()
                .map(fav -> {
                    MedicinePO medicine = medicineMapper.selectById(fav.getMedicineId());
                    if (medicine == null || medicine.getDeleted() == 1) {
                        return null;
                    }
                    Map<String, Object> map = new HashMap<>();
                    map.put("id", fav.getId());
                    map.put("medicineId", medicine.getId());
                    map.put("name", medicine.getName());
                    map.put("image", medicine.getImage());
                    map.put("price", medicine.getPrice());
                    map.put("originalPrice", medicine.getOriginalPrice());
                    map.put("specification", medicine.getSpecification());
                    map.put("stock", medicine.getStock());
                    map.put("status", medicine.getStatus());
                    map.put("isPrescription", medicine.getIsPrescription());
                    return map;
                })
                .filter(map -> map != null)
                .collect(Collectors.toList());
    }

    @Override
    @Transactional
    public void addFavorite(Long userId, Long medicineId) {
        // 检查药品是否存在
        MedicinePO medicine = medicineMapper.selectById(medicineId);
        if (medicine == null || medicine.getDeleted() == 1) {
            throw new BusinessException(ResultCode.MEDICINE_NOT_EXIST);
        }

        // 检查是否已收藏
        FavoritePO existing = favoriteMapper.selectByUserIdAndMedicineId(userId, medicineId);
        if (existing != null) {
            return; // 已收藏，直接返回
        }

        FavoritePO favorite = new FavoritePO();
        favorite.setUserId(userId);
        favorite.setMedicineId(medicineId);
        favoriteMapper.insert(favorite);
        log.info("用户添加收藏: userId={}, medicineId={}", userId, medicineId);
    }

    @Override
    @Transactional
    public void removeFavorite(Long userId, Long medicineId) {
        favoriteMapper.deleteByUserIdAndMedicineId(userId, medicineId);
        log.info("用户取消收藏: userId={}, medicineId={}", userId, medicineId);
    }

    @Override
    public boolean isFavorite(Long userId, Long medicineId) {
        FavoritePO favorite = favoriteMapper.selectByUserIdAndMedicineId(userId, medicineId);
        return favorite != null;
    }
}
