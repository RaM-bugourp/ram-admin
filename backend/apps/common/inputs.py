from rest_framework.exceptions import ValidationError

def positive_int(value,name='id',maximum=None):
    try:
        if isinstance(value,bool):raise ValueError()
        result=int(value)
        if str(result)!=str(value) or result<1 or (maximum and result>maximum):raise ValueError()
    except (TypeError,ValueError):raise ValidationError({name:'必须为有效范围内的正整数'})
    return result

def pagination(request):
    return positive_int(request.query_params.get('page','1'),'page'),positive_int(request.query_params.get('page_size','20'),'page_size',100)
