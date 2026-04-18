package com.zhiyao.domain.rider.entity;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import lombok.Builder;

import java.io.Serializable;
import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 骑手实体
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Rider implements Serializable {

    private static final long serialVersionUID = 1L;

    /** 骑手ID */
    private Long id;

    /** 用户ID（关联登录账号） */
    private Long userId;

    /** 姓名 */
    private String name;

    /** 手机号 */
    private String phone;

    /** 头像 */
    private String avatar;

    /** 身份证号 */
    private String idCard;

    /** 当前经度 */
    private Double longitude;

    /** 当前纬度 */
    private Double latitude;

    /** 在线状态：0-离线 1-在线 */
    private Integer onlineStatus;

    /** 接单状态：0-休息 1-接单中 */
    private Integer workStatus;

    /** 累计配送单数 */
    private Integer totalOrders;

    /** 评分 */
    private BigDecimal rating;

    /** 状态：0-禁用 1-正常 */
    private Integer status;

    /** 审核状态：0-待审核 1-审核通过 2-审核拒绝 */
    private Integer auditStatus;

    /** 创建时间 */
    private LocalDateTime createTime;

    /** 更新时间 */
    private LocalDateTime updateTime;

    /** 逻辑删除标识 */
    private Integer deleted;

    /**
     * 判断是否可接单
     */
    public boolean canAcceptOrder() {
        return this.onlineStatus != null && this.onlineStatus == 1
            && this.workStatus != null && this.workStatus == 1
            && this.status != null && this.status == 1;
    }
}
