package com.zhiyao.application.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.zhiyao.application.service.MedicineService;
import com.zhiyao.common.exception.BusinessException;
import com.zhiyao.common.result.PageResult;
import com.zhiyao.common.result.ResultCode;
import com.zhiyao.infrastructure.persistence.mapper.MedicineCategoryMapper;
import com.zhiyao.infrastructure.persistence.mapper.MedicineMapper;
import com.zhiyao.infrastructure.persistence.po.MedicineCategoryPO;
import com.zhiyao.infrastructure.persistence.po.MedicinePO;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import java.math.BigDecimal;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * 药品服务实现类
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class MedicineServiceImpl implements MedicineService {

    private final MedicineMapper medicineMapper;
    private final MedicineCategoryMapper categoryMapper;

    @Override
    public PageResult<Map<String, Object>> searchMedicines(String keyword, Long categoryId, Long merchantId,
                                                           Integer isPrescription, String sortBy, String sortOrder,
                                                           Integer pageNum, Integer pageSize) {
        log.info("药品搜索参数: keyword={}, categoryId={}, merchantId={}, isPrescription={}, sortBy={}, sortOrder={}, pageNum={}, pageSize={}",
                keyword, categoryId, merchantId, isPrescription, sortBy, sortOrder, pageNum, pageSize);
        
        LambdaQueryWrapper<MedicinePO> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(MedicinePO::getStatus, 1)  // 只查询上架的药品
                .eq(MedicinePO::getAuditStatus, 1)  // 只查询审核通过的药品
                .eq(MedicinePO::getDeleted, 0);

        // 关键词搜索
        if (StringUtils.hasText(keyword)) {
            wrapper.and(w -> w.like(MedicinePO::getName, keyword)
                    .or().like(MedicinePO::getCommonName, keyword)
                    .or().like(MedicinePO::getEfficacy, keyword));
        }

        // 分类筛选
        if (categoryId != null) {
            wrapper.eq(MedicinePO::getCategoryId, categoryId);
        }

        // 商家筛选
        if (merchantId != null) {
            wrapper.eq(MedicinePO::getMerchantId, merchantId);
        }

        // 处方药筛选
        if (isPrescription != null) {
            wrapper.eq(MedicinePO::getIsPrescription, isPrescription);
        }

        // 排序
        if ("price".equals(sortBy)) {
            if ("asc".equals(sortOrder)) {
                wrapper.orderByAsc(MedicinePO::getPrice);
            } else {
                wrapper.orderByDesc(MedicinePO::getPrice);
            }
        } else {
            // 默认按销量排序
            wrapper.orderByDesc(MedicinePO::getSales);
        }

        // 分页查询
        Page<MedicinePO> page = new Page<>(pageNum, pageSize);
        Page<MedicinePO> result = medicineMapper.selectPage(page, wrapper);

        log.info("药品搜索结果: total={}, current={}, size={}", result.getTotal(), result.getCurrent(), result.getSize());
        
        // 转换结果
        List<Map<String, Object>> records = result.getRecords().stream()
                .map(this::convertToMap)
                .collect(Collectors.toList());

        return PageResult.of(result.getTotal(), records, result.getCurrent(), result.getSize());
    }

    @Override
    public Map<String, Object> getMedicineDetail(Long id) {
        MedicinePO medicine = medicineMapper.selectById(id);
        if (medicine == null || medicine.getDeleted() == 1) {
            throw new BusinessException(ResultCode.MEDICINE_NOT_EXIST);
        }
        return convertToDetailMap(medicine);
    }

    @Override
    public List<Map<String, Object>> getCategories() {
        List<MedicineCategoryPO> categories = categoryMapper.selectAllEnabled();
        return categories.stream()
                .map(cat -> {
                    Map<String, Object> map = new HashMap<>();
                    map.put("id", cat.getId());
                    map.put("name", cat.getName());
                    map.put("icon", cat.getIcon());
                    map.put("parentId", cat.getParentId());
                    map.put("level", cat.getLevel());
                    return map;
                })
                .collect(Collectors.toList());
    }

    @Override
    public List<Map<String, Object>> getHotMedicines(Integer limit) {
        List<MedicinePO> medicines = medicineMapper.selectHotMedicines(limit);
        return medicines.stream()
                .map(this::convertToMap)
                .collect(Collectors.toList());
    }

    @Override
    public PageResult<Map<String, Object>> getMedicinesByCategory(Long categoryId, Integer pageNum, Integer pageSize) {
        LambdaQueryWrapper<MedicinePO> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(MedicinePO::getCategoryId, categoryId)
                .eq(MedicinePO::getStatus, 1)
                .eq(MedicinePO::getAuditStatus, 1)  // 只查询审核通过的药品
                .eq(MedicinePO::getDeleted, 0)
                .orderByDesc(MedicinePO::getSales);

        Page<MedicinePO> page = new Page<>(pageNum, pageSize);
        Page<MedicinePO> result = medicineMapper.selectPage(page, wrapper);

        List<Map<String, Object>> records = result.getRecords().stream()
                .map(this::convertToMap)
                .collect(Collectors.toList());

        return PageResult.of(result.getTotal(), records, result.getCurrent(), result.getSize());
    }

    @Override
    @Transactional
    public Long addMedicine(Long merchantId, Map<String, Object> medicineDTO) {
        MedicinePO medicine = new MedicinePO();
        medicine.setMerchantId(merchantId);
        medicine.setName((String) medicineDTO.get("name"));
        medicine.setCommonName((String) medicineDTO.get("commonName"));

        // categoryId处理，默认为1
        Object categoryIdObj = medicineDTO.get("categoryId");
        medicine.setCategoryId(categoryIdObj != null ? Long.valueOf(categoryIdObj.toString()) : 1L);

        medicine.setImage((String) medicineDTO.get("image"));
        medicine.setSpecification((String) medicineDTO.get("specification"));
        medicine.setManufacturer((String) medicineDTO.get("manufacturer"));

        // price处理
        Object priceObj = medicineDTO.get("price");
        medicine.setPrice(priceObj != null ? new BigDecimal(priceObj.toString()) : BigDecimal.ZERO);

        // originalPrice处理
        Object originalPriceObj = medicineDTO.get("originalPrice");
        medicine.setOriginalPrice(originalPriceObj != null ? new BigDecimal(originalPriceObj.toString()) : null);

        // stock处理，默认为0
        Object stockObj = medicineDTO.get("stock");
        medicine.setStock(stockObj != null ? Integer.valueOf(stockObj.toString()) : 0);

        // isPrescription处理，支持Boolean和Integer类型
        Object prescriptionObj = medicineDTO.get("isPrescription");
        if (prescriptionObj instanceof Boolean) {
            medicine.setIsPrescription((Boolean) prescriptionObj ? 1 : 0);
        } else if (prescriptionObj != null) {
            medicine.setIsPrescription(Integer.valueOf(prescriptionObj.toString()));
        } else {
            medicine.setIsPrescription(0);
        }

        // efficacy/indications兼容处理
        String efficacy = (String) medicineDTO.get("efficacy");
        if (efficacy == null) {
            efficacy = (String) medicineDTO.get("indications");
        }
        medicine.setEfficacy(efficacy);

        medicine.setDosage((String) medicineDTO.get("dosage"));
        medicine.setAdverseReactions((String) medicineDTO.get("adverseReactions"));
        medicine.setContraindications((String) medicineDTO.get("contraindications"));
        medicine.setPrecautions((String) medicineDTO.get("precautions"));
        medicine.setRiskTips((String) medicineDTO.get("riskTips"));
        medicine.setApprovalNumber((String) medicineDTO.get("approvalNumber"));
        medicine.setImages((String) medicineDTO.get("images"));
        medicine.setStatus(0);  // 默认下架，需要审核
        medicine.setAuditStatus(0);  // 待审核
        medicine.setSales(0);  // 销量初始化为0
        medicine.setDeleted(0);

        medicineMapper.insert(medicine);
        log.info("商家添加药品: merchantId={}, medicineId={}, name={}", merchantId, medicine.getId(), medicine.getName());
        return medicine.getId();
    }

    @Override
    @Transactional
    public void updateMedicine(Long merchantId, Long medicineId, Map<String, Object> medicineDTO) {
        MedicinePO medicine = medicineMapper.selectById(medicineId);
        if (medicine == null || !medicine.getMerchantId().equals(merchantId)) {
            throw new BusinessException(ResultCode.MEDICINE_NOT_EXIST);
        }

        // 更新字段
        if (medicineDTO.containsKey("name")) {
            medicine.setName((String) medicineDTO.get("name"));
        }
        if (medicineDTO.containsKey("price")) {
            medicine.setPrice(new BigDecimal(medicineDTO.get("price").toString()));
        }
        if (medicineDTO.containsKey("stock")) {
            medicine.setStock(Integer.valueOf(medicineDTO.get("stock").toString()));
        }
        if (medicineDTO.containsKey("specification")) {
            medicine.setSpecification((String) medicineDTO.get("specification"));
        }
        if (medicineDTO.containsKey("manufacturer")) {
            medicine.setManufacturer((String) medicineDTO.get("manufacturer"));
        }
        // efficacy/indications 兼容处理
        if (medicineDTO.containsKey("efficacy")) {
            medicine.setEfficacy((String) medicineDTO.get("efficacy"));
        } else if (medicineDTO.containsKey("indications")) {
            medicine.setEfficacy((String) medicineDTO.get("indications"));
        }
        // isPrescription 处理
        if (medicineDTO.containsKey("isPrescription")) {
            Object prescriptionObj = medicineDTO.get("isPrescription");
            if (prescriptionObj instanceof Boolean) {
                medicine.setIsPrescription((Boolean) prescriptionObj ? 1 : 0);
            } else if (prescriptionObj != null) {
                medicine.setIsPrescription(Integer.valueOf(prescriptionObj.toString()));
            }
        }
        // image 处理
        if (medicineDTO.containsKey("image")) {
            medicine.setImage((String) medicineDTO.get("image"));
        }
        // images 处理
        if (medicineDTO.containsKey("images")) {
            medicine.setImages((String) medicineDTO.get("images"));
        }
        // approvalNumber 处理
        if (medicineDTO.containsKey("approvalNumber")) {
            medicine.setApprovalNumber((String) medicineDTO.get("approvalNumber"));
        }
        // originalPrice 处理
        if (medicineDTO.containsKey("originalPrice")) {
            Object originalPriceObj = medicineDTO.get("originalPrice");
            medicine.setOriginalPrice(originalPriceObj != null ? new BigDecimal(originalPriceObj.toString()) : null);
        }
        // categoryId 处理
        if (medicineDTO.containsKey("categoryId")) {
            Object categoryIdObj = medicineDTO.get("categoryId");
            medicine.setCategoryId(categoryIdObj != null ? Long.valueOf(categoryIdObj.toString()) : null);
        }
        // commonName 处理
        if (medicineDTO.containsKey("commonName")) {
            medicine.setCommonName((String) medicineDTO.get("commonName"));
        }
        // dosage 处理
        if (medicineDTO.containsKey("dosage")) {
            medicine.setDosage((String) medicineDTO.get("dosage"));
        }
        // adverseReactions 处理
        if (medicineDTO.containsKey("adverseReactions")) {
            medicine.setAdverseReactions((String) medicineDTO.get("adverseReactions"));
        }
        // contraindications 处理
        if (medicineDTO.containsKey("contraindications")) {
            medicine.setContraindications((String) medicineDTO.get("contraindications"));
        }
        // precautions 处理
        if (medicineDTO.containsKey("precautions")) {
            medicine.setPrecautions((String) medicineDTO.get("precautions"));
        }
        // riskTips 处理
        if (medicineDTO.containsKey("riskTips")) {
            medicine.setRiskTips((String) medicineDTO.get("riskTips"));
        }

        // 如果药品被拒绝（auditStatus=2），编辑后重置为待审核状态
        if (medicine.getAuditStatus() != null && medicine.getAuditStatus() == 2) {
            medicine.setAuditStatus(0);  // 重置为待审核
            medicine.setAuditRemark(null);  // 清空拒绝原因
            log.info("被拒绝的药品重新提交审核: medicineId={}", medicineId);
        }

        medicineMapper.updateById(medicine);
        log.info("商家更新药品: merchantId={}, medicineId={}", merchantId, medicineId);
    }

    @Override
    @Transactional
    public void deleteMedicine(Long merchantId, Long medicineId) {
        // 根据userId查询商家信息
        MedicinePO medicine = medicineMapper.selectById(medicineId);
        // 判断药品是否存在
        if (medicine == null || !medicine.getMerchantId().equals(merchantId)) {
            throw new BusinessException(ResultCode.MEDICINE_NOT_EXIST);
        }

        // 上架状态的药品不能删除
        if (medicine.getStatus() != null && medicine.getStatus() == 1) {
            throw new BusinessException(ResultCode.FAIL, "请先下架药品后再删除");
        }

        // 逻辑删除
        medicine.setDeleted(1);
        medicineMapper.updateById(medicine);



        log.info("商家删除药品: merchantId={}, medicineId={}", merchantId, medicineId);
    }

    @Override
    @Transactional
    public void updateMedicineStatus(Long merchantId, Long medicineId, Integer status) {
        MedicinePO medicine = medicineMapper.selectById(medicineId);
        if (medicine == null || !medicine.getMerchantId().equals(merchantId)) {
            throw new BusinessException(ResultCode.MEDICINE_NOT_EXIST);
        }

        // 只有审核通过的药品才能上架
        if (status == 1 && (medicine.getAuditStatus() == null || medicine.getAuditStatus() != 1)) {
            throw new BusinessException(ResultCode.FAIL, "药品待平台审核通过后才能上架");
        }

        medicine.setStatus(status);
        medicineMapper.updateById(medicine);
        log.info("商家更新药品状态: merchantId={}, medicineId={}, status={}", merchantId, medicineId, status);
    }

    /**
     * 转换为简单Map（列表使用）
     */
    private Map<String, Object> convertToMap(MedicinePO medicine) {
        Map<String, Object> map = new HashMap<>();
        map.put("id", medicine.getId());
        map.put("name", medicine.getName());
        map.put("image", medicine.getImage());
        map.put("specification", medicine.getSpecification());
        map.put("price", medicine.getPrice());
        map.put("originalPrice", medicine.getOriginalPrice());
        map.put("sales", medicine.getSales());
        map.put("isPrescription", medicine.getIsPrescription());
        map.put("merchantId", medicine.getMerchantId());
        return map;
    }

    /**
     * 转换为详细Map（详情使用）
     */
    private Map<String, Object> convertToDetailMap(MedicinePO medicine) {
        Map<String, Object> map = convertToMap(medicine);
        map.put("commonName", medicine.getCommonName());
        map.put("manufacturer", medicine.getManufacturer());
        map.put("approvalNumber", medicine.getApprovalNumber());
        map.put("stock", medicine.getStock());
        map.put("efficacy", medicine.getEfficacy());
        map.put("dosage", medicine.getDosage());
        map.put("adverseReactions", medicine.getAdverseReactions());
        map.put("contraindications", medicine.getContraindications());
        map.put("precautions", medicine.getPrecautions());
        map.put("riskTips", medicine.getRiskTips());
        map.put("images", medicine.getImages());
        map.put("categoryId", medicine.getCategoryId());
        return map;
    }
}
