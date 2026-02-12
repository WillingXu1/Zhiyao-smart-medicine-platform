package com.zhiyao.infrastructure.persistence.po;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

import java.io.Serializable;
import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 药品持久化对象
 */
@Data
@TableName("medicine")
public class MedicinePO implements Serializable {

    private static final long serialVersionUID = 1L;

    @TableId(type = IdType.AUTO)
    private Long id;

    private Long merchantId;

    private Long categoryId;

    private String name;

    private String commonName;

    private String image;

    private String images;

    private String specification;

    private String manufacturer;

    private String approvalNumber;

    private BigDecimal price;

    private BigDecimal originalPrice;

    private Integer stock;

    private Integer sales;

    private Integer isPrescription;

    private String efficacy;

    private String dosage;

    private String adverseReactions;

    private String contraindications;

    private String precautions;

    private String riskTips;

    private String tags;

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
