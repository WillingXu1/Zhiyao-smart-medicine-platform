package com.zhiyao.application.dto;

import lombok.Data;

/**
 * 管理员个人信息DTO
 */
@Data
public class AdminProfileDTO {
    
    /** 姓名 */
    private String name;
    
    /** 邮箱 */
    private String email;
    
    /** 手机号 */
    private String phone;
    
    /** 头像URL */
    private String avatar;
}
