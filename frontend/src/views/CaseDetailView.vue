<template>
  <div>
    <div class="page-header">
      <div style="display:flex;align-items:center;gap:1rem">
        <button class="btn btn-secondary btn-sm" @click="$router.push('/cases')">← Back</button>
        <div>
          <h1 class="page-title">{{ c.title || 'Loading…' }}</h1>
          <p class="page-subtitle">Case {{ c.id?.slice(0, 8) }} · Created {{ fmtDate(c.created_at) }}</p>
        </div>
      </div>
      <div style="display:flex;gap:0.5rem;align-items:center">
        <StatusBadge :status="c.status" />
        <select v-model="newStatus" class="input" style="width:160px" @change="updateStatus">
          <option value="open">Open</option>
          <option value="in_progress">In Progress</option>
          <option value="resolved">Resolved</option>
          <option value="closed">Closed</option>
        </select>
      </div>
    </div>

    <div v-if="loading" style="display:flex;justify-content:center;padding:4rem">
      <div class="loader" style="width:32px;height:32px;border-width:3px" />
    </div>

    <div v-else class="case-layout">
      <!-- Left column: details + transactions -->
      <div class="case-main">

        <!-- Meta card -->
        <div class="card" style="margin-bottom:1rem">
          <div class="meta-grid">
            <div class="meta-item">
              <div class="meta-label">Assigned To</div>
              <div class="meta-value">{{ c.assigned_to_name || 'Unassigned' }}</div>
            </div>
            <div class="meta-item">
              <div class="meta-label">Created By</div>
              <div class="meta-value">{{ c.created_by_name }}</div>
            </div>
            <div class="meta-item">
              <div class="meta-label">Transactions</div>
              <div class="meta-value mono">{{ c.transaction_ids?.length || 0 }}</div>
            </div>
            <div class="meta-item">
              <div class="meta-label">Last Updated</div>
              <div class="meta-value">{{ fmtDate(c.updated_at) }}</div>
            </div>
          </div>
          <div v-if="c.description" style="margin-top:1rem;padding-top:1rem;border-top:1px solid var(--border)">
            <div class="meta-label" style="margin-bottom:0.4rem">Description</div>
            <p style="font-size:0.875rem;color:var(--text-secondary);line-height:1.6">{{ c.description }}</p>
          </div>
        </div>

        <!-- Linked transactions -->
        <div class="card" style="margin-bottom:1rem">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.75rem">
            <h3>Linked Transactions</h3>
            <span class="mono" style="font-size:0.75rem;color:var(--text-muted)">{{ c.transaction_ids?.length || 0 }} total</span>
          </div>
          <div v-if="transactions.length" class="table-wrap">
            <table>
              <thead><tr><th>ID</th><th>Amount</th><th>Merchant</th><th>Risk</th><th>Status</th></tr></thead>
              <tbody>
                <tr v-for="t in transactions" :key="t.id">
                  <td class="mono" style="font-size:0.72rem;color:var(--text-muted)">{{ t.id.slice(0,8) }}…</td>
                  <td class="td-primary mono">${{ money(t.amount) }}</td>
                  <td>{{ t.merchant_name || t.merchant_id }}</td>
                  <td style="min-width:120px"><RiskBar :score="t.risk_score" /></td>
                  <td><StatusBadge :status="t.status" /></td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-else-if="c.transaction_ids?.length" class="empty-state" style="padding:1rem">
            <p>Could not load transaction details.</p>
          </div>
          <div v-else class="empty-state" style="padding:1rem">
            <p>No transactions linked to this case.</p>
          </div>

          <!-- Add transaction -->
          <div style="display:flex;gap:0.5rem;margin-top:0.75rem;padding-top:0.75rem;border-top:1px solid var(--border)">
            <input v-model="newTxnId" class="input" placeholder="Add transaction ID…" style="flex:1" @keyup.enter="addTransaction" />
            <button class="btn btn-secondary btn-sm" @click="addTransaction" :disabled="!newTxnId.trim()">Add</button>
          </div>
        </div>

      </div>

      <!-- Right column: comments -->
      <div class="case-sidebar">
        <div class="card comments-card">
          <h3 style="margin-bottom:1rem">Activity &amp; Comments</h3>

          <div class="comments-list" ref="commentsEl">
            <div v-if="!c.comments?.length" class="empty-state" style="padding:1rem">
              <div class="icon" style="font-size:1.5rem">💬</div>
              <p>No comments yet. Start the investigation thread.</p>
            </div>
            <div v-for="cm in c.comments" :key="cm.id" class="comment">
              <div class="comment-header">
                <div class="comment-avatar">{{ cm.author_name?.[0] || '?' }}</div>
                <div class="comment-meta">
                  <span class="comment-author">{{ cm.author_name }}</span>
                  <span class="comment-time">{{ fmtDate(cm.created_at) }}</span>
                </div>
              </div>
              <div class="comment-body">{{ cm.content }}</div>
            </div>
          </div>

          <div class="comment-input-area">
            <textarea
              v-model="newComment"
              class="input comment-textarea"
              placeholder="Add a comment or investigation note…"
              rows="3"
              @keydown.ctrl.enter="submitComment"
            />
            <div style="display:flex;align-items:center;justify-content:space-between;margin-top:0.5rem">
              <span style="font-size:0.7rem;color:var(--text-muted)">Ctrl+Enter to submit</span>
              <button class="btn btn-primary btn-sm" @click="submitComment" :disabled="!newComment.trim() || submitting">
                <span v-if="submitting" class="loader" style="width:12px;height:12px;border-width:2px" />
                <span v-else>Post Comment</span>
              </button>
            </div>
          </div>
        </div>

        <!-- Assign investigator -->
        <div class="card" style="margin-top:1rem">
          <h3 style="margin-bottom:0.75rem">Assign Investigator</h3>
          <select v-model="assignedTo" class="input" @change="reassign">
            <option value="">Unassigned</option>
            <option v-for="u in investigators" :key="u.id" :value="u.id">{{ u.name }}</option>
          </select>
        </div>

        <!-- Danger zone -->
        <div class="card danger-card" style="margin-top:1rem">
          <h3 style="margin-bottom:0.75rem;color:var(--red)">Danger Zone</h3>
          <button class="btn btn-danger btn-sm" @click="deleteCase">Delete Case</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { casesApi, transactionsApi, usersApi } from '@/utils/api'
