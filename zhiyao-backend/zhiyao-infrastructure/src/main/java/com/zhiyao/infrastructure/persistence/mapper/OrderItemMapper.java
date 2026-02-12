package com.zhiyao.infrastructure.persistence.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.zhiyao.infrastructure.persistence.po.OrderItemPO;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.util.List;

/**
 * 订单项Mapper接口
 */
@Mapper
public interface OrderItemMapper extends BaseMapper<OrderItemPO> {

    /**
     * 根据订单ID查询订单项
     */
    @Select("SELECT * FROM order_item WHERE order_id = #{orderId}")
    List<OrderItemPO> selectByOrderId(@Param("orderId") Long orderId);
}
