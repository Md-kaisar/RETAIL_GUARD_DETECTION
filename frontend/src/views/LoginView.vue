<template>
  <div class="login-page">
    <div class="login-bg">
      <div class="scan-line" />
    </div>

    <div class="login-container">
      <div class="login-header">
        <div class="login-logo">🛡️</div>
        <h1 class="login-title">RetailGuard</h1>
        <p class="login-sub">Fraud Detection & Prevention Suite</p>
      </div>

      <form class="login-form" @submit.prevent="submit">
        <div class="field">
          <label class="field-label">Email</label>
          <input v-model="form.email" type="email" class="input" placeholder="you@company.com" required />
        </div>
        <div class="field">
          <label class="field-label">Password</label>
          <input v-model="form.password" type="password" class="input" placeholder="••••••••" required />
        </div>

        <button type="submit" class="btn btn-primary login-btn" :disabled="loading">
          <span v-if="loading" class="loader" />
          <span v-else>Access System →</span>
        </button>

        <p v-if="error" class="error-msg">{{ error }}</p>
      </form>

      <div class="demo-creds">
        <div class="demo-title">Demo Credentials</div>
        <div v-for="cred in creds" :key="cred.role" class="demo-item" @click="fill(cred)">
          <StatusBadge :status="cred.role" />
          <span class="demo-email">{{ cred.email }}</span>
          <span class="demo-hint">click to fill</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/store/auth'
import StatusBadge from '@/components/StatusBadge.vue'

const router = useRouter()
const auth = useAuthStore()
const loading = ref(false)
const error = ref('')
const form = ref({ email: '', password: '' })

const creds = [
  { role: 'admin', email: 'admin@retailguard.io', password: 'Admin@123' },
  { role: 'analyst', email: 'analyst@retailguard.io', password: 'Analyst@123' },
  { role: 'investigator', email: 'investigator@retailguard.io', password: 'Invest@123' },
]

function fill(cred) {
  form.value.email = cred.email
  form.value.password = cred.password
}

async function submit() {
  loading.value = true
  error.value = ''
  try {
    await auth.login(form.value.email, form.value.password)
    router.push('/dashboard')
  } catch (e) {
    error.value = e.response?.data?.detail || 'Login failed'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  background: var(--bg-primary);
}

.login-bg {
  position: absolute;
  inset: 0;
  background:
    linear-gradient(135deg, #00d4aa08 0%, transparent 50%),
    repeating-linear-gradient(0deg, transparent, transparent 39px, #242a3320 40px),
    repeating-linear-gradient(90deg, transparent, transparent 39px, #242a3320 40px);
}
.scan-line {
  position: absolute;
  width: 100%;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--accent), transparent);
  opacity: 0.3;
  animation: scan 4s linear infinite;
}
@keyframes scan { from { top: 0; } to { top: 100%; } }

.login-container {
  position: relative;
  background: var(--bg-card);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  padding: 2.5rem;
  width: 420px;
  box-shadow: var(--shadow), 0 0 60px #00d4aa0a;
}

.login-header { text-align: center; margin-bottom: 2rem; }
.login-logo { font-size: 3rem; margin-bottom: 0.75rem; }
.login-title {
  font-family: var(--font-mono);
  font-size: 1.75rem;
  color: var(--accent);
  letter-spacing: -0.03em;
}
.login-sub { color: var(--text-muted); font-size: 0.8rem; margin-top: 0.3rem; }

.login-form { display: flex; flex-direction: column; gap: 1rem; }
.field { display: flex; flex-direction: column; gap: 0.4rem; }
.field-label {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-muted);
  font-family: var(--font-mono);
}
.login-btn { width: 100%; justify-content: center; padding: 0.75rem; font-size: 0.95rem; margin-top: 0.5rem; }
.error-msg { color: var(--red); font-size: 0.8rem; text-align: center; }

.demo-creds {
  margin-top: 1.5rem;
  padding-top: 1.25rem;
  border-top: 1px solid var(--border);
}
.demo-title {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-muted);
  font-family: var(--font-mono);
  margin-bottom: 0.75rem;
}
.demo-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem 0.75rem;
  border-radius: var(--radius);
  cursor: pointer;
  transition: background 0.1s;
}
.demo-item:hover { background: var(--bg-hover); }
.demo-email { font-size: 0.8rem; color: var(--text-secondary); flex: 1; }
.demo-hint { font-size: 0.7rem; color: var(--text-muted); font-style: italic; }
</style>
