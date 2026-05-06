/**
 * API 模块：菜单管理
 */

import request from '@/utils/request'

export const getMenuTree = () => request.get('/system/menu/tree/')
export const getMenuList = (params) => request.get('/system/menu/list/', { params })
export const createMenu = (data) => request.post('/system/menu/', data)
export const updateMenu = (id, data) => request.put(`/system/menu/${id}/`, data)
export const deleteMenu = (id) => request.delete(`/system/menu/${id}/`)
