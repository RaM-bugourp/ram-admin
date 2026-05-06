/**
 * API 模块：文章管理
 */

import request from '@/utils/request'

export const getArticleList = (params) => request.get('/articles/', { params })
export const getArticleDetail = (id) => request.get(`/articles/${id}/`)
export const createArticle = (data) => request.post('/articles/', data)
export const updateArticle = (id, data) => request.put(`/articles/${id}/`, data)
export const deleteArticle = (id) => request.delete(`/articles/${id}/`)
export const publishArticle = (id) => request.post(`/articles/${id}/publish/`)
export const archiveArticle = (id) => request.post(`/articles/${id}/archive/`)
export const getArticleStatistics = () => request.get('/articles/statistics/')

export const getCategoryList = (params) => request.get('/categories/', { params })
export const createCategory = (data) => request.post('/categories/', data)
export const updateCategory = (id, data) => request.put(`/categories/${id}/`, data)
export const deleteCategory = (id) => request.delete(`/categories/${id}/`)
