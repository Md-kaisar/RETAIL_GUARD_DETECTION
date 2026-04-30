<template>
  <div class="layout">
    <!-- Sidebar -->
    <aside class="sidebar">
      <div class="sidebar-brand">
        <span class="brand-icon">🛡️</span>
        <div>
          <div class="brand-name">RetailGuard</div>
          <div class="brand-sub">Fraud Detection Suite</div>
        </div>
      </div>

      <nav class="sidebar-nav">
        <RouterLink v-for="item in navItems" :key="item.to" :to="item.to" class="nav-item">
          <span class="nav-icon">{{ item.icon }}</span>
          <span class="nav-label">{{ item.label }}</span>
          <span v-if="item.badge" class="nav-badge">{{ item.badge }}</span>
        </RouterLink>
      </nav>

      <div class="sidebar-footer">
        <div class="user-info">
          <div class="user-avatar">{{ auth.user?.name?.[0] || '?' }}</div>
          <div>
            <div class="user-name">{{ auth.user?.name }}</div>
            <div class="user-role">{{ auth.user?.role }}</div>
          </div>
        </div>
        <button class="btn btn-secondary btn-sm" @click="logout">Logout</button>
      </div>
    </aside>

    <!-- Main content -->
    <main class="main-content">
      <RouterView />
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { RouterLink, RouterView, useRouter } from 'vue-router'
import { useAuthStore } from '@/store/auth'
import { alertsApi } from '@/utils/api'

const auth = useAuthStore()
const router = useRouter()
const alertCount = ref(0)

async function fetchAlertCount() {
  try {
    const { data } = await alertsApi.count()
    alertCount.value = data.new
  } catch {}
}

onMounted(fetchAlertCount)

const navItems = [
  { to: '/dashboard', icon: '◈', label: 'Dashboard' },
  { to: '/transactions', icon: '⟁', label: 'Transactions' },
  { to: '/transactions/upload', icon: '↑', label: 'Upload' },
  { to: '/alerts', icon: '⚠', label: 'Alerts' },
  { to: '/cases', icon: '⊡', label: 'Cases' },
  { to: '/users', icon: '◉', label: 'Users' },
  { to: '/audit', icon: '≡', label: 'Audit Log' },
]

function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.layout {
  display: flex;
  min-height: 100vh;
}

.sidebar {
  width: var(--sidebar-width);
  min-height: 100vh;
  background: var(--bg-secondary);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  position: fixed;
  top: 0; left: 0;
  z-index: 100;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1.25rem 1rem;
  border-bottom: 1px solid var(--border);
}
.brand-icon { font-size: 1.5rem; }
.brand-name {
  font-family: var(--font-mono);
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--accent);
  letter-spacing: 0.02em;
}
.brand-sub { font-size: 0.7rem; color: var(--text-muted); }

.sidebar-nav {
  flex: 1;
  padding: 0.75rem 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.nav-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.625rem 1rem;
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 0.875rem;
  font-weight: 500;
  border-radius: 0;
  transition: all 0.15s;
  position: relative;
}
.nav-item:hover { background: var(--bg-hover); color: var(--text-primary); }
.nav-item.router-link-active {
  background: var(--accent-dim);
  color: var(--accent);
  border-right: 2px solid var(--accent);
}
.nav-icon {
  width: 1.25rem;
  text-align: center;
  font-size: 1rem;
  flex-shrink: 0;
}
.nav-badge {
  margin-left: auto;
  background: var(--red);
  color: white;
  font-size: 0.65rem;
  font-weight: 700;
  padding: 0.1rem 0.4rem;
  border-radius: 10px;
}

.sidebar-footer {
  padding: 1rem;
  border-top: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
.user-info {
  display: flex;
  align-items: center;
  gap: 0.625rem;
}
.user-avatar {
  width: 32px; height: 32px;
  background: var(--accent-dim);
  border: 1px solid var(--accent);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  color: var(--accent);
  font-family: var(--font-mono);
  font-size: 0.875rem;
  flex-shrink: 0;
}
.user-name { font-size: 0.8rem; font-weight: 600; }
.user-role {
  font-size: 0.7rem;
  color: var(--text-muted);
  text-transform: uppercase;
  font-family: var(--font-mono);
  letter-spacing: 0.05em;
}

.main-content {
  margin-left: var(--sidebar-width);
  flex: 1;
  padding: 1.75rem;
  min-height: 100vh;
}
</style>
