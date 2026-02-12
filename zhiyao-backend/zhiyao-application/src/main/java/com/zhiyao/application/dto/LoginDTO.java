package com.zhiyao.application.dto;

import lombok.Data;

/**
 * 登录请求DTO
 */
@Data
public class LoginDTO {
    /**
     * 手机号/用户名
     */
    private String phone;
    
    /**
     * 密码
     */
    private String password;
    
    /**
     * 验证码（可选）
     */
    private String code;
}
