"""
操作日志中间件
══════════════════════════════════════════════════════════════════

面试要点：

Q: Django 中间件的执行顺序？
A: 
    请求进来：M1.process_request → M2.process_request → ... → View
    响应回去：M1.process_response ← M2.process_response ← ... ← View

Q: 中间件能获取到用户信息吗？
A: 能。AuthenticationMiddleware 在操作日志中间件之前执行，
   所以 request.user 已经填充好了。

Q: process_response 里的 response.data 能拿到吗？
A: 能。DRF 的 Response 会在 render() 后才有 data 属性。
   但 process_response 阶段 response.status_code 已经可用。

══════════════════════════════════════════════════════════════════

工作原理：
    1. process_request：检查是否需要记录，准备请求数据
    2. process_response：请求完成后，记录日志
    3. 日志记录是异步的（不阻塞主请求）
"""

import json
import logging
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class OperationLogMiddleware(MiddlewareMixin):
    """
    操作日志中间件 —— 无感记录所有 API 操作。

    工作流程：
        请求进来 → 检查是否记录 → 存入 request._operation_log
        响应回去 → 从 request._operation_log 取出 → 创建 OperationLog

    排除规则：
        —— 非 /api/ 开头的请求不记录（静态文件等）
        —— 登录/登出/菜单获取等高频接口不记录
        —— 只记录 POST/PUT/PATCH/DELETE（GET 列表默认不记）
    """

    # 不记录的路径（高频/敏感接口）
    EXCLUDE_PATHS = frozenset([
        '/api/rbac/auth/login/',
        '/api/rbac/auth/logout/',
        '/api/rbac/auth/user-info/',
        '/api/rbac/system/menu/tree/',
        '/api/rbac/system/metrics/',
        '/api/rbac/system/organization/tree/',
    ])

    # HTTP 方法 → 操作类型
    METHOD_TO_ACTION = {
        'GET': 'LIST',       # 注意：中间件里 list 的判断在后面单独处理
        'POST': 'CREATE',
        'PUT': 'UPDATE',
        'PATCH': 'UPDATE',
        'DELETE': 'DELETE',
    }

    def process_request(self, request):
        """
        请求进来时：决定是否记录，准备数据。

        不返回任何值（返回 None 继续处理流程）。
        如果返回 HttpResponse，会直接跳到 process_response。
        """
        # 1. 只记录 API 请求
        if not request.path.startswith('/api/'):
            return None

        # 2. 排除白名单路径
        if any(request.path.startswith(p) for p in self.EXCLUDE_PATHS):
            return None

        # 3. 提取基本信息
        request._operation_log = {
            'request_path': request.path,
            'request_method': request.method,
            'ip_address': self._get_client_ip(request),
            'user_agent': (request.META.get('HTTP_USER_AGENT') or '')[:500],
            'request_params': self._extract_params(request),
            'action_type': self.METHOD_TO_ACTION.get(request.method, 'OTHER'),
        }

        # 4. GET 请求如果是获取单条记录（/api/article/42/），标记为 VIEW
        if request.method == 'GET':
            path_parts = [p for p in request.path.rstrip('/').split('/') if p]
            if len(path_parts) >= 4 and path_parts[-1].isdigit():
                request._operation_log['action_type'] = 'VIEW'
            else:
                # GET 列表请求默认不记录（太频繁）
                return None  # 注意：返回 None 表示继续处理，但不在 process_response 记录

        return None

    def process_response(self, request, response):
        """
        响应返回时：检查是否需要记录，写入日志。

        注意：
            —— 必须检查 hasattr(request, '_operation_log') 确认前面要记录
            —— 记录失败不能影响主请求（用 try/except 包裹）
        """
        # 1. 没有 _operation_log 标记（GET 列表请求或排除路径）
        if not hasattr(request, '_operation_log'):
            return response

        # 2. 只记录非成功响应或变更类操作（可选：取消注释可只记录变更）
        # if response.status_code < 200 or response.status_code >= 300:
        #     return response  # 不记录失败请求

        log_data = request._operation_log

        try:
            self._create_log(
                request=request,
                response=response,
                log_data=log_data,
            )
        except Exception as e:
            # 记录失败不影响主请求（只打 warning）
            logger.warning('创建操作日志失败: %s', e, exc_info=True)

        return response

    def _create_log(self, request, response, log_data):
        """创建 OperationLog 记录"""
        # 用户信息
        user = getattr(request, 'user', None)
        username = ''
        if user and getattr(user, 'is_authenticated', False):
            username = getattr(user, 'username', '') or str(user)

        # 提取被操作对象（从 URL 路径推断）
        content_type = None
        object_id = None
        object_repr = ''

        try:
            from django.contrib.contenttypes.models import ContentType
            from django.apps import apps

            path_parts = request.path.rstrip('/').split('/')
            # /api/rbac/users/42/ → app=rbac, model=users → rbac.user
            if len(path_parts) >= 4:
                app_label = path_parts[1]
                model_name = path_parts[2].rstrip('s')  # users → user
                try:
                    app_config = apps.get_app_config(app_label)
                    model = app_config.get_model(model_name)
                    content_type = ContentType.objects.get_for_model(model)

                    # 提取 object_id（最后一截路径是数字）
                    if path_parts[-1].isdigit():
                        object_id = int(path_parts[-1])
                        # 尝试获取对象描述
                        try:
                            obj = model.objects.get(pk=object_id)
                            object_repr = str(obj)[:255]
                        except Exception:
                            pass
                except Exception:
                    pass
        except Exception:
            pass

        # 写入数据库
        from .models import OperationLog
        OperationLog.objects.create(
            user=user if (user and getattr(user, 'is_authenticated', False)) else None,
            username=username,
            action_type=log_data['action_type'],
            content_type=content_type,
            object_id=object_id,
            object_repr=object_repr,
            request_path=log_data['request_path'],
            request_method=log_data['request_method'],
            request_params=log_data['request_params'],
            ip_address=log_data['ip_address'],
            user_agent=log_data['user_agent'],
            status_code=response.status_code,
            error_message=(
                self._extract_error(response) if response.status_code >= 400 else ''
            ),
        )

    def _get_client_ip(self, request):
        """获取真实客户端 IP（支持代理）"""
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        if xff:
            return xff.split(',')[0].strip()[:45]
        return request.META.get('REMOTE_ADDR', '')[:45]

    def _extract_params(self, request):
        """提取请求参数（GET + POST/PUT/PATCH）"""
        params = {}
        if request.GET:
            params['query'] = dict(request.GET)

        if request.method in ('POST', 'PUT', 'PATCH'):
            try:
                body = request.body
                if body:
                    data = json.loads(body)
                    params['body'] = self._filter_sensitive(data)
            except Exception:
                pass

        return params

    def _filter_sensitive(self, data, depth=3):
        """
        过滤敏感字段（密码、Token、API Key 等）。

        为什么用黑名单而不是白名单？
            —— 白名单（只允许特定字段）太严格，容易漏掉业务字段
            —— 黑名单（过滤已知敏感字段）更实用
        """
        if depth <= 0:
            return '[MAX_DEPTH]'

        sensitive_keys = {
            'password', 'pwd', 'passwd', 'old_password', 'new_password',
            'token', 'access_token', 'refresh_token', 'secret',
            'api_key', 'apikey', 'private_key',
        }

        if isinstance(data, dict):
            return {
                k: ('***' if any(s in k.lower() for s in sensitive_keys) else self._filter_sensitive(v, depth - 1))
                for k, v in data.items()
            }
        elif isinstance(data, list):
            return [self._filter_sensitive(item, depth - 1) for item in data]
        else:
            return data

    def _extract_error(self, response):
        """从响应中提取错误信息"""
        if hasattr(response, 'data') and isinstance(response.data, dict):
            msg = response.data.get('detail') or response.data.get('message')
            if msg:
                return str(msg)[:1000]
        return ''
