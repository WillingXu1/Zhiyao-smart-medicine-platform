package com.zhiyao.common.enums;

import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * 用户角色枚举
 */
@Getter
@AllArgsConstructor
public enum UserRole {

    USER(1, "用户"),
    MERCHANT(2, "商家"),
    ADMIN(3, "管理员"),
    RIDER(4, "骑手");

    private final Integer code;
    private final String desc;

    public static UserRole fromCode(Integer code) {
        for (UserRole role : values()) {
            if (role.code.equals(code)) {
                return role;
            }
        }
        return null;
    }
}
