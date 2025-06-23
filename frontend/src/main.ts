import './assets/main.css'
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import Antd from 'ant-design-vue'
import * as Icons from '@ant-design/icons-vue'
import axios from 'axios'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'

const pinia = createPinia()
pinia.use(piniaPluginPersistedstate)
const app = createApp(App)

axios.defaults.baseURL = import.meta.env.VITE_SERVER

app.use(Antd).use(router).use(pinia).mount('#app')

const icons = Icons;
for (const i in icons) {
    app.component(i, icons[i]);
}