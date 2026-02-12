package com.zhiyao.application.service;

import com.zhiyao.common.result.PageResult;

import java.util.List;
import java.util.Map;

/**
 * 药品应用服务接口
 */
public interface MedicineService {

    /**
     * 搜索药品
     */
    PageResult<Map<String, Object>> searchMedicines(String keyword, Long categoryId, Long merchantId,
                                                     Integer isPrescription, String sortBy, String sortOrder,
                                                     Integer pageNum, Integer pageSize);

    /**
     * 获取药品详情
     */
    Map<String, Object> getMedicineDetail(Long id);

    /**
     * 获取药品分类列表
     */
    List<Map<String, Object>> getCategories();

    /**
     * 获取热销药品
     */
    List<Map<String, Object>> getHotMedicines(Integer limit);

    /**
     * 根据分类获取药品
     */
    PageResult<Map<String, Object>> getMedicinesByCategory(Long categoryId, Integer pageNum, Integer pageSize);

    /**
     * 商家添加药品
     */
    Long addMedicine(Long merchantId, Map<String, Object> medicineDTO);

    /**
     * 商家更新药品
     */
    void updateMedicine(Long merchantId, Long medicineId, Map<String, Object> medicineDTO);

    /**
     * 商家删除药品
     */
    void deleteMedicine(Long merchantId, Long medicineId);

    /**
     * 上架/下架药品
     */
    void updateMedicineStatus(Long merchantId, Long medicineId, Integer status);
}
