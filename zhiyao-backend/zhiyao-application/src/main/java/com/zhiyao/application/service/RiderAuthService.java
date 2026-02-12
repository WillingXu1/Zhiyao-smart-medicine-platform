package com.zhiyao.application.service;

import com.zhiyao.application.dto.LoginDTO;
import com.zhiyao.application.dto.RiderRegisterDTO;
import com.zhiyao.common.result.Result;

/**
 * 骑手认证服务接口
 */
public interface RiderAuthService {

    /**
     * 骑手登录
     */
    Result<?> login(LoginDTO loginDTO);

    /**
     * 骑手注册
     */
    Result<?> register(RiderRegisterDTO registerDTO);
}
