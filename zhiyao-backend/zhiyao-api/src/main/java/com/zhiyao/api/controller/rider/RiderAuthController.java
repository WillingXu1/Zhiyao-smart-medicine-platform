package com.zhiyao.api.controller.rider;

import com.zhiyao.application.dto.LoginDTO;
import com.zhiyao.application.dto.RiderRegisterDTO;
import com.zhiyao.application.service.RiderAuthService;
import com.zhiyao.common.result.Result;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

/**
 * 骑手认证接口
 */
@Tag(name = "骑手认证", description = "骑手登录注册相关接口")
@RestController
@RequestMapping("/rider/auth")
@RequiredArgsConstructor
public class RiderAuthController {

    private final RiderAuthService riderAuthService;

    @Operation(summary = "骑手登录", description = "骑手账号密码登录")
    @PostMapping("/login")
    public Result<?> login(@RequestBody LoginDTO loginDTO) {
        return riderAuthService.login(loginDTO);
    }

    @Operation(summary = "骑手注册", description = "骑手入驻申请")
    @PostMapping("/register")
    public Result<?> register(@RequestBody RiderRegisterDTO registerDTO) {
        return riderAuthService.register(registerDTO);
    }
}
