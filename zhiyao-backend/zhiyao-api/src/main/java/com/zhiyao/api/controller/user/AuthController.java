package com.zhiyao.api.controller.user;

import com.zhiyao.application.dto.LoginVO;
import com.zhiyao.application.dto.UserLoginDTO;
import com.zhiyao.application.dto.UserRegisterDTO;
import com.zhiyao.application.service.UserService;
import com.zhiyao.common.result.Result;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

/**
 * 用户认证接口
 */
@Tag(name = "用户认证", description = "用户注册、登录相关接口")
@RestController
@RequestMapping("/auth")
@RequiredArgsConstructor
public class AuthController {

    private final UserService userService;

    @Operation(summary = "用户注册", description = "普通用户注册账号")
    @PostMapping("/register")
    public Result<Long> register(@Valid @RequestBody UserRegisterDTO dto) {
        Long userId = userService.register(dto);
        return Result.success("注册成功", userId);
    }

    @Operation(summary = "用户登录", description = "普通用户登录")
    @PostMapping("/login")
    public Result<LoginVO> login(@Valid @RequestBody UserLoginDTO dto) {
        LoginVO loginVO = userService.login(dto);
        return Result.success(loginVO);
    }

    @Operation(summary = "商家登录", description = "商家端登录")
    @PostMapping("/merchant/login")
    public Result<LoginVO> merchantLogin(@Valid @RequestBody UserLoginDTO dto) {
        LoginVO loginVO = userService.merchantLogin(dto);
        return Result.success(loginVO);
    }

    @Operation(summary = "管理员登录", description = "管理端登录")
    @PostMapping("/admin/login")
    public Result<LoginVO> adminLogin(@Valid @RequestBody UserLoginDTO dto) {
        LoginVO loginVO = userService.adminLogin(dto);
        return Result.success(loginVO);
    }

    @Operation(summary = "骑手登录", description = "骑手端登录")
    @PostMapping("/rider/login")
    public Result<LoginVO> riderLogin(@Valid @RequestBody UserLoginDTO dto) {
        LoginVO loginVO = userService.riderLogin(dto);
        return Result.success(loginVO);
    }
}
