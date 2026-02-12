package com.zhiyao.application.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Data;

/**
 * 修改密码DTO
 */
@Data
public class ChangePasswordDTO {
    
    /** 原密码 */
    @NotBlank(message = "原密码不能为空")
    private String oldPassword;
    
    /** 新密码 */
    @NotBlank(message = "新密码不能为空")
    @Size(min = 6, message = "密码长度不能少于6位")
    private String newPassword;
    
    /** 确认密码 */
    @NotBlank(message = "确认密码不能为空")
    private String confirmPassword;
}
