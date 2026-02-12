package com.zhiyao.infrastructure.persistence.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.zhiyao.infrastructure.persistence.po.DeliveryExceptionPO;
import org.apache.ibatis.annotations.Mapper;

/**
 * 配送异常Mapper接口
 */
@Mapper
public interface DeliveryExceptionMapper extends BaseMapper<DeliveryExceptionPO> {
}
