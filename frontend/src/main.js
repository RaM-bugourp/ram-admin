import { createApp } from 'vue'
import ArcoVue from '@arco-design/web-vue'
import '@arco-design/web-vue/dist/arco.css'
import App from './App.vue'
import router from './router'
import store from './store'
import { setupDirectives } from './directives/permission'
import { setupLoadingDirective } from './directives/loading'
import './style.css'

const app = createApp(App)

app.use(ArcoVue, {
  // Arco Design 全局配置
})

app.use(store)
app.use(router)

// 注册自定义指令
setupDirectives(app)
setupLoadingDirective(app)

app.mount('#app')
