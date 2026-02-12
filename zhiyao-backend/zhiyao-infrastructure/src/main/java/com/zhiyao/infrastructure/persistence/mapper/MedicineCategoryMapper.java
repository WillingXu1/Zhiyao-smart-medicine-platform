package com.zhiyao.infrastructure.persistence.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.zhiyao.infrastructure.persistence.po.MedicineCategoryPO;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Select;

import java.util.List;

/**
 * 药品分类Mapper接口
 */
@Mapper
public interface MedicineCategoryMapper extends BaseMapper<MedicineCategoryPO> {

    /**
     * 获取所有启用的分类
     */
    @Select("SELECT * FROM medicine_category WHERE status = 1 AND deleted = 0 ORDER BY sort ASC")
    List<MedicineCategoryPO> selectAllEnabled();
}
