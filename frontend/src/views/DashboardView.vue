<template>
  <div>
    <div class="page-header">
      <div>
        <h1 class="page-title">Dashboard</h1>
        <p class="page-subtitle">System overview · {{ now }}</p>
      </div>
      <button class="btn btn-secondary" @click="load" :disabled="loading">
        <span v-if="loading" class="loader" /> ↻ Refresh
      </button>
    </div>

    <!-- Stat Cards -->
    <div class="grid-4" style="margin-bottom:1.25rem">
      <div class="stat-card">
        <div class="label">Total Transactions</div>
        <div class="value mono">{{ fmt(stats.total_transactions) }}</div>
        <div class="sub">All time</div>
      </div>
      <div class="stat-card" style="border-color:#ff4d6a44">
        <div class="label" style="color:var(--red)">Flagged Today</div>
        <div class="value mono" style="color:var(--red)">{{ stats.flagged_today }}</div>
        <div class="sub">Fraud rate: {{ pct(stats.fraud_rate) }}</div>
      </div>
      <div class="stat-card" style="border-color:#4da6ff44">
        <div class="label" style="color:var(--blue)">Active Cases</div>
        <div class="value mono" style="color:var(--blue)">{{ stats.active_cases }}</div>
        <div class="sub">Open + in progress</div>
      </div>
      <div class="stat-card" style="border-color:#ffd16644">
        <div class="label" style="color:var(--yellow)">New Alerts</div>
        <div class="value mono" style="color:var(--yellow)">{{ stats.new_alerts }}</div>
        <div class="sub">Unacknowledged</div>
      </div>
    </div>

    <div class="grid-2" style="margin-bottom:1.25rem">
      <!-- Volume chart -->
      <div class="card">
        <div class="chart-header">
          <h3>Transaction Volume (14 days)</h3>
        </div>
        <div style="height:200px" v-if="volumeData">
          <Bar :data="volumeData" :options="barOptions" />
        </div>
        <div v-else class="empty-state"><div class="icon">📊</div><p>No data yet</p></div>
      </div>

      <!-- Risk distribution -->
      <div class="card">
        <div class="chart-header">
          <h3>Risk Distribution</h3>
        </div>
        <div style="height:200px;display:flex;align-items:center;justify-content:center" v-if="riskData">
          <Doughnut :data="riskData" :options="doughnutOptions" style="max-height:200px" />
        </div>
        <div v-else class="empty-state"><div class="icon">🎯</div><p>No data yet</p></div>
      </div>
    </div>

    <div class="grid-2">
      <!-- Recent alerts -->
      <div class="card">
        <div class="chart-header" style="margin-bottom:0.75rem">
          <h3>Recent Alerts</h3>
          <RouterLink to="/alerts" class="btn btn-secondary btn-sm">View All</RouterLink>
        </div>
        <div class="table-wrap">
          <table v-if="stats.recent_alerts?.length">
            <thead><tr><th>Amount</th><th>Merchant</th><th>Score</th><th>Status</th></tr></thead>
            <tbody>
              <tr v-for="a in stats.recent_alerts" :key="a.id">
                <td class="td-primary mono">${{ money(a.amount) }}</td>
                <td>{{ a.merchant_name }}</td>
                <td><RiskBar :score="a.risk_score" /></td>
                <td><StatusBadge :status="a.status" /></td>
              </tr>
            </tbody>
          </table>
          <div v-else class="empty-state"><div class="icon">✓</div><p>No recent alerts</p></div>
        </div>
      </div>

      <!-- Top merchants -->
      <div class="card">
        <div class="chart-header" style="margin-bottom:0.75rem">
          <h3>Top Flagged Merchants</h3>
          <div class="stat-pill">Fraud exposure</div>
        </div>
        <div v-if="stats.top_merchants?.length">
          <div v-for="m in stats.top_merchants" :key="m.name" class="merchant-row">
            <div class="merchant-name">{{ m.name }}</div>
            <div class="merchant-bar-wrap">
              <div class="merchant-bar" :style="{ width: barPct(m.count) }" />
            </div>
            <div class="merchant-count mono">{{ m.count }}</div>
            <div class="merchant-amount">${{ money(m.total_amount) }}</div>
          </div>
        </div>
        <div v-else class="empty-state"><div class="icon">🏪</div><p>No flagged merchants</p></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { Bar, Doughnut } from 'vue-chartjs'
