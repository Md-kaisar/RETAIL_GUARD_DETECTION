<template>
  <div>
    <div class="page-header">
      <div>
        <h1 class="page-title">Alerts</h1>
        <p class="page-subtitle">{{ newCount }} unacknowledged</p>
      </div>
      <select v-model="statusFilter" class="input" style="width:180px" @change="load">
        <option value="">All Alerts</option>
        <option value="new">New</option>
        <option value="acknowledged">Acknowledged</option>
        <option value="resolved">Resolved</option>
      </select>
    </div>

    <div class="card">
      <div v-if="loading" style="display:flex;justify-content:center;padding:2rem">
        <div class="loader" style="width:28px;height:28px;border-width:3px" />
      </div>
      <div class="table-wrap" v-else>
        <table v-if="alerts.length">
          <thead>
            <tr>
              <th>Triggered</th>
              <th>Transaction</th>
              <th>Amount</th>
              <th>Merchant</th>
              <th>Customer</th>
              <th>Risk Score</th>
              <th>Type</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="a in alerts" :key="a.id" :class="{ 'row-new': a.status === 'new' }">
              <td class="mono" style="font-size:0.75rem;white-space:nowrap">{{ fmtDate(a.triggered_at) }}</td>
              <td class="mono" style="font-size:0.75rem;color:var(--text-muted)">{{ a.transaction_id.slice(0,8) }}…</td>
              <td class="td-primary mono">${{ money(a.amount) }}</td>
              <td>{{ a.merchant_name || '—' }}</td>
              <td class="mono" style="font-size:0.75rem">{{ a.user_id || '—' }}</td>
              <td style="min-width:120px"><RiskBar :score="a.risk_score" /></td>
              <td><StatusBadge :status="a.type" /></td>
              <td><StatusBadge :status="a.status" /></td>
              <td>
                <div style="display:flex;gap:0.4rem">
                  <button v-if="a.status === 'new'" class="btn btn-secondary btn-sm" @click="updateAlert(a, 'acknowledged')">Ack</button>
                  <button v-if="a.status !== 'resolved'" class="btn btn-secondary btn-sm" @click="updateAlert(a, 'resolved')">Resolve</button>
                  <button class="btn btn-secondary btn-sm" @click="createCase(a)">Case</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-else class="empty-state">
          <div class="icon">✅</div>
          <p>No alerts found for the selected filter.</p>
        </div>
      </div>
    </div>

    <!-- Create case modal -->
    <div v-if="caseModal" class="modal-overlay" @click.self="caseModal = null">
      <div class="modal">
        <h3 style="margin-bottom:1rem">Create Investigation Case</h3>
        <div class="field" style="margin-bottom:0.75rem">
          <label class="field-label">Case Title</label>
          <input v-model="caseForm.title" class="input" placeholder="Describe the suspected fraud..." />
        </div>
        <div class="field" style="margin-bottom:1rem">
          <label class="field-label">Description (optional)</label>
          <textarea v-model="caseForm.description" class="input" rows="3" placeholder="Add context..." />
        </div>
        <div style="display:flex;gap:0.5rem;justify-content:flex-end">
          <button class="btn btn-secondary" @click="caseModal = null">Cancel</button>
          <button class="btn btn-primary" @click="submitCase" :disabled="creatingCase">
            <span v-if="creatingCase" class="loader" /> Create Case
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { alertsApi, casesApi } from '@/utils/api'
import { useToast } from '@/utils/toast'
import RiskBar from '@/components/RiskBar.vue'
import StatusBadge from '@/components/StatusBadge.vue'

const router = useRouter()
const toast = useToast()
const alerts = ref([])
const loading = ref(false)
const statusFilter = ref('')
const caseModal = ref(null)
const caseForm = ref({ title: '', description: '' })
const creatingCase = ref(false)
const newCount = computed(() => alerts.value.filter(a => a.status === 'new').length)

async function load() {
  loading.value = true
  try {
    const params = { limit: 100 }
    if (statusFilter.value) params.status = statusFilter.value
    const { data } = await alertsApi.list(params)
    alerts.value = data
  } finally { loading.value = false }
}

async function updateAlert(alert, status) {
  try {
    const { data } = await alertsApi.update(alert.id, status)
    Object.assign(alert, data)
    toast.success(`Alert ${status}`)
  } catch { toast.error('Failed to update alert') }
}

function createCase(alert) {
  caseModal.value = alert
  caseForm.value = {
    title: `Fraud Alert — $${money(alert.amount)} at ${alert.merchant_name || 'Unknown'}`,
    description: `Risk score: ${Math.round((alert.risk_score || 0) * 100)}%. Transaction ID: ${alert.transaction_id}`,
  }
}

async function submitCase() {
  creatingCase.value = true
  try {
    const { data } = await casesApi.create({
      title: caseForm.value.title,
      description: caseForm.value.description,
      transaction_ids: [caseModal.value.transaction_id],
    })
    toast.success('Case created')
    caseModal.value = null
    router.push(`/cases/${data.id}`)
  } catch { toast.error('Failed to create case') }
  finally { creatingCase.value = false }
}

function fmtDate(d) {
  return new Date(d).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}
function money(n) { return (n || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }

onMounted(load)
</script>

<style scoped>
.row-new td { background: #ff4d6a06; }
.field-label { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text-muted); font-family: var(--font-mono); display: block; margin-bottom: 0.4rem; }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.6); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal { background: var(--bg-card); border: 1px solid var(--border-light); border-radius: var(--radius-lg); padding: 1.5rem; width: 480px; max-width: 90vw; box-shadow: var(--shadow); }
</style>
