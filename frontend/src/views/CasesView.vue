<template>
  <div>
    <div class="page-header">
      <div>
        <h1 class="page-title">Investigation Cases</h1>
        <p class="page-subtitle">Collaborative fraud investigation workflow</p>
      </div>
      <button class="btn btn-primary" @click="showCreate = true">+ New Case</button>
    </div>

    <!-- Filters -->
    <div style="display:flex;gap:0.75rem;margin-bottom:1rem">
      <select v-model="statusFilter" class="input" style="width:160px" @change="load">
        <option value="">All Status</option>
        <option value="open">Open</option>
        <option value="in_progress">In Progress</option>
        <option value="resolved">Resolved</option>
        <option value="closed">Closed</option>
      </select>
    </div>

    <div class="card">
      <div v-if="loading" style="display:flex;justify-content:center;padding:2rem">
        <div class="loader" style="width:28px;height:28px;border-width:3px" />
      </div>
      <div class="table-wrap" v-else>
        <table v-if="cases.length">
          <thead>
            <tr><th>Title</th><th>Transactions</th><th>Assigned To</th><th>Status</th><th>Created</th><th></th></tr>
          </thead>
          <tbody>
            <tr v-for="c in cases" :key="c.id" class="clickable-row" @click="$router.push(`/cases/${c.id}`)">
              <td class="td-primary">{{ c.title }}</td>
              <td class="mono">{{ c.transaction_ids.length }}</td>
              <td>{{ c.assigned_to_name || '—' }}</td>
              <td><StatusBadge :status="c.status" /></td>
              <td class="mono" style="font-size:0.75rem">{{ fmtDate(c.created_at) }}</td>
              <td><span class="chevron">›</span></td>
            </tr>
          </tbody>
        </table>
        <div v-else class="empty-state">
          <div class="icon">⊡</div>
          <p>No cases yet. Create one from an alert or manually.</p>
        </div>
      </div>
    </div>

    <!-- Create modal -->
    <div v-if="showCreate" class="modal-overlay" @click.self="showCreate = false">
      <div class="modal">
        <h3 style="margin-bottom:1.25rem">Create New Case</h3>
        <div class="field" style="margin-bottom:0.75rem">
          <label class="field-label">Title *</label>
          <input v-model="form.title" class="input" placeholder="Case title..." required />
        </div>
        <div class="field" style="margin-bottom:0.75rem">
          <label class="field-label">Transaction IDs (comma-separated)</label>
          <input v-model="form.txn_ids_raw" class="input" placeholder="txn-uuid-1, txn-uuid-2" />
        </div>
        <div class="field" style="margin-bottom:0.75rem">
          <label class="field-label">Description</label>
          <textarea v-model="form.description" class="input" rows="3" placeholder="Describe the suspected fraud pattern..." />
        </div>
        <div style="display:flex;gap:0.5rem;justify-content:flex-end">
          <button class="btn btn-secondary" @click="showCreate = false">Cancel</button>
          <button class="btn btn-primary" @click="create" :disabled="creating || !form.title">
            <span v-if="creating" class="loader" /> Create Case
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { casesApi } from '@/utils/api'
import { useToast } from '@/utils/toast'
import StatusBadge from '@/components/StatusBadge.vue'

const router = useRouter()
const toast = useToast()
const cases = ref([])
const loading = ref(false)
const statusFilter = ref('')
const showCreate = ref(false)
const creating = ref(false)
const form = ref({ title: '', txn_ids_raw: '', description: '' })

async function load() {
  loading.value = true
  try {
    const params = {}
    if (statusFilter.value) params.status = statusFilter.value
    const { data } = await casesApi.list(params)
    cases.value = data
  } finally { loading.value = false }
}

async function create() {
  creating.value = true
  try {
    const txn_ids = form.value.txn_ids_raw.split(',').map(s => s.trim()).filter(Boolean)
    const { data } = await casesApi.create({
      title: form.value.title,
      transaction_ids: txn_ids,
      description: form.value.description,
    })
    toast.success('Case created')
    showCreate.value = false
    router.push(`/cases/${data.id}`)
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Failed to create case')
  } finally { creating.value = false }
}

function fmtDate(d) {
  return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

onMounted(load)
</script>

<style scoped>
.clickable-row { cursor: pointer; }
.chevron { color: var(--text-muted); font-size: 1.2rem; }
.field-label { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text-muted); font-family: var(--font-mono); display: block; margin-bottom: 0.4rem; }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.6); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal { background: var(--bg-card); border: 1px solid var(--border-light); border-radius: var(--radius-lg); padding: 1.5rem; width: 520px; max-width: 90vw; box-shadow: var(--shadow); }
</style>
