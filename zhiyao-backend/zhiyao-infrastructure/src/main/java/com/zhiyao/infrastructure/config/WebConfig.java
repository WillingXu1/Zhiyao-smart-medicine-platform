package com.zhiyao.infrastructure.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.web.client.RestTemplate;

/**
 * Web配置类
 */
@Configuration
public class WebConfig {

    @Bean
    public RestTemplate restTemplate() {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(10000);  // 连接超时10秒
        factory.setReadTimeout(60000);     // 读取超时60秒（AI响应可能较慢）
        return new RestTemplate(factory);
    }
}
