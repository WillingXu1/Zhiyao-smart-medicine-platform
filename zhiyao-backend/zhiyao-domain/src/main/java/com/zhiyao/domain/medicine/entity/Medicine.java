package com.zhiyao.domain.medicine.entity;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import lombok.Builder;

import java.io.Serializable;
import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 药品实体
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Medicine implements Serializable {

    private static final long serialVersionUID = 1L;

    /** 药品ID */
    private Long id;

    /** 商家ID */
    private Long merchantId;

    /** 分类ID */
    private Long categoryId;

    /** 药品名称 */
    private String name;

    /** 通用名 */
    private String commonName;

    /** 药品图片 */
    private String image;

    /** 药品图片列表（JSON数组） */
    private String images;

    /** 规格 */
    private String specification;

    /** 生产厂家 */
    private String manufacturer;

    /** 批准文号 */
    private String approvalNumber;

    /** 售价 */
    private BigDecimal price;

    /** 原价 */
    private BigDecimal originalPrice;

    /** 库存 */
    private Integer stock;

    /** 销量 */
    private Integer sales;

    /** 是否处方药：0-非处方药 1-处方药 */
    private Integer isPrescription;

    /** 功效说明 */
    private String efficacy;

    /** 用法用量 */
    private String dosage;

    /** 不良反应 */
    private String adverseReactions;

    /** 禁忌 */
    private String contraindications;

    /** 注意事项 */
    private String precautions;

    /** 用药风险提示 */
    private String riskTips;

    /** 标签（JSON数组） */
    private String tags;

    /** 状态：0-下架 1-上架 2-审核中 */
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
     * 判断是否为处方药
     */
    public boolean isPrescriptionMedicine() {
        return this.isPrescription != null && this.isPrescription == 1;
    }

    /**
     * 判断是否上架
     */
    public boolean isOnShelf() {
        return this.status != null && this.status == 1;
    }

    /**
     * 判断库存是否充足
     */
    public boolean hasStock(int quantity) {
        return this.stock != null && this.stock >= quantity;
    }

    /**
     * 扣减库存
     */
    public void deductStock(int quantity) {
        if (hasStock(quantity)) {
            this.stock -= quantity;
        }
    }

    /**
     * 增加销量
     */
    public void addSales(int quantity) {
        if (this.sales == null) {
            this.sales = 0;
        }
        this.sales += quantity;
    }
}
