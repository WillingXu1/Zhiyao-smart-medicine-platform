package com.zhiyao.application.dto;

import lombok.Data;

/**
 * 骑手注册DTO
 */
@Data
public class RiderRegisterDTO {
    
    /** 手机号 */
    private String phone;
    
    /** 密码 */
    private String password;
    
    /** 姓名 */
    private String name;
    
    /** 身份证号 */
    private String idCard;
}
