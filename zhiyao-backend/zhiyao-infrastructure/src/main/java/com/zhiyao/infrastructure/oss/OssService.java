package com.zhiyao.infrastructure.oss;

import com.aliyun.oss.OSS;
import com.aliyun.oss.model.ObjectMetadata;
import com.aliyun.oss.model.PutObjectRequest;
import com.zhiyao.infrastructure.config.OssConfig;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.io.InputStream;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.UUID;

/**
 * 阿里云OSS服务
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class OssService {
    
    private final OSS ossClient;
    private final OssConfig ossConfig;
    
    /**
     * 上传文件
     * @param file 文件
     * @param folder 文件夹(如: images/avatar)
     * @return 文件访问URL
     */
    public String uploadFile(MultipartFile file, String folder) {
        if (file == null || file.isEmpty()) {
            throw new IllegalArgumentException("上传文件不能为空");
        }
        
        try {
            // 生成唯一文件名
            String originalFilename = file.getOriginalFilename();
            String extension = "";
            if (originalFilename != null && originalFilename.contains(".")) {
                extension = originalFilename.substring(originalFilename.lastIndexOf("."));
            }
            
            // 按日期分目录存储
            String dateFolder = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy/MM/dd"));
            String fileName = folder + "/" + dateFolder + "/" + UUID.randomUUID().toString().replace("-", "") + extension;
            
            // 设置元数据
            ObjectMetadata metadata = new ObjectMetadata();
            metadata.setContentLength(file.getSize());
            metadata.setContentType(file.getContentType());
            
            // 上传文件
            InputStream inputStream = file.getInputStream();
            PutObjectRequest putObjectRequest = new PutObjectRequest(
                    ossConfig.getBucketName(), 
                    fileName, 
                    inputStream, 
                    metadata
            );
            ossClient.putObject(putObjectRequest);
            
            // 返回访问URL
            String url = "https://" + ossConfig.getBucketName() + "." + ossConfig.getEndpoint() + "/" + fileName;
            log.info("文件上传成功: {}", url);
            return url;
            
        } catch (IOException e) {
            log.error("文件上传失败", e);
            throw new RuntimeException("文件上传失败: " + e.getMessage());
        }
    }
    
    /**
     * 上传图片
     */
    public String uploadImage(MultipartFile file) {
        return uploadFile(file, "images");
    }
    
    /**
     * 上传头像
     */
    public String uploadAvatar(MultipartFile file) {
        return uploadFile(file, "images/avatar");
    }
    
    /**
     * 上传商品图片
     */
    public String uploadProductImage(MultipartFile file) {
        return uploadFile(file, "images/product");
    }
    
    /**
     * 上传商家图片
     */
    public String uploadMerchantImage(MultipartFile file) {
        return uploadFile(file, "images/merchant");
    }
    
    /**
     * 删除文件
     * @param fileUrl 文件URL
     */
    public void deleteFile(String fileUrl) {
        if (fileUrl == null || fileUrl.isEmpty()) {
            return;
        }
        
        try {
            // 从URL中提取文件名
            String prefix = "https://" + ossConfig.getBucketName() + "." + ossConfig.getEndpoint() + "/";
            if (fileUrl.startsWith(prefix)) {
                String fileName = fileUrl.substring(prefix.length());
                ossClient.deleteObject(ossConfig.getBucketName(), fileName);
                log.info("文件删除成功: {}", fileUrl);
            }
        } catch (Exception e) {
            log.error("文件删除失败: {}", fileUrl, e);
        }
    }
}
