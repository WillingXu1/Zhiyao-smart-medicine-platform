package com.zhiyao.domain.user.entity;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import lombok.Builder;

import java.io.Serializable;
import java.time.LocalDateTime;

/**
 * 用户收货地址实体
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class UserAddress implements Serializable {

    private static final long serialVersionUID = 1L;

    /** 地址ID */
    private Long id;

    /** 用户ID */
    private Long userId;

    /** 收货人姓名 */
    private String receiverName;

    /** 收货人手机号 */
    private String receiverPhone;

    /** 省份 */
    private String province;

    /** 城市 */
    private String city;

    /** 区县 */
    private String district;

    /** 详细地址 */
    private String detailAddress;

    /** 完整地址 */
    private String fullAddress;

    /** 经度 */
    private Double longitude;

    /** 纬度 */
    private Double latitude;

    /** 是否默认地址：0-否 1-是 */
    private Integer isDefault;

    /** 标签：家、公司、学校等 */
    private String tag;

    /** 创建时间 */
    private LocalDateTime createTime;

    /** 更新时间 */
    private LocalDateTime updateTime;

    /** 逻辑删除标识 */
    private Integer deleted;

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
        if (detailAddress != null) sb.append(detailAddress);
        return sb.toString();
    }

    /**
     * 判断是否为默认地址
     */
    public boolean isDefaultAddress() {
        return this.isDefault != null && this.isDefault == 1;
    }
}
