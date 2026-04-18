package com.zhiyao.infrastructure.persistence.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.zhiyao.infrastructure.persistence.po.RiderPO;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

/**
 * 骑手Mapper接口
 */
@Mapper
public interface RiderMapper extends BaseMapper<RiderPO> {

    /**
     * 根据用户ID查询骑手
     */
    @Select("SELECT * FROM rider WHERE user_id = #{userId} AND deleted = 0")
    RiderPO selectByUserId(@Param("userId") Long userId);

    /**
     * 根据手机号查询骑手（通过 user 表关联）
     * 注意：rider 表中没有 phone 字段，需要通过 user_id 关联查询
     */
    @Select("SELECT r.* FROM rider r " +
            "INNER JOIN sys_user u ON r.user_id = u.id " +
            "WHERE u.phone = #{phone} AND r.deleted = 0 AND u.deleted = 0")
    RiderPO selectByPhone(@Param("phone") String phone);
}
