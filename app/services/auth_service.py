# -*- coding: utf-8 -*-
"""
LeanCloud身份验证服务
用于验证App端发送的 X-LC-UID 和 X-LC-Session
"""
import os
import httpx
import yaml
import logging
from typing import Optional, Tuple
from functools import lru_cache

logger = logging.getLogger(__name__)

# 加载配置
config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config.yaml')


@lru_cache(maxsize=1)
def get_leancloud_config() -> dict:
    """获取LeanCloud配置（带缓存）"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config.get('LeanCloud', {})
    except Exception as e:
        logger.error(f"读取LeanCloud配置失败: {e}")
        return {}


class AuthService:
    """身份验证服务类"""
    
    # 缓存验证结果（简单的内存缓存，生产环境建议用Redis）
    _session_cache: dict = {}
    
    @staticmethod
    def is_auth_enabled() -> bool:
        """检查是否启用身份验证"""
        config = get_leancloud_config()
        return config.get('Enable_Auth', True)
    
    @staticmethod
    async def verify_session(lc_uid: str, lc_session: str) -> Tuple[bool, Optional[str]]:
        """
        验证LeanCloud Session Token
        
        Args:
            lc_uid: LeanCloud用户objectId
            lc_session: LeanCloud sessionToken
            
        Returns:
            (是否验证通过, 错误信息)
        """
        # 检查是否启用验证
        if not AuthService.is_auth_enabled():
            logger.debug("身份验证已禁用，跳过验证")
            return True, None
        
        # 检查参数
        if not lc_uid or not lc_session:
            return False, "缺少身份验证信息"
        
        # 检查缓存（避免频繁调用LeanCloud API）
        cache_key = f"{lc_uid}:{lc_session[:16]}"  # 只用session前16位作为缓存key
        if cache_key in AuthService._session_cache:
            cached = AuthService._session_cache[cache_key]
            return cached['valid'], cached.get('error')
        
        # 获取配置
        config = get_leancloud_config()
        app_id = config.get('App_ID', '')
        app_key = config.get('App_Key', '')
        api_server = config.get('API_Server', '')
        
        # 检查配置是否完整
        if not all([app_id, app_key, api_server]) or 'your_' in app_id:
            logger.warning("LeanCloud配置不完整，跳过验证")
            return True, None  # 配置不完整时默认通过（便于测试）
        
        try:
            # 调用LeanCloud API验证sessionToken
            headers = {
                "X-LC-Id": app_id,
                "X-LC-Key": app_key,
                "X-LC-Session": lc_session,
                "Content-Type": "application/json"
            }
            
            url = f"{api_server.rstrip('/')}/1.1/users/me"
            
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url, headers=headers)
                
                if resp.status_code == 200:
                    user_data = resp.json()
                    # 验证返回的objectId是否与传入的lc_uid一致
                    if user_data.get('objectId') == lc_uid:
                        # 缓存成功结果
                        AuthService._session_cache[cache_key] = {'valid': True}
                        logger.debug(f"用户验证成功: {lc_uid}")
                        return True, None
                    else:
                        error = "用户ID不匹配"
                        AuthService._session_cache[cache_key] = {'valid': False, 'error': error}
                        return False, error
                elif resp.status_code == 401:
                    error = "Session已过期或无效"
                    AuthService._session_cache[cache_key] = {'valid': False, 'error': error}
                    return False, error
                else:
                    error = f"验证请求失败: {resp.status_code}"
                    logger.error(f"LeanCloud验证失败: {resp.status_code}, {resp.text}")
                    return False, error
                    
        except httpx.TimeoutException:
            logger.error("LeanCloud验证超时")
            return False, "验证服务超时"
        except Exception as e:
            logger.error(f"LeanCloud验证异常: {e}")
            return False, f"验证服务异常: {str(e)}"
    
    @staticmethod
    def clear_cache():
        """清除验证缓存"""
        AuthService._session_cache.clear()
        logger.info("身份验证缓存已清除")

