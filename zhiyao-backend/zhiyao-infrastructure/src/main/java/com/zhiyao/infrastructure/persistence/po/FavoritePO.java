package com.zhiyao.infrastructure.persistence.po;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

import java.io.Serializable;
import java.time.LocalDateTime;

/**
 * 收藏持久化对象
 */
@Data
@TableName("favorite")
public class FavoritePO implements Serializable {

    private static final long serialVersionUID = 1L;

    @TableId(type = IdType.AUTO)
    private Long id;

    private Long userId;

    private Long medicineId;

    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;
}
