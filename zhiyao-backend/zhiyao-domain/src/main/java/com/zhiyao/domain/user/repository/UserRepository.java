package com.zhiyao.domain.user.repository;

import com.zhiyao.domain.user.entity.User;

import java.util.Optional;

/**
 * 用户仓储接口
 */
public interface UserRepository {

    /**
     * 根据ID查询用户
     */
    Optional<User> findById(Long id);

    /**
     * 根据用户名查询用户
     */
    Optional<User> findByUsername(String username);

    /**
     * 根据手机号查询用户
     */
    Optional<User> findByPhone(String phone);

    /**
     * 保存用户
     */
    User save(User user);

    /**
     * 更新用户
     */
    User update(User user);

    /**
     * 检查用户名是否存在
     */
    boolean existsByUsername(String username);

    /**
     * 检查手机号是否存在
     */
    boolean existsByPhone(String phone);
}
