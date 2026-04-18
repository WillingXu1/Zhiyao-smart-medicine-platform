package com.zhiyao.application.dto;

import lombok.Data;

/**
 * 审核请求DTO
 */
@Data
public class AuditDTO {
    /**
     * 审核状态 (1=通过, 2=拒绝)
     */
    private Integer status;
    
    /**
     * 审核原因/备注
     */
    private String reason;
    
    /**
     * 药品分类ID（审核药品时可修改）
     */
    private Long categoryId;
}
