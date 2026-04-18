package com.zhiyao.api.controller.merchant;

import com.zhiyao.application.dto.LoginDTO;
import com.zhiyao.application.dto.MerchantRegisterDTO;
import com.zhiyao.application.service.MerchantAuthService;
import com.zhiyao.common.result.Result;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

/**
 * 商家认证接口
 */
@Tag(name = "商家认证", description = "商家登录注册相关接口")
@RestController
@RequestMapping("/merchant/auth")
@RequiredArgsConstructor
public class MerchantAuthController {

    private final MerchantAuthService merchantAuthService;

    @Operation(summary = "商家登录", description = "商家账号密码登录")
    @PostMapping("/login")
    public Result<?> login(@RequestBody LoginDTO loginDTO) {
        return merchantAuthService.login(loginDTO);
    }

    @Operation(summary = "商家注册", description = "商家入驻申请")
    @PostMapping("/register")
    public Result<?> register(@RequestBody MerchantRegisterDTO registerDTO) {
        return merchantAuthService.register(registerDTO);
    }
}
