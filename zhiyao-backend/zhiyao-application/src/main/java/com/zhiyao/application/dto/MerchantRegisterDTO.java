package com.zhiyao.application.dto;

import lombok.Data;
import java.util.Map;

/**
 * 商家注册DTO
 */
@Data
public class MerchantRegisterDTO {
    
    /** 手机号 */
    private String phone;
    
    /** 密码 */
    private String password;
    
    /** 店铺名称 */
    private String name;
    
    /** 店铺地址 */
    private String address;
    
    /** 营业时间 */
    private String businessHours;
    
    /** 营业执照（可以是字符串或对象） */
    private Object businessLicense;
    
    /** 药品经营许可证（可以是字符串或对象） */
    private Object pharmacistLicense;
    
    /** 联系人姓名 */
    private String contactName;
    
    /** 联系电话 */
    private String contactPhone;
    
    /** 店铺Logo */
    private String logo;
    
    /**
     * 获取营业执照号或图片URL
     */
    public String getBusinessLicenseValue() {
        if (businessLicense == null) {
            return null;
        }
        if (businessLicense instanceof String) {
            return (String) businessLicense;
        }
        if (businessLicense instanceof Map) {
            Map<?, ?> map = (Map<?, ?>) businessLicense;
            // 优先取url，其次取value
            Object url = map.get("url");
            if (url != null) return url.toString();
            Object value = map.get("value");
            if (value != null) return value.toString();
        }
        return businessLicense.toString();
    }
    
    /**
     * 获取药品经营许可证号或图片URL
     */
    public String getPharmacistLicenseValue() {
        if (pharmacistLicense == null) {
            return null;
        }
        if (pharmacistLicense instanceof String) {
            return (String) pharmacistLicense;
        }
        if (pharmacistLicense instanceof Map) {
            Map<?, ?> map = (Map<?, ?>) pharmacistLicense;
            Object url = map.get("url");
            if (url != null) return url.toString();
            Object value = map.get("value");
            if (value != null) return value.toString();
        }
        return pharmacistLicense.toString();
    }
}
