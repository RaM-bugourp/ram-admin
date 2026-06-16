"""Tests for BusinessError and custom exception handler."""
import pytest
from rest_framework import status
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from apps.common.exceptions import BusinessError, custom_exception_handler
from rest_framework.exceptions import NotFound


def make_view():
    """Create a simple view for testing exception handler."""
    view = APIView.as_view(
        permission_classes=[AllowAny],
    )
    return view


def test_business_error_constructs_correctly():
    """BusinessError 包含 message / code / status。"""
    err = BusinessError(message='用户名已存在', code='DUPLICATE_USERNAME', status=409)
    assert err.message == '用户名已存在'
    assert err.code == 'DUPLICATE_USERNAME'
    assert err.status == 409


def test_business_error_defaults():
    """BusinessError 使用默认值。"""
    err = BusinessError(message='出错了')
    assert err.code == 'BUSINESS_ERROR'
    assert err.status == 400


def test_exception_handler_business_error():
    """BusinessError → {error: {code, message}}。"""
    err = BusinessError(message='用户不存在', code='NOT_FOUND', status=404)
    factory = APIRequestFactory()
    request = factory.get('/')

    response = custom_exception_handler(err, {'view': None, 'request': request})
    assert response is not None
    assert response.status_code == 404
    assert response.data == {'error': {'code': 'NOT_FOUND', 'message': '用户不存在'}}


def test_exception_handler_business_error_default_status():
    """BusinessError 默认 status=400。"""
    err = BusinessError(message='参数错误', code='INVALID_PARAM')
    factory = APIRequestFactory()
    request = factory.get('/')

    response = custom_exception_handler(err, {'view': None, 'request': request})
    assert response is not None
    assert response.status_code == 400
    assert response.data == {'error': {'code': 'INVALID_PARAM', 'message': '参数错误'}}


def test_exception_handler_drf_error():
    """DRF 异常被正确包裹。"""
    err = NotFound(detail='资源不存在')
    factory = APIRequestFactory()
    request = factory.get('/')

    response = custom_exception_handler(err, {'view': None, 'request': request})
    assert response is not None
    assert response.status_code == 404
    assert 'error' in response.data
    assert response.data['error']['code'] == 'VALIDATION_ERROR'


def test_exception_handler_unknown_error():
    """未知异常返回 None（DRF 默认处理）。"""
    err = ValueError('something broke')
    factory = APIRequestFactory()
    request = factory.get('/')

    response = custom_exception_handler(err, {'view': None, 'request': request})
    assert response is None
