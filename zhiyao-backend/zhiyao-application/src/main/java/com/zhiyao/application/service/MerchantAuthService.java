package com.zhiyao.application.service;

import com.zhiyao.application.dto.LoginDTO;
import com.zhiyao.application.dto.MerchantRegisterDTO;
import com.zhiyao.common.result.Result;

/**
 * 商家认证服务接口
 */
public interface MerchantAuthService {

    /**
     * 商家登录
     */
    Result<?> login(LoginDTO loginDTO);

    /**
     * 商家注册
     */
    Result<?> register(MerchantRegisterDTO registerDTO);
}
