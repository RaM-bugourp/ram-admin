/**
 * API 模块：用户认证
 *
 * 所有 API 调用都集中在这里，方便管理和维护。
 */

import request from '@/utils/request'

export const login = (data) => request.post('/auth/login/', data)
export const logout = () => request.post('/auth/logout/')
export const getUserInfo = () => request.get('/auth/user_info/')
