package com.zhiyao.api.controller.user;

import com.zhiyao.application.service.AiConsultService;
import com.zhiyao.application.service.impl.AiConsultServiceImpl;
import com.zhiyao.common.result.Result;
import com.zhiyao.api.util.SecurityUtils;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * AI用药咨询控制器
 */
@Slf4j
@RestController
@RequestMapping("/consult")
@RequiredArgsConstructor
@Tag(name = "AI用药咨询", description = "AI智能用药咨询接口")
public class ConsultController {

    private final AiConsultService aiConsultService;
    private final AiConsultServiceImpl aiConsultServiceImpl;

    @Operation(summary = "发送咨询消息", description = "发送消息给AI助手并获取回复")
    @PostMapping("/chat")
    public Result<?> chat(@RequestBody Map<String, Object> request) {
        String message = (String) request.get("message");
        String sessionId = (String) request.get("sessionId");
        List<Map<String, String>> history = (List<Map<String, String>>) request.get("history");
        
        if (message == null || message.trim().isEmpty()) {
            return Result.fail("消息内容不能为空");
        }
        
        // 生成会话ID（如果没有）
        if (sessionId == null || sessionId.isEmpty()) {
            sessionId = UUID.randomUUID().toString().replace("-", "");
        }
        
        // 获取当前用户ID（可能未登录）
        Long userId = null;
        try {
            userId = SecurityUtils.getCurrentUserId();
        } catch (Exception e) {
            // 未登录用户也可以使用咨询功能
        }
        
        // 保存用户消息
        if (userId != null) {
            aiConsultServiceImpl.saveConsultation(userId, sessionId, "user", message, 1);
        }
        
        // 调用AI服务
        Result<?> result = aiConsultService.chat(message, history);
        
        // 保存AI回复
        if (result.getCode() == 200 && userId != null) {
            Map<String, Object> data = (Map<String, Object>) result.getData();
            String reply = (String) data.get("reply");
            aiConsultServiceImpl.saveConsultation(userId, sessionId, "assistant", reply, 1);
            data.put("sessionId", sessionId);
        }
        
        return result;
    }

    @Operation(summary = "获取对话历史", description = "获取指定会话的对话历史")
    @GetMapping("/history/{sessionId}")
    public Result<?> getHistory(@PathVariable String sessionId) {
        List<Map<String, String>> history = aiConsultServiceImpl.getSessionHistory(sessionId);
        return Result.success(history);
    }

    @Operation(summary = "新建会话", description = "创建一个新的咨询会话")
    @PostMapping("/session/new")
    public Result<?> newSession() {
        String sessionId = UUID.randomUUID().toString().replace("-", "");
        return Result.success(Map.of("sessionId", sessionId));
    }

    @Operation(summary = "获取用户最近对话", description = "获取当前登录用户的最近一次对话历史")
    @GetMapping("/user/latest")
    public Result<?> getUserLatestSession() {
        try {
            Long userId = SecurityUtils.getCurrentUserId();
            if (userId == null) {
                return Result.success(Map.of("sessionId", "", "messages", List.of()));
            }
            Map<String, Object> data = aiConsultServiceImpl.getUserLatestSession(userId);
            return Result.success(data);
        } catch (Exception e) {
            // 未登录用户返回空历史
            return Result.success(Map.of("sessionId", "", "messages", List.of()));
        }
    }
}