import { Chart, registerables } from 'chart.js'
import { dashboardApi } from '@/utils/api'
import RiskBar from '@/components/RiskBar.vue'
import StatusBadge from '@/components/StatusBadge.vue'

Chart.register(...registerables)

const loading = ref(false)
const stats = ref({
  total_transactions: 0, flagged_today: 0, active_cases: 0, new_alerts: 0,
  fraud_rate: 0, total_fraud_amount: 0, avg_risk_score: 0,
  transactions_by_day: [], risk_distribution: [], top_merchants: [], recent_alerts: [],
})

const now = computed(() => new Date().toLocaleString())

const volumeData = computed(() => {
  const days = stats.value.transactions_by_day
  if (!days.length) return null
  return {
    labels: days.map(d => d.date.slice(5)),
    datasets: [
      { label: 'Total', data: days.map(d => d.count), backgroundColor: '#4da6ff30', borderColor: '#4da6ff', borderWidth: 1.5, borderRadius: 3 },
      { label: 'Flagged', data: days.map(d => d.flagged), backgroundColor: '#ff4d6a30', borderColor: '#ff4d6a', borderWidth: 1.5, borderRadius: 3 },
    ],
  }
})

const riskData = computed(() => {
  const dist = stats.value.risk_distribution
  if (!dist.length) return null
  return {
    labels: dist.map(d => d.label),
    datasets: [{
      data: dist.map(d => d.count),
      backgroundColor: ['#06d6a040', '#ffd16640', '#ff8c4240', '#ff4d6a40'],
      borderColor: ['#06d6a0', '#ffd166', '#ff8c42', '#ff4d6a'],
      borderWidth: 2,
    }],
  }
})

const barOptions = {
  responsive: true, maintainAspectRatio: false,
  plugins: { legend: { labels: { color: '#8b96a5', boxWidth: 12, font: { size: 11 } } } },
  scales: {
    x: { grid: { color: '#242a33' }, ticks: { color: '#5a6572', font: { size: 10 } } },
    y: { grid: { color: '#242a33' }, ticks: { color: '#5a6572', font: { size: 10 } } },
  },
}
const doughnutOptions = {
  responsive: true, maintainAspectRatio: false,
  plugins: { legend: { position: 'right', labels: { color: '#8b96a5', boxWidth: 12, font: { size: 11 } } } },
  cutout: '65%',
}

const maxCount = computed(() => Math.max(...(stats.value.top_merchants?.map(m => m.count) || [1])))
function barPct(count) { return `${Math.round(count / maxCount.value * 100)}%` }

async function load() {
  loading.value = true
  try {
    const { data } = await dashboardApi.stats()
    stats.value = data
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

function fmt(n) { return (n || 0).toLocaleString() }
function pct(n) { return `${((n || 0) * 100).toFixed(1)}%` }
function money(n) { return (n || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }

onMounted(load)
</script>

<style scoped>
.chart-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem; }
.stat-pill {
  font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.06em;
  color: var(--text-muted); font-family: var(--font-mono); padding: 0.2rem 0.5rem;
  border: 1px solid var(--border); border-radius: 20px;
}
.merchant-row {
  display: flex; align-items: center; gap: 0.75rem;
  padding: 0.5rem 0; border-bottom: 1px solid var(--border);
}
.merchant-row:last-child { border-bottom: none; }
.merchant-name { width: 130px; font-size: 0.8rem; color: var(--text-primary); flex-shrink: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.merchant-bar-wrap { flex: 1; height: 6px; background: var(--bg-tertiary); border-radius: 3px; overflow: hidden; }
.merchant-bar { height: 100%; background: var(--red); border-radius: 3px; transition: width 0.5s ease; }
.merchant-count { width: 30px; text-align: right; font-size: 0.8rem; color: var(--red); }
.merchant-amount { width: 80px; text-align: right; font-size: 0.75rem; color: var(--text-muted); }
</style>
