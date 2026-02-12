package com.zhiyao.infrastructure.persistence.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.zhiyao.infrastructure.persistence.po.AddressPO;
import org.apache.ibatis.annotations.*;

import java.util.List;

/**
 * 收货地址Mapper
 */
@Mapper
public interface AddressMapper extends BaseMapper<AddressPO> {

    /**
     * 根据用户ID查询地址列表
     */
    @Select("SELECT * FROM address WHERE user_id = #{userId} AND deleted = 0 ORDER BY is_default DESC, create_time DESC")
    List<AddressPO> selectByUserId(@Param("userId") Long userId);

    /**
     * 重置用户所有地址为非默认
     */
    @Update("UPDATE address SET is_default = 0 WHERE user_id = #{userId}")
    void resetDefault(@Param("userId") Long userId);
}
