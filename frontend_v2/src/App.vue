<template>
  <div id="app">
    <a-layout class="app-layout">
      <a-layout-header class="app-header">
        <div class="header-brand">
          <span class="brand-icon">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" width="28" height="28">
              <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z" fill="currentColor"/>
              <circle cx="12" cy="9" r="2.5" fill="white"/>
            </svg>
          </span>
          <span class="brand-title">TripPilot</span>
          <span class="brand-edition">AGENT WORKBENCH</span>
        </div>
        <nav class="header-nav">
          <router-link to="/" class="nav-link">工作台</router-link>
          <router-link to="/plan" class="nav-link">新建任务</router-link>
          <span class="system-state" :class="`state-${runtimeState}`" :title="runtimeDetails"><i></i>{{ runtimeLabel }}</span>
        </nav>
      </a-layout-header>

      <a-layout-content class="app-content">
        <router-view />
      </a-layout-content>

      <a-layout-footer class="app-footer">
        <div class="footer-inner">
          <span class="footer-copy">TripPilot Agent Workbench &copy; {{ new Date().getFullYear() }}</span>
          <span class="footer-divider">|</span>
          <span class="footer-tech">基于 LangGraph + MCP 架构</span>
        </div>
      </a-layout-footer>
    </a-layout>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { healthCheck } from '@/services/api'

const runtimeState = ref<'checking' | 'ready' | 'degraded' | 'offline'>('checking')
const runtimeDetails = ref('正在检查 Agent Runtime')
const runtimeLabel = computed(() => ({ checking: 'Checking', ready: 'Agent Ready', degraded: 'Runtime Degraded', offline: 'Agent Offline' }[runtimeState.value]))

onMounted(async () => {
  try {
    const result = await healthCheck()
    runtimeState.value = result.agent_ready ? 'ready' : 'degraded'
    const missing = Object.entries(result.checks || {}).filter(([, item]: any) => !item.ready).map(([name]) => name)
    runtimeDetails.value = missing.length ? `缺少运行依赖：${missing.join('、')}` : `Runtime v${result.version} 已就绪`
  } catch {
    runtimeState.value = 'offline'
    runtimeDetails.value = '无法连接后端服务'
  }
})
</script>

<style>
:root {
  --font-display: 'Noto Serif SC', 'Georgia', serif;
  --font-body: 'Noto Sans SC', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;

  --color-ink: #1a1a2e;
  --color-slate: #16213e;
  --color-accent: #0f3460;
  --color-warm: #e94560;
  --color-cream: #faf9f6;
  --color-paper: #ffffff;
  --color-muted: #8b8b9a;
  --color-border: rgba(26, 26, 46, 0.08);
}

#app {
  font-family: var(--font-body);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: var(--color-ink);
}

.app-layout {
  min-height: 100vh;
  background: var(--color-cream);
}

.app-header {
  background: var(--color-ink) !important;
  padding: 0 48px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid rgba(255,255,255,0.06);
  position: sticky;
  top: 0;
  z-index: 100;
  backdrop-filter: blur(12px);
}

.header-brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand-icon {
  color: var(--color-warm);
  display: flex;
  align-items: center;
  justify-content: center;
}

.brand-title {
  font-family: var(--font-display);
  color: #ffffff;
  font-size: 20px;
  font-weight: 700;
  letter-spacing: 1px;
}

.brand-edition {
  margin-left: 2px;
  padding-left: 12px;
  border-left: 1px solid rgba(255,255,255,.18);
  color: #8d99af;
  font-size: 9px;
  font-weight: 800;
  letter-spacing: 1.7px;
}

.header-nav { display: flex; align-items: center; gap: 8px; }
.nav-link { padding: 7px 13px; border-radius: 8px; color: #9ca6b8; font-size: 13px; transition: .2s; }
.nav-link:hover, .nav-link.router-link-exact-active { background: rgba(255,255,255,.08); color: #fff; }
.system-state { margin-left: 12px; padding-left: 18px; border-left: 1px solid rgba(255,255,255,.12); color: #9ca6b8; font-size: 11px; text-transform: uppercase; letter-spacing: .7px; }
.system-state i { display: inline-block; width: 7px; height: 7px; margin-right: 7px; border-radius: 50%; background: #35c98a; box-shadow: 0 0 8px rgba(53,201,138,.65); }
.system-state.state-checking i,.system-state.state-degraded i { background:#f0b34d; box-shadow:0 0 8px rgba(240,179,77,.55); }
.system-state.state-offline i { background:#e35a6b; box-shadow:0 0 8px rgba(227,90,107,.55); }

.header-tagline {
  color: var(--color-muted);
  font-size: 13px;
  font-weight: 400;
  letter-spacing: 0.5px;
}

@media (max-width: 680px) {
  .app-header { padding: 0 16px; }
  .brand-edition, .system-state { display: none; }
  .nav-link { padding: 7px 9px; }
}

.app-content {
  background: var(--color-cream);
}

.app-footer {
  background: var(--color-paper) !important;
  border-top: 1px solid var(--color-border);
  padding: 20px 48px;
  text-align: center;
}

.footer-inner {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  color: var(--color-muted);
  font-size: 13px;
}

.footer-divider {
  opacity: 0.4;
}

.footer-tech {
  font-weight: 500;
  color: var(--color-accent);
}
</style>
