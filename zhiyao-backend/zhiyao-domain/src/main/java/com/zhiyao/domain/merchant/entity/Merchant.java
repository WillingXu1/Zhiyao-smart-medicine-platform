package com.zhiyao.domain.merchant.entity;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import lombok.Builder;

import java.io.Serializable;
import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 商家（药店）实体
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Merchant implements Serializable {

    private static final long serialVersionUID = 1L;

    /** 商家ID */
    private Long id;

    /** 用户ID（关联登录账号） */
    private Long userId;

    /** 店铺名称 */
    private String shopName;

    /** 店铺Logo */
    private String logo;

    /** 店铺封面图 */
    private String coverImage;

    /** 联系人姓名 */
    private String contactName;

    /** 联系电话 */
    private String contactPhone;

    /** 省份 */
    private String province;

    /** 城市 */
    private String city;

    /** 区县 */
    private String district;

    /** 详细地址 */
    private String address;

    /** 完整地址 */
    private String fullAddress;

    /** 经度 */
    private Double longitude;

    /** 纬度 */
    private Double latitude;

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

    /** 配送费 */
    private BigDecimal deliveryFee;

    /** 起送金额 */
    private BigDecimal minOrderAmount;

    /** 配送范围（公里） */
    private Integer deliveryRange;

    /** 店铺评分 */
    private BigDecimal rating;

    /** 月销量 */
    private Integer monthlySales;

    /** 状态：0-关闭 1-营业中 */
    private Integer status;

    /** 审核状态：0-待审核 1-审核通过 2-审核拒绝 */
    private Integer auditStatus;

    /** 审核备注 */
    private String auditRemark;

    /** 创建时间 */
    private LocalDateTime createTime;

    /** 更新时间 */
    private LocalDateTime updateTime;

    /** 逻辑删除标识 */
    private Integer deleted;

    /**
     * 判断是否营业中
     */
    public boolean isOpen() {
        return this.status != null && this.status == 1;
    }

    /**
     * 判断是否审核通过
     */
    public boolean isApproved() {
        return this.auditStatus != null && this.auditStatus == 1;
    }

    /**
     * 获取完整地址
     */
    public String getFullAddress() {
        if (this.fullAddress != null) {
            return this.fullAddress;
        }
        StringBuilder sb = new StringBuilder();
        if (province != null) sb.append(province);
        if (city != null) sb.append(city);
        if (district != null) sb.append(district);
        if (address != null) sb.append(address);
        return sb.toString();
    }
}
