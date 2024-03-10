// Composables
import { createRouter, createWebHashHistory, createWebHistory } from 'vue-router'

const routes = [
    {
        path: '/',
        component: () => import('@/views/Home.vue'),
        meta: {
            name: "配置",
        }
    },
]

const router = createRouter({
    history: createWebHashHistory(),
    routes,
})

export default router
