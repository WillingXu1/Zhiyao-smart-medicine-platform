package com.zhiyao.infrastructure.persistence.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.zhiyao.infrastructure.persistence.po.OrderPO;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

/**
 * 订单Mapper接口
 */
@Mapper
public interface OrderMapper extends BaseMapper<OrderPO> {

    /**
     * 根据订单号查询订单
     */
    @Select("SELECT * FROM orders WHERE order_no = #{orderNo} AND deleted = 0")
    OrderPO selectByOrderNo(@Param("orderNo") String orderNo);
}
