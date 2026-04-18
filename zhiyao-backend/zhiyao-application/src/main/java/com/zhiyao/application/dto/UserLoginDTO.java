package com.zhiyao.application.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

/**
 * 用户登录DTO
 */
@Data
public class UserLoginDTO {

    @NotBlank(message = "用户名/手机号不能为空")
    private String username;

    @NotBlank(message = "密码不能为空")
    private String password;
}
