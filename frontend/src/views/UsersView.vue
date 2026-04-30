<template>
  <div>
    <div class="page-header">
      <div>
        <h1 class="page-title">User Management</h1>
        <p class="page-subtitle">RBAC — Role-Based Access Control</p>
      </div>
      <button class="btn btn-primary" @click="showCreate = true">+ Add User</button>
    </div>

    <div v-if="!auth.isAdmin" class="card" style="color:var(--red);text-align:center;padding:2rem">
      ⚠ Admin access required to manage users.
    </div>

    <div v-else>
      <!-- Stats row -->
      <div class="grid-4" style="margin-bottom:1rem">
        <div class="stat-card" v-for="role in roleStats" :key="role.label">
          <div class="label">{{ role.label }}</div>
          <div class="value mono">{{ role.count }}</div>
          <div class="sub">{{ role.desc }}</div>
        </div>
      </div>

      <div class="card">
        <div v-if="loading" style="display:flex;justify-content:center;padding:2rem">
          <div class="loader" style="width:28px;height:28px;border-width:3px" />
        </div>
        <div class="table-wrap" v-else>
          <table v-if="users.length">
            <thead>
              <tr><th>Name</th><th>Email</th><th>Role</th><th>Status</th><th>Created</th><th>Actions</th></tr>
            </thead>
            <tbody>
              <tr v-for="u in users" :key="u.id">
                <td class="td-primary">
                  <div style="display:flex;align-items:center;gap:0.625rem">
                    <div class="mini-avatar">{{ u.name?.[0] }}</div>
                    {{ u.name }}
                  </div>
                </td>
                <td class="mono" style="font-size:0.8rem">{{ u.email }}</td>
                <td><StatusBadge :status="u.role" /></td>
                <td>
                  <span :class="u.is_active ? 'badge badge-green' : 'badge badge-gray'">
                    {{ u.is_active ? 'Active' : 'Inactive' }}
                  </span>
                </td>
                <td class="mono" style="font-size:0.75rem">{{ fmtDate(u.created_at) }}</td>
                <td>
                  <div style="display:flex;gap:0.4rem">
                    <button class="btn btn-secondary btn-sm" @click="editUser(u)">Edit</button>
                    <button
                      v-if="u.is_active && u.id !== auth.user?.id"
                      class="btn btn-danger btn-sm"
                      @click="deactivate(u)"
                    >Disable</button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
          <div v-else class="empty-state"><div class="icon">◉</div><p>No users found.</p></div>
        </div>
      </div>
    </div>

    <!-- Create User Modal -->
    <div v-if="showCreate" class="modal-overlay" @click.self="showCreate = false">
      <div class="modal">
        <h3 style="margin-bottom:1.25rem">Add New User</h3>
        <div class="field-group">
          <div class="field">
            <label class="field-label">Full Name *</label>
            <input v-model="createForm.name" class="input" placeholder="Jane Doe" />
          </div>
          <div class="field">
            <label class="field-label">Email *</label>
            <input v-model="createForm.email" type="email" class="input" placeholder="jane@company.com" />
          </div>
          <div class="field">
            <label class="field-label">Password *</label>
            <input v-model="createForm.password" type="password" class="input" placeholder="Minimum 8 characters" />
          </div>
          <div class="field">
            <label class="field-label">Role *</label>
            <select v-model="createForm.role" class="input">
              <option value="analyst">Analyst</option>
              <option value="investigator">Investigator</option>
              <option value="admin">Admin</option>
            </select>
          </div>
        </div>
        <div style="display:flex;gap:0.5rem;justify-content:flex-end;margin-top:1rem">
          <button class="btn btn-secondary" @click="showCreate = false">Cancel</button>
          <button class="btn btn-primary" @click="createUser" :disabled="creating">
            <span v-if="creating" class="loader" /> Create User
          </button>
        </div>
      </div>
    </div>

    <!-- Edit User Modal -->
    <div v-if="editModal" class="modal-overlay" @click.self="editModal = null">
      <div class="modal">
        <h3 style="margin-bottom:1.25rem">Edit User — {{ editModal.name }}</h3>
        <div class="field-group">
          <div class="field">
            <label class="field-label">Name</label>
            <input v-model="editForm.name" class="input" />
          </div>
          <div class="field">
            <label class="field-label">Role</label>
            <select v-model="editForm.role" class="input">
              <option value="analyst">Analyst</option>
              <option value="investigator">Investigator</option>
              <option value="admin">Admin</option>
            </select>
          </div>
        </div>
        <div style="display:flex;gap:0.5rem;justify-content:flex-end;margin-top:1rem">
          <button class="btn btn-secondary" @click="editModal = null">Cancel</button>
          <button class="btn btn-primary" @click="saveEdit" :disabled="saving">
            <span v-if="saving" class="loader" /> Save Changes
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/store/auth'
import { usersApi, authApi } from '@/utils/api'
import { useToast } from '@/utils/toast'
import StatusBadge from '@/components/StatusBadge.vue'

