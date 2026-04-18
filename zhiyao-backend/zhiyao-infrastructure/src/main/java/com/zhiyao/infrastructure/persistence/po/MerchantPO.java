package com.zhiyao.infrastructure.persistence.po;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

import java.io.Serializable;
import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 商家持久化对象
 */
@Data
@TableName("merchant")
public class MerchantPO implements Serializable {

    private static final long serialVersionUID = 1L;

    @TableId(type = IdType.AUTO)
    private Long id;

    private Long userId;

    @TableField("shop_name")
    private String shopName;

    private String logo;

    private String coverImage;

    private String contactName;

    private String contactPhone;

    private String province;

    private String city;

    private String district;

    private String address;

    private String fullAddress;

    /** 店铺简介 */
    private String description;

    private BigDecimal longitude;

    private BigDecimal latitude;

    /** 营业执照号 */
    private String businessLicense;

    /** 营业执照图片 */
    private String businessLicenseImage;

    /** 药品经营许可证号 */
    private String drugLicense;

    /** 药品经营许可证图片 */
    private String drugLicenseImage;

    /** 营业开始时间 */
    private String openTime;

    /** 营业结束时间 */
    private String closeTime;

    private BigDecimal deliveryFee;

    private BigDecimal minOrderAmount;

    private Integer deliveryRange;

    private BigDecimal rating;

    private Integer monthlySales;

    private Integer status;

    private Integer auditStatus;

    private String auditRemark;

    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;

    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updateTime;

    @TableLogic
    private Integer deleted;
}
