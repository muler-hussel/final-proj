import './assets/main.css'
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import Antd from 'ant-design-vue'
import * as Icons from '@ant-design/icons-vue'
import axios from 'axios'
import PrimeVue from 'primevue/config';

const pinia = createPinia()
const app = createApp(App)

axios.defaults.baseURL = import.meta.env.VITE_SERVER

app.use(Antd).use(PrimeVue).use(router).use(pinia).mount('#app')

const icons = Icons;
type iconKey = keyof typeof icons
for (const i in icons) {
    app.component(i as iconKey, icons[i as iconKey]);
}