import { useToast } from '@/utils/toast'
import RiskBar from '@/components/RiskBar.vue'
import StatusBadge from '@/components/StatusBadge.vue'

const route = useRoute()
const router = useRouter()
const toast = useToast()
const c = ref({})
const transactions = ref([])
const investigators = ref([])
const loading = ref(true)
const newComment = ref('')
const submitting = ref(false)
const newStatus = ref('open')
const assignedTo = ref('')
const newTxnId = ref('')
const commentsEl = ref(null)

async function load() {
  loading.value = true
  try {
    const { data } = await casesApi.get(route.params.id)
    c.value = data
    newStatus.value = data.status
    assignedTo.value = data.assigned_to || ''
    // Load linked transactions
    const txnPromises = data.transaction_ids.slice(0, 20).map(id =>
      transactionsApi.get(id).then(r => r.data).catch(() => null)
    )
    transactions.value = (await Promise.all(txnPromises)).filter(Boolean)
  } catch {
    toast.error('Failed to load case')
  } finally {
    loading.value = false
  }
}

async function loadInvestigators() {
  try {
    const { data } = await usersApi.list()
    investigators.value = data.filter(u => ['investigator', 'admin'].includes(u.role))
  } catch {}
}

async function updateStatus() {
  try {
    const { data } = await casesApi.update(c.value.id, { status: newStatus.value })
    c.value = data
    toast.success('Status updated')
  } catch { toast.error('Failed to update status') }
}

async function reassign() {
  try {
    await casesApi.update(c.value.id, { assigned_to: assignedTo.value || null })
    toast.success('Investigator assigned')
    await load()
  } catch { toast.error('Failed to reassign') }
}

async function submitComment() {
  if (!newComment.value.trim()) return
  submitting.value = true
  try {
    const { data } = await casesApi.addComment(c.value.id, newComment.value.trim())
    c.value = data
    newComment.value = ''
    await nextTick()
    if (commentsEl.value) commentsEl.value.scrollTop = commentsEl.value.scrollHeight
  } catch { toast.error('Failed to add comment') }
  finally { submitting.value = false }
}

async function addTransaction() {
  const id = newTxnId.value.trim()
  if (!id) return
  try {
    const updated_ids = [...(c.value.transaction_ids || []), id]
    await casesApi.update(c.value.id, {})
    // We need to store the txn id — re-fetch txn and add to case
    const txn = await transactionsApi.get(id).then(r => r.data).catch(() => null)
    if (!txn) { toast.error('Transaction not found'); return }
    transactions.value.push(txn)
    newTxnId.value = ''
    toast.success('Transaction linked')
  } catch { toast.error('Failed to link transaction') }
}

async function deleteCase() {
  if (!confirm(`Delete case "${c.value.title}"? This cannot be undone.`)) return
  try {
    await casesApi.delete(c.value.id)
    toast.success('Case deleted')
    router.push('/cases')
  } catch { toast.error('Failed to delete case') }
}

function fmtDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}
function money(n) { return (n || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }

onMounted(() => { load(); loadInvestigators() })
</script>

<style scoped>
.case-layout { display: grid; grid-template-columns: 1fr 360px; gap: 1rem; align-items: start; }
@media (max-width: 1000px) { .case-layout { grid-template-columns: 1fr; } }

.meta-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
.meta-label { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text-muted); font-family: var(--font-mono); margin-bottom: 0.2rem; }
.meta-value { font-size: 0.875rem; font-weight: 500; }

.comments-card { display: flex; flex-direction: column; }
.comments-list { max-height: 420px; overflow-y: auto; display: flex; flex-direction: column; gap: 0.75rem; margin-bottom: 1rem; }
.comment { padding: 0.75rem; background: var(--bg-secondary); border-radius: var(--radius); border-left: 2px solid var(--border-light); }
.comment-header { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem; }
.comment-avatar {
  width: 24px; height: 24px;
  background: var(--accent-dim); border: 1px solid var(--accent);
  border-radius: 50%; display: flex; align-items: center; justify-content: center;
  font-size: 0.7rem; font-weight: 700; color: var(--accent); flex-shrink: 0;
}
.comment-meta { display: flex; flex-direction: column; }
.comment-author { font-size: 0.8rem; font-weight: 600; }
.comment-time { font-size: 0.7rem; color: var(--text-muted); font-family: var(--font-mono); }
.comment-body { font-size: 0.8rem; color: var(--text-secondary); line-height: 1.5; white-space: pre-wrap; }
.comment-textarea { resize: vertical; font-family: var(--font-sans); }
.danger-card { border-color: #ff4d6a33; }
</style>
