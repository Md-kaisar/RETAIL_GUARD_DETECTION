<template>
  <div>
    <div class="page-header">
      <div>
        <h1 class="page-title">Transactions</h1>
        <p class="page-subtitle">{{ summary.total || 0 }} total · {{ summary.flagged || 0 }} flagged</p>
      </div>
      <RouterLink to="/transactions/upload" class="btn btn-primary">↑ Upload File</RouterLink>
    </div>

    <!-- Filters -->
    <div class="filters card" style="margin-bottom:1rem">
      <div class="filters-row">
        <select v-model="filters.status" class="input" style="width:160px" @change="load">
          <option value="">All Status</option>
          <option value="flagged">Flagged</option>
          <option value="cleared">Cleared</option>
          <option value="fraud">Fraud</option>
          <option value="pending">Pending</option>
          <option value="unscored">Unscored</option>
        </select>
        <div class="filter-group">
          <label class="filter-label">Min Score</label>
          <input v-model.number="filters.min_score" type="number" class="input" style="width:100px" min="0" max="1" step="0.1" placeholder="0.0" @change="load" />
        </div>
        <div class="filter-group">
          <label class="filter-label">Max Score</label>
          <input v-model.number="filters.max_score" type="number" class="input" style="width:100px" min="0" max="1" step="0.1" placeholder="1.0" @change="load" />
        </div>
        <button class="btn btn-secondary btn-sm" @click="resetFilters">Reset</button>
        <div class="filter-info mono">{{ transactions.length }} shown</div>
      </div>
    </div>

    <!-- Table -->
    <div class="card">
      <div v-if="loading" style="display:flex;justify-content:center;padding:2rem">
        <div class="loader" style="width:28px;height:28px;border-width:3px" />
      </div>
      <div class="table-wrap" v-else>
        <table v-if="transactions.length">
          <thead>
            <tr>
              <th>ID</th>
              <th>Timestamp</th>
              <th>Amount</th>
              <th>Merchant</th>
              <th>Customer</th>
              <th>Risk Score</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="t in transactions" :key="t.id">
              <td class="mono" style="font-size:0.75rem;color:var(--text-muted)">{{ t.id.slice(0,8) }}…</td>
              <td>{{ fmtDate(t.timestamp) }}</td>
              <td class="td-primary mono">${{ money(t.amount) }}</td>
              <td>{{ t.merchant_name || t.merchant_id }}</td>
              <td class="mono" style="font-size:0.75rem">{{ t.user_id }}</td>
              <td style="min-width:130px"><RiskBar :score="t.risk_score" /></td>
              <td><StatusBadge :status="t.status" /></td>
            </tr>
          </tbody>
        </table>
        <div v-else class="empty-state">
          <div class="icon">📋</div>
          <p>No transactions found. <RouterLink to="/transactions/upload">Upload a file</RouterLink> to get started.</p>
        </div>
      </div>

      <!-- Pagination -->
      <div class="pagination" v-if="transactions.length === limit">
        <button class="btn btn-secondary btn-sm" :disabled="page === 0" @click="page--; load()">← Prev</button>
        <span class="mono page-info">Page {{ page + 1 }}</span>
        <button class="btn btn-secondary btn-sm" @click="page++; load()">Next →</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { transactionsApi } from '@/utils/api'
import RiskBar from '@/components/RiskBar.vue'
import StatusBadge from '@/components/StatusBadge.vue'

const transactions = ref([])
const summary = ref({})
const loading = ref(false)
const page = ref(0)
const limit = 50
const filters = ref({ status: '', min_score: null, max_score: null })

async function load() {
  loading.value = true
  try {
    const params = { skip: page.value * limit, limit }
    if (filters.value.status) params.status = filters.value.status
    if (filters.value.min_score != null) params.min_score = filters.value.min_score
    if (filters.value.max_score != null) params.max_score = filters.value.max_score
    const [{ data: txns }, { data: sum }] = await Promise.all([
      transactionsApi.list(params),
      transactionsApi.summary(),
    ])
    transactions.value = txns
    summary.value = sum
  } finally { loading.value = false }
}

function resetFilters() {
  filters.value = { status: '', min_score: null, max_score: null }
  page.value = 0
  load()
}
function fmtDate(d) {
  return new Date(d).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}
function money(n) { return (n || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }

onMounted(load)
</script>

<style scoped>
.filters-row { display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap; }
.filter-group { display: flex; align-items: center; gap: 0.4rem; }
.filter-label { font-size: 0.75rem; color: var(--text-muted); white-space: nowrap; font-family: var(--font-mono); }
.filter-info { font-size: 0.75rem; color: var(--text-muted); margin-left: auto; }
.pagination { display: flex; align-items: center; gap: 1rem; justify-content: center; padding: 1rem 0 0; border-top: 1px solid var(--border); }
.page-info { font-size: 0.8rem; color: var(--text-muted); }
</style>
