package com.zhiyao.infrastructure.persistence.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.zhiyao.infrastructure.persistence.po.UserPO;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

/**
 * 用户Mapper接口
 */
@Mapper
public interface UserMapper extends BaseMapper<UserPO> {

    /**
     * 根据用户名查询
     */
    @Select("SELECT * FROM sys_user WHERE username = #{username} AND deleted = 0")
    UserPO selectByUsername(@Param("username") String username);

    /**
     * 根据手机号查询
     */
    @Select("SELECT * FROM sys_user WHERE phone = #{phone} AND deleted = 0")
    UserPO selectByPhone(@Param("phone") String phone);

    /**
     * 检查用户名是否存在
     */
    @Select("SELECT COUNT(1) FROM sys_user WHERE username = #{username} AND deleted = 0")
    int countByUsername(@Param("username") String username);

    /**
     * 检查手机号是否存在
     */
    @Select("SELECT COUNT(1) FROM sys_user WHERE phone = #{phone} AND deleted = 0")
    int countByPhone(@Param("phone") String phone);
}
