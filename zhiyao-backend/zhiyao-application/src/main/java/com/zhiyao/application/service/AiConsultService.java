package com.zhiyao.application.service;

import com.zhiyao.common.result.Result;
import java.util.List;
import java.util.Map;

/**
 * AI用药咨询服务接口
 */
public interface AiConsultService {

    /**
     * 发送消息给AI并获取回复
     * @param message 用户消息
     * @param history 对话历史
     * @return AI回复
     */
    Result<?> chat(String message, List<Map<String, String>> history);
}
