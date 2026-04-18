package com.zhiyao.infrastructure.persistence.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.zhiyao.infrastructure.persistence.po.ConsultationPO;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.util.List;

/**
 * 用药咨询Mapper
 */
@Mapper
public interface ConsultationMapper extends BaseMapper<ConsultationPO> {

    /**
     * 根据会话ID查询对话历史
     */
    @Select("SELECT * FROM consultation WHERE session_id = #{sessionId} AND deleted = 0 ORDER BY create_time ASC")
    List<ConsultationPO> selectBySessionId(@Param("sessionId") String sessionId);

    /**
     * 根据用户ID查询最近的会话
     */
    @Select("SELECT DISTINCT session_id FROM consultation WHERE user_id = #{userId} AND deleted = 0 ORDER BY create_time DESC LIMIT 10")
    List<String> selectRecentSessions(@Param("userId") Long userId);

    /**
     * 根据用户ID查询最近一次会话的所有消息
     */
    @Select("SELECT * FROM consultation WHERE user_id = #{userId} AND deleted = 0 " +
            "AND session_id = (SELECT session_id FROM consultation WHERE user_id = #{userId} AND deleted = 0 ORDER BY create_time DESC LIMIT 1) " +
            "ORDER BY create_time ASC")
    List<ConsultationPO> selectLatestSessionByUserId(@Param("userId") Long userId);
}
