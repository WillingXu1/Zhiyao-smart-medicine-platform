package com.zhiyao.infrastructure.persistence.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.zhiyao.infrastructure.persistence.po.MedicinePO;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.util.List;

/**
 * 药品Mapper接口
 */
@Mapper
public interface MedicineMapper extends BaseMapper<MedicinePO> {

    /**
     * 获取热销药品
     */
    @Select("SELECT * FROM medicine WHERE status = 1 AND audit_status = 1 AND deleted = 0 ORDER BY sales DESC LIMIT #{limit}")
    List<MedicinePO> selectHotMedicines(@Param("limit") Integer limit);

    /**
     * 根据分类ID查询药品
     */
    @Select("SELECT * FROM medicine WHERE category_id = #{categoryId} AND status = 1 AND deleted = 0")
    List<MedicinePO> selectByCategoryId(@Param("categoryId") Long categoryId);
}
