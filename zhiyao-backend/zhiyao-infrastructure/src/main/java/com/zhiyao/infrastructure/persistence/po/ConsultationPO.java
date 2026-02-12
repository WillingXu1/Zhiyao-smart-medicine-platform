package com.zhiyao.infrastructure.persistence.po;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

import java.io.Serializable;
import java.time.LocalDateTime;

/**
 * 用药咨询持久化对象
 */
@Data
@TableName("consultation")
public class ConsultationPO implements Serializable {

    private static final long serialVersionUID = 1L;

    @TableId(type = IdType.AUTO)
    private Long id;

    /** 用户ID */
    private Long userId;

    /** 会话ID，用于标识一次完整对话 */
    private String sessionId;

    /** 消息角色：user-用户 assistant-AI */
    private String role;

    /** 消息内容 */
    private String content;

    /** 咨询类型：1-用药咨询 2-症状咨询 3-药品查询 */
    private Integer consultType;

    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;

    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updateTime;

    @TableLogic
    private Integer deleted;
}
