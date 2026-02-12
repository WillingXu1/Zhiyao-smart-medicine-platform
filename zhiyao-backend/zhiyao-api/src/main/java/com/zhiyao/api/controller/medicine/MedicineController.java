package com.zhiyao.api.controller.medicine;

import com.zhiyao.application.service.MedicineService;
import com.zhiyao.common.result.Result;
import com.zhiyao.common.result.PageResult;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

/**
 * 药品接口
 */
@Tag(name = "药品管理", description = "药品搜索、详情、分类相关接口")
@RestController
@RequestMapping("/medicines")
@RequiredArgsConstructor
public class MedicineController {

    private final MedicineService medicineService;

    @Operation(summary = "药品搜索", description = "根据关键词搜索药品")
    @GetMapping
    public Result<PageResult<Map<String, Object>>> searchMedicines(
            @Parameter(description = "搜索关键词") @RequestParam(value = "keyword", required = false) String keyword,
            @Parameter(description = "分类ID") @RequestParam(value = "categoryId", required = false) Long categoryId,
            @Parameter(description = "商家ID") @RequestParam(value = "merchantId", required = false) Long merchantId,
            @Parameter(description = "是否处方药：0-非处方 1-处方") @RequestParam(value = "isPrescription", required = false) Integer isPrescription,
            @Parameter(description = "排序字段：price-价格 sales-销量") @RequestParam(value = "sortBy", defaultValue = "sales") String sortBy,
            @Parameter(description = "排序方式：asc-升序 desc-降序") @RequestParam(value = "sortOrder", defaultValue = "desc") String sortOrder,
            @Parameter(description = "页码") @RequestParam(value = "pageNum", defaultValue = "1") Integer pageNum,
            @Parameter(description = "每页条数") @RequestParam(value = "pageSize", defaultValue = "10") Integer pageSize) {
        PageResult<Map<String, Object>> result = medicineService.searchMedicines(
                keyword, categoryId, merchantId, isPrescription, sortBy, sortOrder, pageNum, pageSize);
        return Result.success(result);
    }

    @Operation(summary = "获取药品详情", description = "根据药品ID获取详细信息")
    @GetMapping("/{id}")
    public Result<Map<String, Object>> getMedicineDetail(
            @Parameter(description = "药品ID") @PathVariable("id") Long id) {
        Map<String, Object> detail = medicineService.getMedicineDetail(id);
        return Result.success(detail);
    }

    @Operation(summary = "获取药品分类", description = "获取所有药品分类列表")
    @GetMapping("/categories")
    public Result<List<Map<String, Object>>> getCategories() {
        List<Map<String, Object>> categories = medicineService.getCategories();
        return Result.success(categories);
    }

    @Operation(summary = "获取热销药品", description = "获取热销药品列表")
    @GetMapping("/hot")
    public Result<List<Map<String, Object>>> getHotMedicines(
            @Parameter(description = "数量限制") @RequestParam(value = "limit", defaultValue = "10") Integer limit) {
        List<Map<String, Object>> hotMedicines = medicineService.getHotMedicines(limit);
        return Result.success(hotMedicines);
    }

    @Operation(summary = "根据分类获取药品", description = "获取指定分类下的药品列表")
    @GetMapping("/category/{categoryId}")
    public Result<PageResult<Map<String, Object>>> getMedicinesByCategory(
            @Parameter(description = "分类ID") @PathVariable("categoryId") Long categoryId,
            @Parameter(description = "页码") @RequestParam(value = "pageNum", defaultValue = "1") Integer pageNum,
            @Parameter(description = "每页条数") @RequestParam(value = "pageSize", defaultValue = "10") Integer pageSize) {
        PageResult<Map<String, Object>> result = medicineService.getMedicinesByCategory(categoryId, pageNum, pageSize);
        return Result.success(result);
    }
}