const auth = useAuthStore()
const toast = useToast()
const users = ref([])
const loading = ref(false)
const showCreate = ref(false)
const creating = ref(false)
const editModal = ref(null)
const saving = ref(false)
const createForm = ref({ name: '', email: '', password: '', role: 'analyst' })
const editForm = ref({ name: '', role: '' })

const roleStats = computed(() => {
  const counts = { admin: 0, analyst: 0, investigator: 0 }
  users.value.forEach(u => { if (u.is_active) counts[u.role] = (counts[u.role] || 0) + 1 })
  return [
    { label: 'Total Active', count: users.value.filter(u => u.is_active).length, desc: 'active accounts' },
    { label: 'Admins', count: counts.admin, desc: 'full access' },
    { label: 'Analysts', count: counts.analyst, desc: 'can upload & view' },
    { label: 'Investigators', count: counts.investigator, desc: 'can manage cases' },
  ]
})

async function load() {
  loading.value = true
  try {
    const { data } = await usersApi.list()
    users.value = data
  } catch { toast.error('Failed to load users') }
  finally { loading.value = false }
}

async function createUser() {
  if (!createForm.value.name || !createForm.value.email || !createForm.value.password) {
    toast.error('All fields are required'); return
  }
  creating.value = true
  try {
    await authApi.register(createForm.value)
    toast.success('User created successfully')
    showCreate.value = false
    createForm.value = { name: '', email: '', password: '', role: 'analyst' }
    await load()
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Failed to create user')
  } finally { creating.value = false }
}

function editUser(u) {
  editModal.value = u
  editForm.value = { name: u.name, role: u.role }
}

async function saveEdit() {
  saving.value = true
  try {
    await usersApi.update(editModal.value.id, editForm.value)
    toast.success('User updated')
    editModal.value = null
    await load()
  } catch { toast.error('Failed to update user') }
  finally { saving.value = false }
}

async function deactivate(u) {
  if (!confirm(`Disable account for ${u.name}?`)) return
  try {
    await usersApi.deactivate(u.id)
    toast.success('User disabled')
    await load()
  } catch { toast.error('Failed to disable user') }
}

function fmtDate(d) {
  return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

onMounted(load)
</script>

<style scoped>
.field-group { display: flex; flex-direction: column; gap: 0.75rem; }
.field { display: flex; flex-direction: column; gap: 0.35rem; }
.field-label { font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.07em; color: var(--text-muted); font-family: var(--font-mono); }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.6); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal { background: var(--bg-card); border: 1px solid var(--border-light); border-radius: var(--radius-lg); padding: 1.5rem; width: 460px; max-width: 90vw; box-shadow: var(--shadow); }
.mini-avatar {
  width: 28px; height: 28px; border-radius: 50%;
  background: var(--accent-dim); border: 1px solid var(--accent);
  display: flex; align-items: center; justify-content: center;
  font-size: 0.75rem; font-weight: 700; color: var(--accent);
  flex-shrink: 0; font-family: var(--font-mono);
}
</style>
