package com.zhiyao.api.controller;

import com.zhiyao.common.result.Result;
import com.zhiyao.infrastructure.oss.OssService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 文件上传控制器
 */
@Tag(name = "文件上传", description = "文件上传相关接口")
@RestController
@RequestMapping("/upload")
@RequiredArgsConstructor
public class FileUploadController {
    
    private final OssService ossService;
    
    @Operation(summary = "上传单个图片")
    @PostMapping("/image")
    public Result<Map<String, String>> uploadImage(@RequestParam("file") MultipartFile file) {
        String url = ossService.uploadImage(file);
        Map<String, String> result = new HashMap<>();
        result.put("url", url);
        return Result.success(result);
    }
    
    @Operation(summary = "上传头像")
    @PostMapping("/avatar")
    public Result<Map<String, String>> uploadAvatar(@RequestParam("file") MultipartFile file) {
        String url = ossService.uploadAvatar(file);
        Map<String, String> result = new HashMap<>();
        result.put("url", url);
        return Result.success(result);
    }
    
    @Operation(summary = "上传商品图片")
    @PostMapping("/product")
    public Result<Map<String, String>> uploadProductImage(@RequestParam("file") MultipartFile file) {
        String url = ossService.uploadProductImage(file);
        Map<String, String> result = new HashMap<>();
        result.put("url", url);
        return Result.success(result);
    }
    
    @Operation(summary = "上传商家图片")
    @PostMapping("/merchant")
    public Result<Map<String, String>> uploadMerchantImage(@RequestParam("file") MultipartFile file) {
        String url = ossService.uploadMerchantImage(file);
        Map<String, String> result = new HashMap<>();
        result.put("url", url);
        return Result.success(result);
    }
    
    @Operation(summary = "批量上传图片")
    @PostMapping("/images")
    public Result<Map<String, List<String>>> uploadImages(@RequestParam("files") MultipartFile[] files) {
        List<String> urls = new ArrayList<>();
        for (MultipartFile file : files) {
            String url = ossService.uploadImage(file);
            urls.add(url);
        }
        Map<String, List<String>> result = new HashMap<>();
        result.put("urls", urls);
        return Result.success(result);
    }
    
    @Operation(summary = "删除文件")
    @DeleteMapping
    public Result<Void> deleteFile(@RequestParam("url") String url) {
        ossService.deleteFile(url);
        return Result.success(null);
    }
}
