<template>
  <div>
    <div class="page-header">
      <div>
        <h1 class="page-title">Audit Log</h1>
        <p class="page-subtitle">Immutable record of all system actions</p>
      </div>
      <button class="btn btn-secondary" @click="load">↻ Refresh</button>
    </div>

    <div v-if="!auth.isAdmin" class="card" style="color:var(--red);text-align:center;padding:2rem">
      ⚠ Admin access required to view audit logs.
    </div>

    <div v-else>
      <!-- Action filter chips -->
      <div class="filter-chips" style="margin-bottom:1rem">
        <button
          v-for="f in filterOptions" :key="f.value"
          :class="['chip', { active: actionFilter === f.value }]"
          @click="actionFilter = f.value; load()"
        >{{ f.label }}</button>
      </div>

      <div class="card">
        <div v-if="loading" style="display:flex;justify-content:center;padding:2rem">
          <div class="loader" style="width:28px;height:28px;border-width:3px" />
        </div>
        <div class="table-wrap" v-else>
          <table v-if="logs.length">
            <thead>
              <tr><th>Timestamp</th><th>User</th><th>Action</th><th>Details</th></tr>
            </thead>
            <tbody>
              <tr v-for="log in filteredLogs" :key="log.id">
                <td class="mono" style="font-size:0.75rem;white-space:nowrap;color:var(--text-muted)">
                  {{ fmtDate(log.timestamp) }}
                </td>
                <td>
                  <div style="display:flex;align-items:center;gap:0.5rem">
                    <div class="mini-avatar">{{ log.user_name?.[0] || '?' }}</div>
                    <span style="font-size:0.85rem">{{ log.user_name }}</span>
                  </div>
                </td>
                <td>
                  <span :class="['action-tag', actionColor(log.action)]">{{ log.action }}</span>
                </td>
                <td>
                  <div class="details-cell">
                    <span v-for="(v, k) in log.details" :key="k" class="detail-pill">
                      <span class="detail-key">{{ k }}</span>
                      <span class="detail-val">{{ truncate(String(v)) }}</span>
                    </span>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
          <div v-else class="empty-state"><div class="icon">≡</div><p>No audit logs found.</p></div>
        </div>

        <!-- Load more -->
        <div v-if="logs.length === limit" style="display:flex;justify-content:center;padding:1rem;border-top:1px solid var(--border)">
          <button class="btn btn-secondary" @click="loadMore">Load More</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/store/auth'
import { dashboardApi } from '@/utils/api'

const auth = useAuthStore()
const logs = ref([])
const loading = ref(false)
const skip = ref(0)
const limit = 100
const actionFilter = ref('ALL')

const filterOptions = [
  { label: 'All', value: 'ALL' },
  { label: 'Auth', value: 'AUTH' },
  { label: 'Transactions', value: 'TRANSACTIONS' },
  { label: 'Cases', value: 'CASE' },
  { label: 'Alerts', value: 'ALERT' },
  { label: 'Users', value: 'USER' },
]

const filteredLogs = computed(() => {
  if (actionFilter.value === 'ALL') return logs.value
  return logs.value.filter(l => l.action.startsWith(actionFilter.value))
})

async function load() {
  loading.value = true
  skip.value = 0
  try {
    const { data } = await dashboardApi.auditLogs({ skip: 0, limit })
    logs.value = data
  } finally { loading.value = false }
}

async function loadMore() {
  skip.value += limit
  try {
    const { data } = await dashboardApi.auditLogs({ skip: skip.value, limit })
    logs.value.push(...data)
  } catch {}
}

function fmtDate(d) {
  return new Date(d).toLocaleString('en-US', {
    month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit', second: '2-digit'
  })
}

function truncate(s, n = 40) {
  return s.length > n ? s.slice(0, n) + '…' : s
}

function actionColor(action) {
  if (action.includes('LOGIN') || action.includes('REGISTER')) return 'action-auth'
  if (action.includes('UPLOAD') || action.includes('TRANSACTION')) return 'action-txn'
  if (action.includes('CASE')) return 'action-case'
  if (action.includes('ALERT')) return 'action-alert'
  if (action.includes('USER')) return 'action-user'
  return 'action-default'
}

onMounted(load)
</script>

<style scoped>
.filter-chips { display: flex; gap: 0.5rem; flex-wrap: wrap; }
.chip {
  padding: 0.35rem 0.875rem;
  border-radius: 20px;
  border: 1px solid var(--border-light);
  background: transparent;
  color: var(--text-secondary);
  font-size: 0.8rem;
  cursor: pointer;
  font-family: var(--font-mono);
  letter-spacing: 0.03em;
  transition: all 0.15s;
}
.chip:hover { border-color: var(--accent); color: var(--accent); }
.chip.active { background: var(--accent-dim); border-color: var(--accent); color: var(--accent); }

.mini-avatar {
  width: 24px; height: 24px; border-radius: 50%;
  background: var(--bg-tertiary); border: 1px solid var(--border-light);
  display: flex; align-items: center; justify-content: center;
  font-size: 0.7rem; font-weight: 700; color: var(--text-secondary); flex-shrink: 0;
}

.action-tag {
  display: inline-block;
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
  font-family: var(--font-mono);
  font-size: 0.72rem;
  letter-spacing: 0.04em;
  font-weight: 600;
}
.action-auth { background: #4da6ff18; color: var(--blue); border: 1px solid #4da6ff33; }
.action-txn { background: #00d4aa18; color: var(--accent); border: 1px solid #00d4aa33; }
.action-case { background: #ffd16618; color: var(--yellow); border: 1px solid #ffd16633; }
.action-alert { background: #ff4d6a18; color: var(--red); border: 1px solid #ff4d6a33; }
.action-user { background: #ff8c4218; color: var(--orange); border: 1px solid #ff8c4233; }
.action-default { background: var(--bg-tertiary); color: var(--text-muted); border: 1px solid var(--border); }

.details-cell { display: flex; gap: 0.4rem; flex-wrap: wrap; max-width: 360px; }
.detail-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 0.1rem 0.4rem;
  font-size: 0.7rem;
}
.detail-key { color: var(--text-muted); font-family: var(--font-mono); }
.detail-val { color: var(--text-secondary); font-family: var(--font-mono); }
</style>
