import './assets/main.css'
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import Antd from 'ant-design-vue'
import * as Icons from '@ant-design/icons-vue';

const app = createApp(App)

app.use(Antd).use(router).mount('#app')

const icons = Icons;
for (const i in icons) {
    app.component(i, icons[i]);
}