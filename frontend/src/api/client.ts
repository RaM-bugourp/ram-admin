import axios, { AxiosError } from 'axios'
import router from '@/router'
import store from '@/stores'
const client=axios.create({baseURL:'/api',timeout:15000,headers:{'Content-Type':'application/json'},withCredentials:true,xsrfCookieName:'csrftoken',xsrfHeaderName:'X-CSRFToken'})
client.interceptors.response.use(response=>response.data,(error:AxiosError<{error?:{code:string;message:string}}>)=>{
 const status=error.response?.status;const code=error.response?.data?.error?.code||'UNKNOWN'
 // Session expiry is confirmed through user-info only; a business 403/CSRF error must not navigate.
 if((status===401||status===403)&&error.config?.url==='/auth/user-info/'){store.commit('user/CLEAR');if(store.state.user.bootstrapped)router.replace('/login')}
 return Promise.reject({code,message:error.response?.data?.error?.message||'请求失败，请重试',status})
})
export default client
