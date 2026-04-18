package com.zhiyao.infrastructure.persistence.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.zhiyao.infrastructure.persistence.po.FavoritePO;
import org.apache.ibatis.annotations.*;

import java.util.List;

/**
 * 收藏Mapper
 */
@Mapper
public interface FavoriteMapper extends BaseMapper<FavoritePO> {

    /**
     * 根据用户ID查询收藏列表
     */
    @Select("SELECT * FROM favorite WHERE user_id = #{userId} ORDER BY create_time DESC")
    List<FavoritePO> selectByUserId(@Param("userId") Long userId);

    /**
     * 根据用户ID和药品ID查询收藏
     */
    @Select("SELECT * FROM favorite WHERE user_id = #{userId} AND medicine_id = #{medicineId} LIMIT 1")
    FavoritePO selectByUserIdAndMedicineId(@Param("userId") Long userId, @Param("medicineId") Long medicineId);

    /**
     * 删除收藏
     */
    @Delete("DELETE FROM favorite WHERE user_id = #{userId} AND medicine_id = #{medicineId}")
    void deleteByUserIdAndMedicineId(@Param("userId") Long userId, @Param("medicineId") Long medicineId);
}
