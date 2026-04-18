package com.zhiyao.infrastructure.persistence.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.zhiyao.infrastructure.persistence.po.MerchantPO;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

/**
 * 商家Mapper接口
 */
@Mapper
public interface MerchantMapper extends BaseMapper<MerchantPO> {

    /**
     * 根据用户ID查询商家
     */
    @Select("SELECT * FROM merchant WHERE user_id = #{userId} AND deleted = 0")
    MerchantPO selectByUserId(@Param("userId") Long userId);
}
