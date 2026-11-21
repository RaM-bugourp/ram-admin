import { Module } from 'vuex'
import client from '@/api/client'
interface RoleInfo { id:number; name:string; code:string }
interface UserState { currentUser:{id:number;username:string;email:string;is_superuser?:boolean}|null;roles:RoleInfo[];permissions:string[];bootstrapped:boolean;aiEnabled:boolean }
let bootPromise:Promise<any>|null=null
const user:Module<UserState,any>={
 namespaced:true,
 state:():UserState=>({currentUser:null,roles:[],permissions:[],bootstrapped:false,aiEnabled:false}),
 getters:{
  isAuthenticated:(s:UserState)=>!!s.currentUser,
  isRoot:(s:UserState)=>!!s.currentUser?.is_superuser||s.roles.some(r=>r.code==='root'),
  isAdmin:(s:UserState)=>s.permissions.includes('users.write'),
  can:(s:UserState)=>(code:string)=>s.permissions.includes(code),
  roleCodes:(s:UserState)=>s.roles.map(r=>r.code),
 },
 mutations:{
  SET_USER(s:UserState,p:any){s.currentUser=p;s.roles=p?.roles||[];s.permissions=p?.permissions||[]},
  BOOTSTRAPPED(s:UserState){s.bootstrapped=true},
  AI_ENABLED(s:UserState,v:boolean){s.aiEnabled=v},
  CLEAR(s:UserState){s.currentUser=null;s.roles=[];s.permissions=[];s.aiEnabled=false},
 },
 actions:{
  async login({commit,dispatch}:any,credentials:{username:string;password:string}){await client.get('/auth/csrf/');const r:any=await client.post('/auth/login/',credentials);commit('SET_USER',r.data);commit('BOOTSTRAPPED');await dispatch('fetchSettings')},
  async fetchUserInfo({commit}:any){const r:any=await client.get('/auth/user-info/');commit('SET_USER',r.data)},
  async fetchSettings({commit}:any){const r:any=await client.get('/auth/settings/');commit('AI_ENABLED',!!r.data.ai_enabled)},
  async bootstrap({state,commit,dispatch}:any){if(state.bootstrapped)return;if(!bootPromise)bootPromise=(async()=>{try{await dispatch('fetchUserInfo');await dispatch('fetchSettings')}catch{commit('CLEAR')}finally{commit('BOOTSTRAPPED')}})();return bootPromise},
  async logout({commit}:any){await client.post('/auth/logout/');commit('CLEAR')},
 }
}
export default user
