package com.zhiyao.application.dto;

import lombok.Data;
import java.math.BigDecimal;

/**
 * 平台配置DTO
 */
@Data
public class PlatformConfigDTO {
    
    /** 平台名称 */
    private String platformName;
    
    /** 联系电话 */
    private String contactPhone;
    
    /** 配送费 */
    private BigDecimal deliveryFee;
    
    /** 起送金额 */
    private BigDecimal minOrderAmount;
    
    /** 配送范围(公里) */
    private Integer deliveryRange;
}
