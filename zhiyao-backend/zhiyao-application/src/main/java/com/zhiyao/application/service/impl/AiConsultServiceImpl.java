package com.zhiyao.application.service.impl;

import com.zhiyao.application.service.AiConsultService;
import com.zhiyao.common.result.Result;
import com.zhiyao.infrastructure.persistence.mapper.ConsultationMapper;
import com.zhiyao.infrastructure.persistence.po.ConsultationPO;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.*;

/**
 * AI用药咨询服务实现类
 * 负责处理用户用药咨询，调用DeepSeek API进行智能对话
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class AiConsultServiceImpl implements AiConsultService {

    /** 咨询记录数据访问对象 */
    private final ConsultationMapper consultationMapper;

    /** HTTP请求模板 */
    private final RestTemplate restTemplate;

    /** DeepSeek API密钥 */
    @Value("${ai.deepseek.api-key:sk-a56903ddc505472a8a2c615250254bdc}")
    private String apiKey;

    /** DeepSeek API基础URL */
    @Value("${ai.deepseek.base-url:https://api.deepseek.com}")
    private String baseUrl;

    /** DeepSeek模型名称 */
    @Value("${ai.deepseek.model:deepseek-chat}")
    private String model;

    // 系统提示词：定义AI的角色和行为
    private static final String SYSTEM_PROMPT = """
        你是"智健优选"医药平台的专业用药咨询助手，名字叫"小智"。你的职责是：
        
        1. **用药咨询**：回答用户关于药品用法、用量、注意事项等问题
        2. **症状分析**：根据用户描述的症状，提供可能的用药建议（仅供参考）
        3. **药品查询**：帮助用户了解药品的功效、禁忌、不良反应等信息
        4. **健康建议**：提供一般性的健康和用药安全建议
        
        **重要原则**：
        - 始终提醒用户：AI建议仅供参考，具体用药请遵医嘱
        - 对于处方药，强调必须在医生指导下使用
        - 遇到紧急情况（如严重过敏、中毒等），建议用户立即就医
        - 不提供诊断，只提供用药相关的咨询服务
        - 回答要专业、准确、易懂，适当使用emoji让对话更亲切
        - 回答要简洁明了，避免过长的段落
        
        请用贴吧老哥的语气恢复回答。
        """;

    /**
     * AI对话聊天接口
     * @param message 用户当前消息
     * @param history 历史对话记录，格式为List<Map<String, String>>，每个Map包含role和content
     * @return Result对象，包含AI回复和相关数据
     */
    @Override
    public Result<?> chat(String message, List<Map<String, String>> history) {
        try {
            // 构建消息列表
            List<Map<String, String>> messages = new ArrayList<>();

            // 添加系统提示消息
            Map<String, String> systemMessage = new HashMap<>();
            systemMessage.put("role", "system");
            systemMessage.put("content", SYSTEM_PROMPT);
            messages.add(systemMessage);

            // 添加历史对话（最多保留最近10轮，即20条消息）
            if (history != null && !history.isEmpty()) {
                // 计算起始位置，确保最多保留最近20条历史消息
                int start = Math.max(0, history.size() - 20);
                for (int i = start; i < history.size(); i++) {
                    messages.add(history.get(i));
                }
            }

            // 添加当前用户消息
            Map<String, String> userMessage = new HashMap<>();
            userMessage.put("role", "user");
            userMessage.put("content", message);
            messages.add(userMessage);

            // 调用DeepSeek API获取AI回复
            String aiResponse = callDeepSeekApi(messages);

            // 构建返回结果
            Map<String, Object> result = new HashMap<>();
            result.put("reply", aiResponse); // AI回复内容
            result.put("timestamp", System.currentTimeMillis()); // 回复时间戳

            return Result.success(result);

        } catch (Exception e) {
            log.error("AI咨询失败", e);
            return Result.fail("抱歉，AI助手暂时无法回复，请稍后再试");
        }
    }

    /**
     * 保存单条对话记录到数据库
     * @param userId 用户ID
     * @param sessionId 会话ID
     * @param role 角色（user/assistant）
     * @param content 消息内容
     * @param consultType 咨询类型（默认为1）
     */
    public void saveConsultation(Long userId, String sessionId, String role, String content, Integer consultType) {
        try {
            ConsultationPO consultation = new ConsultationPO();
            consultation.setUserId(userId);
            consultation.setSessionId(sessionId);
            consultation.setRole(role);
            consultation.setContent(content);
            // 如果咨询类型为空，使用默认值1
            consultation.setConsultType(consultType != null ? consultType : 1);
            consultation.setDeleted(0); // 未删除状态
            consultationMapper.insert(consultation);
        } catch (Exception e) {
            log.error("保存咨询记录失败", e);
        }
    }

    /**
     * 根据会话ID获取历史对话记录
     * @param sessionId 会话ID
     * @return 历史对话列表，每个元素包含role和content
     */
    public List<Map<String, String>> getSessionHistory(String sessionId) {
        // 从数据库查询指定会话的所有记录
        List<ConsultationPO> records = consultationMapper.selectBySessionId(sessionId);
        List<Map<String, String>> history = new ArrayList<>();
        for (ConsultationPO record : records) {
            Map<String, String> msg = new HashMap<>();
            msg.put("role", record.getRole());
            msg.put("content", record.getContent());
            history.add(msg);
        }
        return history;
    }

    /**
     * 获取指定用户最近的对话会话信息
     * @param userId 用户ID
     * @return Map包含sessionId和messages（最新会话的消息列表）
     */
    public Map<String, Object> getUserLatestSession(Long userId) {
        Map<String, Object> result = new HashMap<>();
        try {
            // 查询用户最近的一次会话记录
            List<ConsultationPO> records = consultationMapper.selectLatestSessionByUserId(userId);
            if (records == null || records.isEmpty()) {
                // 用户没有历史会话记录
                result.put("sessionId", null);
                result.put("messages", new ArrayList<>());
                return result;
            }

            // 从第一条记录获取会话ID（同一会话的记录有相同的sessionId）
            String sessionId = records.get(0).getSessionId();
            result.put("sessionId", sessionId);

            // 转换数据库记录为消息格式
            List<Map<String, String>> messages = new ArrayList<>();
            for (ConsultationPO record : records) {
                Map<String, String> msg = new HashMap<>();
                msg.put("role", record.getRole());
                msg.put("content", record.getContent());
                messages.add(msg);
            }
            result.put("messages", messages);

        } catch (Exception e) {
            log.error("获取用户对话历史失败", e);
            result.put("sessionId", null);
            result.put("messages", new ArrayList<>());
        }
        return result;
    }

    /**
     * 调用DeepSeek API进行对话
     * @param messages 完整消息列表，包含系统提示、历史对话和当前用户消息
     * @return AI回复的文本内容
     * @throws RuntimeException 当API调用失败时抛出异常
     */
    private String callDeepSeekApi(List<Map<String, String>> messages) {
        // 构建完整的API URL
        String url = baseUrl + "/chat/completions";

        // 构建请求头
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON); // 设置JSON格式
        headers.setBearerAuth(apiKey); // 设置Bearer Token认证

        // 构建请求体参数
        Map<String, Object> requestBody = new HashMap<>();
        requestBody.put("model", model); // 使用的模型
        requestBody.put("messages", messages); // 消息列表
        requestBody.put("temperature", 0.7); // 生成温度，控制随机性
        requestBody.put("max_tokens", 1024); // 最大生成token数
        requestBody.put("stream", false); // 非流式响应

        // 创建HTTP实体
        HttpEntity<Map<String, Object>> entity = new HttpEntity<>(requestBody, headers);

        try {
            // 发送POST请求到DeepSeek API
            ResponseEntity<Map> response = restTemplate.exchange(
                    url,
                    HttpMethod.POST,
                    entity,
                    Map.class
            );

            // 处理成功响应
            if (response.getStatusCode() == HttpStatus.OK && response.getBody() != null) {
                Map body = response.getBody();
                List<Map> choices = (List<Map>) body.get("choices");
                if (choices != null && !choices.isEmpty()) {
                    Map choice = choices.get(0);
                    Map message = (Map) choice.get("message");
                    if (message != null) {
                        // 提取并返回AI的回复内容
                        return (String) message.get("content");
                    }
                }
            }

            // API调用成功但未获取到有效回复
            return "抱歉，我暂时无法回复，请稍后再试 😅";

        } catch (Exception e) {
            log.error("调用DeepSeek API失败: {}", e.getMessage());
            throw new RuntimeException("AI服务调用失败", e);
        }
    }
}