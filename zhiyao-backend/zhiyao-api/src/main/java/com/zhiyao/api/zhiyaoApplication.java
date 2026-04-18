package com.zhiyao.api;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.ConfigurationPropertiesScan;
import org.springframework.context.annotation.ComponentScan;

/**
 * 智健优选启动类
 */
@SpringBootApplication
@ComponentScan(basePackages = "com.zhiyao")
@MapperScan("com.zhiyao.infrastructure.persistence.mapper")
@ConfigurationPropertiesScan(basePackages = "com.zhiyao")
public class zhiyaoApplication {

    public static void main(String[] args) {
        SpringApplication.run(zhiyaoApplication.class, args);
        System.out.println("========================================");
        System.out.println("    知药（健康人生医药优选） - 后端服务启动成功！");
        System.out.println("    API文档: http://localhost:8080/doc.html");
        System.out.println("========================================");
    }
}
