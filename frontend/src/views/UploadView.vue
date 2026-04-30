<template>
  <div>
    <div class="page-header">
      <div>
        <h1 class="page-title">Upload Transactions</h1>
        <p class="page-subtitle">CSV or JSON · Max 50MB</p>
      </div>
      <RouterLink to="/transactions" class="btn btn-secondary">← Back to Transactions</RouterLink>
    </div>

    <div class="grid-2">
      <!-- Upload zone -->
      <div class="card">
        <h3 style="margin-bottom:1rem">Select File</h3>

        <div
          class="drop-zone"
          :class="{ 'drop-active': isDragging, 'has-file': file }"
          @dragover.prevent="isDragging = true"
          @dragleave="isDragging = false"
          @drop.prevent="onDrop"
          @click="$refs.fileInput.click()"
        >
          <input ref="fileInput" type="file" accept=".csv,.json" @change="onFile" hidden />
          <div v-if="!file">
            <div class="drop-icon">↑</div>
            <p class="drop-text">Drop CSV or JSON file here</p>
            <p class="drop-hint">or click to browse</p>
          </div>
          <div v-else class="file-preview">
            <div class="file-icon">📄</div>
            <div>
              <div class="file-name">{{ file.name }}</div>
              <div class="file-size">{{ fmtSize(file.size) }}</div>
            </div>
            <button class="btn btn-secondary btn-sm" @click.stop="file = null">✕</button>
          </div>
        </div>

        <button
          class="btn btn-primary upload-btn"
          :disabled="!file || uploading"
          @click="upload"
        >
          <span v-if="uploading" class="loader" />
          <span v-else>⚡ Process & Analyze</span>
        </button>
      </div>

      <!-- Result / Format guide -->
      <div>
        <div v-if="result" class="card result-card" style="margin-bottom:1rem">
          <h3 style="margin-bottom:1rem;color:var(--accent)">✓ Upload Complete</h3>
          <div class="result-grid">
            <div class="result-item">
              <div class="result-label">Processed</div>
              <div class="result-value mono">{{ result.processed }}</div>
            </div>
            <div class="result-item" style="color:var(--red)">
              <div class="result-label">Flagged</div>
              <div class="result-value mono">{{ result.flagged }}</div>
            </div>
            <div class="result-item" style="color:var(--green)">
              <div class="result-label">Cleared</div>
              <div class="result-value mono">{{ result.processed - result.flagged - result.errors }}</div>
            </div>
            <div class="result-item" style="color:var(--yellow)">
              <div class="result-label">Errors</div>
              <div class="result-value mono">{{ result.errors }}</div>
            </div>
          </div>
          <RouterLink to="/transactions" class="btn btn-primary btn-sm" style="margin-top:1rem">
            View Transactions →
          </RouterLink>
        </div>

        <div class="card format-guide">
          <h3 style="margin-bottom:1rem">File Format Guide</h3>

          <div class="format-section">
            <div class="format-label">CSV Format</div>
            <pre class="code-block">id,timestamp,amount,merchant_id,user_id,merchant_name
txn-001,2024-01-15T14:30:00,299.99,M001,CUST001,Amazon
txn-002,2024-01-15T02:15:00,4500.00,M007,CUST002,Alibaba</pre>
          </div>

          <div class="format-section">
            <div class="format-label">JSON Format</div>
            <pre class="code-block">[
  {
    "id": "txn-001",
    "timestamp": "2024-01-15T14:30:00",
    "amount": 299.99,
    "merchant_id": "M001",
    "merchant_name": "Amazon",
    "user_id": "CUST001",
    "features": {
      "is_online": true,
      "is_foreign": false,
      "num_txn_last_24h": 2
    }
  }
]</pre>
          </div>

          <div class="feature-list">
            <div class="feature-item" v-for="f in featureList" :key="f.name">
              <span class="mono" style="color:var(--accent)">{{ f.name }}</span>
              <span>{{ f.desc }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { RouterLink } from 'vue-router'
import { transactionsApi } from '@/utils/api'
import { useToast } from '@/utils/toast'

const toast = useToast()
const file = ref(null)
const isDragging = ref(false)
const uploading = ref(false)
const result = ref(null)

const featureList = [
  { name: 'is_online', desc: 'Boolean — online transaction' },
  { name: 'is_foreign', desc: 'Boolean — foreign card/IP' },
  { name: 'num_txn_last_24h', desc: 'Integer — recent transaction count' },
  { name: 'avg_txn_amount_30d', desc: 'Float — customer 30-day average' },
  { name: 'distance_from_home', desc: 'Float — km from usual location' },
  { name: 'customer_age_days', desc: 'Integer — account age in days' },
]

function onFile(e) { file.value = e.target.files[0] || null }
function onDrop(e) {
  isDragging.value = false
  file.value = e.dataTransfer.files[0] || null
}
function fmtSize(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1048576).toFixed(1)} MB`
}

async function upload() {
  if (!file.value) return
  uploading.value = true
  result.value = null
  try {
    const { data } = await transactionsApi.upload(file.value)
    result.value = data
    toast.success(`Processed ${data.processed} transactions · ${data.flagged} flagged`)
    file.value = null
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Upload failed')
  } finally { uploading.value = false }
}
</script>

<style scoped>
.drop-zone {
  border: 2px dashed var(--border-light);
  border-radius: var(--radius-lg);
  padding: 2.5rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 1rem;
  min-height: 160px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.drop-zone:hover, .drop-active { border-color: var(--accent); background: var(--accent-dim); }
.has-file { border-color: var(--accent); border-style: solid; }
.drop-icon { font-size: 2.5rem; color: var(--text-muted); margin-bottom: 0.75rem; font-family: var(--font-mono); }
.drop-text { font-size: 0.9rem; font-weight: 500; }
.drop-hint { font-size: 0.8rem; color: var(--text-muted); margin-top: 0.3rem; }
.file-preview { display: flex; align-items: center; gap: 1rem; }
.file-icon { font-size: 2rem; }
.file-name { font-weight: 600; font-size: 0.9rem; }
.file-size { font-size: 0.75rem; color: var(--text-muted); margin-top: 0.2rem; font-family: var(--font-mono); }
.upload-btn { width: 100%; justify-content: center; padding: 0.875rem; }
.result-card { border-color: var(--accent); }
.result-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
.result-item { text-align: center; }
.result-label { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text-muted); font-family: var(--font-mono); }
.result-value { font-size: 2rem; font-weight: 700; font-family: var(--font-mono); }
.format-section { margin-bottom: 1rem; }
.format-label { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text-muted); font-family: var(--font-mono); margin-bottom: 0.4rem; }
.code-block {
  background: var(--bg-primary);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 0.75rem;
  font-family: var(--font-mono);
  font-size: 0.7rem;
  color: var(--accent);
  overflow-x: auto;
  white-space: pre;
  line-height: 1.6;
}
.feature-list { display: flex; flex-direction: column; gap: 0.4rem; margin-top: 0.75rem; border-top: 1px solid var(--border); padding-top: 0.75rem; }
.feature-item { display: flex; align-items: flex-start; gap: 0.75rem; font-size: 0.8rem; color: var(--text-secondary); }
</style>
