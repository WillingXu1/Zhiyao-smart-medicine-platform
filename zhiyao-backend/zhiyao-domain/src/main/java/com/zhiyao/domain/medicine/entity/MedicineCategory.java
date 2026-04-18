package com.zhiyao.domain.medicine.entity;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import lombok.Builder;

import java.io.Serializable;
import java.time.LocalDateTime;

/**
 * 药品分类实体
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class MedicineCategory implements Serializable {

    private static final long serialVersionUID = 1L;

    /** 分类ID */
    private Long id;

    /** 父分类ID */
    private Long parentId;

    /** 分类名称 */
    private String name;

    /** 分类图标 */
    private String icon;

    /** 分类层级 */
    private Integer level;

    /** 排序 */
    private Integer sort;

    /** 状态：0-禁用 1-启用 */
    private Integer status;

    /** 创建时间 */
    private LocalDateTime createTime;

    /** 更新时间 */
    private LocalDateTime updateTime;

    /** 逻辑删除标识 */
    private Integer deleted;

    /**
     * 判断是否为顶级分类
     */
    public boolean isTopLevel() {
        return this.parentId == null || this.parentId == 0;
    }
}
