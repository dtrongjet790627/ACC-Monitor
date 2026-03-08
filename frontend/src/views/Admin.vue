<template>
  <div class="admin-container">
    <!-- Top Bar -->
    <header class="admin-top-bar">
      <div class="top-left">
        <button class="cyber-btn back-btn" @click="goBack">
          <span class="btn-icon">&lt;</span>
          <span class="btn-text">DASHBOARD</span>
        </button>
        <div class="admin-title">
          <span class="title-bracket">[</span>
          <span class="title-text">ADMIN CONSOLE</span>
          <span class="title-bracket">]</span>
        </div>
      </div>
      <div class="top-right">
        <button class="cyber-btn add-btn" @click="showAddServer">
          <span class="btn-icon">+</span>
          <span class="btn-text">NEW SERVER</span>
        </button>
      </div>
    </header>

    <!-- Main Content -->
    <div class="admin-content">
      <!-- Left: Server List -->
      <div class="server-list-panel">
        <div class="panel-header">
          <span class="header-prefix">&gt;_</span>
          <span class="header-title">SERVERS</span>
          <span class="header-count">[{{ servers.length }}]</span>
        </div>
        <div class="server-list">
          <div
            v-for="(server, index) in servers"
            :key="server.id"
            class="server-list-item"
            :class="{ active: selectedServerId === server.id }"
            @click="selectServer(server)"
          >
            <div class="item-order">{{ String(index + 1).padStart(2, '0') }}</div>
            <div class="item-info">
              <div class="item-name">{{ server.name_cn || server.name }}</div>
              <div class="item-ip">{{ server.ip }}</div>
            </div>
            <div class="item-meta">
              <span class="item-os" :class="server.os">{{ server.os === 'linux' ? 'LNX' : 'WIN' }}</span>
              <span class="item-visibility" :class="{ hidden: !server.visible }" @click.stop="toggleVisibility(server)">
                {{ server.visible ? 'SHOW' : 'HIDE' }}
              </span>
            </div>
          </div>
          <div v-if="servers.length === 0" class="empty-state">
            <span>&gt;_ NO SERVERS CONFIGURED</span>
          </div>
        </div>
      </div>

      <!-- Right: Server Detail / Edit -->
      <div class="server-detail-panel">
        <template v-if="selectedServer">
          <!-- Detail Header -->
          <div class="panel-header">
            <span class="header-prefix">&gt;_</span>
            <span class="header-title">{{ isEditing ? 'EDIT' : 'DETAIL' }} // {{ selectedServer.name_cn || selectedServer.name }}</span>
            <div class="header-actions">
              <button v-if="!isEditing" class="cyber-btn-sm edit-btn" @click="startEdit">EDIT</button>
              <button v-if="!isEditing" class="cyber-btn-sm delete-btn" @click="confirmDelete">DELETE</button>
              <button v-if="isEditing" class="cyber-btn-sm save-btn" @click="saveServer">SAVE</button>
              <button v-if="isEditing" class="cyber-btn-sm cancel-btn" @click="cancelEdit">CANCEL</button>
            </div>
          </div>

          <!-- Basic Info Section -->
          <div class="detail-section">
            <div class="section-title">&gt; BASIC INFORMATION</div>
            <div class="form-grid">
              <div class="form-group">
                <label class="form-label">$ SERVER ID</label>
                <input class="cyber-input" :value="selectedServer.id" disabled />
              </div>
              <div class="form-group">
                <label class="form-label">$ NAME</label>
                <input class="cyber-input" v-model="editForm.name" :disabled="!isEditing" />
              </div>
              <div class="form-group">
                <label class="form-label">$ DISPLAY NAME</label>
                <input class="cyber-input" v-model="editForm.name_cn" :disabled="!isEditing" />
              </div>
              <div class="form-group">
                <label class="form-label">$ IP ADDRESS</label>
                <input class="cyber-input" v-model="editForm.ip" :disabled="!isEditing" />
              </div>
              <div class="form-group">
                <label class="form-label">$ OS TYPE</label>
                <select class="cyber-select" v-model="editForm.os" :disabled="!isEditing">
                  <option value="windows">Windows</option>
                  <option value="linux">Linux</option>
                </select>
              </div>
              <div class="form-group" v-if="editForm.os === 'windows'">
                <label class="form-label">$ ACC DRIVE</label>
                <input class="cyber-input" v-model="editForm.acc_drive" :disabled="!isEditing" placeholder="e.g. E" />
              </div>
              <div class="form-group">
                <label class="form-label">$ LOG PATH</label>
                <input class="cyber-input" v-model="editForm.log_path" :disabled="!isEditing" />
              </div>
              <div class="form-group">
                <label class="form-label">$ HAS ORACLE</label>
                <div class="cyber-toggle" :class="{ active: editForm.has_oracle, disabled: !isEditing }" @click="isEditing && (editForm.has_oracle = !editForm.has_oracle)">
                  <span class="toggle-track">
                    <span class="toggle-thumb"></span>
                  </span>
                  <span class="toggle-label">{{ editForm.has_oracle ? 'YES' : 'NO' }}</span>
                </div>
              </div>
              <div class="form-group">
                <label class="form-label">$ VISIBLE ON DASHBOARD</label>
                <div class="cyber-toggle" :class="{ active: editForm.visible, disabled: !isEditing }" @click="isEditing && (editForm.visible = !editForm.visible)">
                  <span class="toggle-track">
                    <span class="toggle-thumb"></span>
                  </span>
                  <span class="toggle-label">{{ editForm.visible ? 'SHOW' : 'HIDE' }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Services Section -->
          <div class="detail-section">
            <div class="section-title">
              <span>&gt; {{ editForm.os === 'linux' ? 'CONTAINERS' : 'SERVICES' }}</span>
              <button v-if="isEditing" class="cyber-btn-sm add-service-btn" @click="addService">+ ADD</button>
            </div>
            <div class="services-table">
              <div class="table-header">
                <span class="col-name">SERVICE NAME</span>
                <span class="col-display">DISPLAY NAME</span>
                <span class="col-actions" v-if="isEditing">ACTIONS</span>
              </div>
              <div class="table-body">
                <div
                  v-for="(service, index) in editForm.services"
                  :key="index"
                  class="table-row"
                >
                  <span class="col-name">
                    <input
                      v-if="isEditing"
                      class="cyber-input-inline"
                      v-model="service.service_name"
                      placeholder="service_name"
                    />
                    <span v-else>{{ service.service_name }}</span>
                  </span>
                  <span class="col-display">
                    <input
                      v-if="isEditing"
                      class="cyber-input-inline"
                      v-model="service.display_name"
                      placeholder="display_name"
                    />
                    <span v-else>{{ service.display_name }}</span>
                  </span>
                  <span class="col-actions" v-if="isEditing">
                    <button class="cyber-btn-xs delete-service-btn" @click="removeService(index)">X</button>
                  </span>
                </div>
                <div v-if="editForm.services.length === 0" class="empty-row">
                  <span>&gt;_ NO SERVICES CONFIGURED</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Processes Section (for windows) -->
          <div class="detail-section" v-if="editForm.os === 'windows'">
            <div class="section-title">
              <span>&gt; MONITORED PROCESSES</span>
              <button v-if="isEditing" class="cyber-btn-sm add-service-btn" @click="addProcess">+ ADD</button>
            </div>
            <div class="process-tags">
              <div v-for="(proc, index) in editForm.processes" :key="index" class="process-tag">
                <span class="tag-text">{{ proc }}</span>
                <button v-if="isEditing" class="tag-remove" @click="removeProcess(index)">x</button>
              </div>
              <div v-if="editForm.processes.length === 0" class="empty-row">
                <span>&gt;_ NONE</span>
              </div>
            </div>
          </div>
        </template>

        <!-- No Selection State -->
        <div v-else class="no-selection">
          <div class="no-selection-icon">&gt;_</div>
          <div class="no-selection-text">SELECT A SERVER TO VIEW DETAILS</div>
          <div class="no-selection-hint">OR CLICK [NEW SERVER] TO ADD ONE</div>
        </div>
      </div>
    </div>

    <!-- Add Server Modal -->
    <Teleport to="body">
      <div v-if="showAddModal" class="modal-overlay" @click.self="showAddModal = false">
        <div class="cyber-modal">
          <div class="modal-header">
            <span class="header-prefix">&gt;_</span>
            <span class="header-title">NEW SERVER</span>
            <button class="modal-close" @click="showAddModal = false">X</button>
          </div>
          <div class="modal-body">
            <div class="form-grid">
              <div class="form-group">
                <label class="form-label">$ SERVER ID (optional)</label>
                <input class="cyber-input" v-model="addForm.id" placeholder="Auto-generate if empty" />
              </div>
              <div class="form-group">
                <label class="form-label">$ NAME *</label>
                <input class="cyber-input" v-model="addForm.name" placeholder="e.g. DP EPS Production" />
              </div>
              <div class="form-group">
                <label class="form-label">$ DISPLAY NAME</label>
                <input class="cyber-input" v-model="addForm.name_cn" placeholder="e.g. DP_EPS" />
              </div>
              <div class="form-group">
                <label class="form-label">$ IP ADDRESS *</label>
                <input class="cyber-input" v-model="addForm.ip" placeholder="e.g. 172.17.10.xxx" />
              </div>
              <div class="form-group">
                <label class="form-label">$ OS TYPE *</label>
                <select class="cyber-select" v-model="addForm.os">
                  <option value="windows">Windows</option>
                  <option value="linux">Linux</option>
                </select>
              </div>
              <div class="form-group" v-if="addForm.os === 'windows'">
                <label class="form-label">$ ACC DRIVE</label>
                <input class="cyber-input" v-model="addForm.acc_drive" placeholder="e.g. E" />
              </div>
              <div class="form-group">
                <label class="form-label">$ LOG PATH</label>
                <input class="cyber-input" v-model="addForm.log_path" placeholder="Log file path" />
              </div>
              <div class="form-group">
                <label class="form-label">$ HAS ORACLE</label>
                <div class="cyber-toggle" :class="{ active: addForm.has_oracle }" @click="addForm.has_oracle = !addForm.has_oracle">
                  <span class="toggle-track">
                    <span class="toggle-thumb"></span>
                  </span>
                  <span class="toggle-label">{{ addForm.has_oracle ? 'YES' : 'NO' }}</span>
                </div>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button class="cyber-btn cancel-btn" @click="showAddModal = false">CANCEL</button>
            <button class="cyber-btn save-btn" @click="createServer">CREATE</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Delete Confirm Modal -->
    <Teleport to="body">
      <div v-if="showDeleteModal" class="modal-overlay" @click.self="showDeleteModal = false">
        <div class="cyber-modal cyber-modal--sm">
          <div class="modal-header modal-header--danger">
            <span class="header-prefix">[!]</span>
            <span class="header-title">CONFIRM DELETE</span>
          </div>
          <div class="modal-body">
            <p class="confirm-text">
              ARE YOU SURE YOU WANT TO DELETE SERVER
              <span class="highlight">{{ selectedServer?.name_cn || selectedServer?.name }}</span>
              ({{ selectedServer?.ip }})?
            </p>
            <p class="confirm-warning">THIS ACTION CANNOT BE UNDONE.</p>
          </div>
          <div class="modal-footer">
            <button class="cyber-btn cancel-btn" @click="showDeleteModal = false">CANCEL</button>
            <button class="cyber-btn danger-btn" @click="deleteServer">DELETE</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, reactive, inject, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()
const toast = inject('toast')

const API_BASE = '/api'

// State
const servers = ref([])
const selectedServerId = ref(null)
const selectedServer = ref(null)
const isEditing = ref(false)
const showAddModal = ref(false)
const showDeleteModal = ref(false)

// Edit form
const editForm = reactive({
  name: '',
  name_cn: '',
  ip: '',
  os: 'windows',
  acc_drive: '',
  log_path: '',
  processes: [],
  services: [],
  has_oracle: false,
  visible: true,
  sort_order: 1
})

// Add form
const addForm = reactive({
  id: '',
  name: '',
  name_cn: '',
  ip: '',
  os: 'windows',
  acc_drive: 'C',
  log_path: '',
  has_oracle: false
})

// Fetch all servers
async function fetchServers() {
  try {
    const res = await axios.get(`${API_BASE}/admin/servers`)
    if (res.data && res.data.data) {
      servers.value = res.data.data
    }
  } catch (err) {
    console.error('Failed to fetch servers:', err)
    if (toast) toast.error('Failed to load server configurations')
  }
}

// Select a server
function selectServer(server) {
  selectedServerId.value = server.id
  selectedServer.value = server
  isEditing.value = false
  populateEditForm(server)
}

// Populate edit form from server data
function populateEditForm(server) {
  editForm.name = server.name || ''
  editForm.name_cn = server.name_cn || ''
  editForm.ip = server.ip || ''
  editForm.os = server.os || 'windows'
  editForm.acc_drive = server.acc_drive || ''
  editForm.log_path = server.log_path || ''
  editForm.processes = [...(server.processes || [])]
  editForm.services = (server.services || []).map(s => ({ ...s }))
  editForm.has_oracle = server.has_oracle || false
  editForm.visible = server.visible !== false
  editForm.sort_order = server.sort_order || 1
}

// Start editing
function startEdit() {
  isEditing.value = true
}

// Cancel editing
function cancelEdit() {
  isEditing.value = false
  if (selectedServer.value) {
    populateEditForm(selectedServer.value)
  }
}

// Save server changes
async function saveServer() {
  try {
    const payload = {
      name: editForm.name,
      name_cn: editForm.name_cn,
      ip: editForm.ip,
      os: editForm.os,
      log_path: editForm.log_path,
      processes: editForm.processes,
      services: editForm.services,
      has_oracle: editForm.has_oracle,
      visible: editForm.visible,
      sort_order: editForm.sort_order
    }

    if (editForm.os === 'windows') {
      payload.acc_drive = editForm.acc_drive
    }

    const res = await axios.put(`${API_BASE}/admin/servers/${selectedServerId.value}`, payload)
    if (res.data && res.data.code === 200) {
      if (toast) toast.success(`Server ${editForm.name_cn || editForm.name} updated`)
      isEditing.value = false
      await fetchServers()
      // Re-select to refresh
      const updated = servers.value.find(s => s.id === selectedServerId.value)
      if (updated) {
        selectedServer.value = updated
        populateEditForm(updated)
      }
    }
  } catch (err) {
    console.error('Failed to save server:', err)
    if (toast) toast.error('Failed to save server configuration')
  }
}

// Toggle visibility
async function toggleVisibility(server) {
  try {
    const newVisible = !server.visible
    await axios.put(`${API_BASE}/admin/servers/${server.id}/visibility`, { visible: newVisible })
    server.visible = newVisible
    if (selectedServer.value && selectedServer.value.id === server.id) {
      editForm.visible = newVisible
    }
    if (toast) toast.info(`${server.name_cn || server.name} ${newVisible ? 'shown' : 'hidden'} on dashboard`)
  } catch (err) {
    console.error('Failed to toggle visibility:', err)
    if (toast) toast.error('Failed to update visibility')
  }
}

// Show add server modal
function showAddServer() {
  addForm.id = ''
  addForm.name = ''
  addForm.name_cn = ''
  addForm.ip = ''
  addForm.os = 'windows'
  addForm.acc_drive = 'C'
  addForm.log_path = ''
  addForm.has_oracle = false
  showAddModal.value = true
}

// Create new server
async function createServer() {
  if (!addForm.name || !addForm.ip || !addForm.os) {
    if (toast) toast.warning('Please fill in required fields (Name, IP, OS)')
    return
  }

  try {
    const payload = { ...addForm }
    if (!payload.id) delete payload.id

    const res = await axios.post(`${API_BASE}/admin/servers`, payload)
    if (res.data && res.data.code === 200) {
      if (toast) toast.success(`Server ${addForm.name_cn || addForm.name} created`)
      showAddModal.value = false
      await fetchServers()
    }
  } catch (err) {
    console.error('Failed to create server:', err)
    const msg = err.response?.data?.message || 'Failed to create server'
    if (toast) toast.error(msg)
  }
}

// Confirm delete
function confirmDelete() {
  showDeleteModal.value = true
}

// Delete server
async function deleteServer() {
  if (!selectedServerId.value) return

  try {
    const res = await axios.delete(`${API_BASE}/admin/servers/${selectedServerId.value}`)
    if (res.data && res.data.code === 200) {
      if (toast) toast.success('Server deleted')
      showDeleteModal.value = false
      selectedServerId.value = null
      selectedServer.value = null
      isEditing.value = false
      await fetchServers()
    }
  } catch (err) {
    console.error('Failed to delete server:', err)
    if (toast) toast.error('Failed to delete server')
  }
}

// Add service to list
function addService() {
  editForm.services.push({ service_name: '', display_name: '' })
}

// Remove service from list
function removeService(index) {
  editForm.services.splice(index, 1)
}

// Add process
function addProcess() {
  const name = prompt('Enter process name:')
  if (name && name.trim()) {
    editForm.processes.push(name.trim())
  }
}

// Remove process
function removeProcess(index) {
  editForm.processes.splice(index, 1)
}

// Go back to dashboard
function goBack() {
  router.push('/')
}

onMounted(() => {
  fetchServers()
})
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

$cyber-cyan: #00d4aa;
$cyber-cyan-dim: rgba(0, 212, 170, 0.6);
$cyber-red: #ff3333;
$cyber-yellow: #ffcc00;
$cyber-bg: #0a0a0a;
$cyber-bg-card: rgba(10, 12, 16, 0.95);
$cyber-border: rgba(0, 212, 170, 0.3);

.admin-container {
  position: relative;
  z-index: 10;
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: transparent;
}

// ============ Top Bar ============
.admin-top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 24px;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  border-bottom: 2px solid $cyber-border;
  flex-shrink: 0;

  &::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent 0%, $cyber-cyan 50%, transparent 100%);
    box-shadow: 0 0 20px rgba($cyber-cyan, 0.4);
  }
}

.top-left {
  display: flex;
  align-items: center;
  gap: 24px;
}

.top-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.admin-title {
  font-family: $font-mono;
  font-size: 20px;
  letter-spacing: 4px;
  color: $cyber-cyan;
  text-shadow: 0 0 10px rgba($cyber-cyan, 0.6);

  .title-bracket {
    color: rgba($cyber-cyan, 0.5);
  }
}

// ============ Buttons ============
.cyber-btn {
  font-family: $font-mono;
  font-size: 12px;
  letter-spacing: 2px;
  padding: 8px 16px;
  border: 1px solid $cyber-border;
  background: rgba($cyber-cyan, 0.08);
  color: $cyber-cyan;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 8px;
  text-transform: uppercase;

  &:hover {
    background: rgba($cyber-cyan, 0.2);
    border-color: $cyber-cyan;
    box-shadow: 0 0 15px rgba($cyber-cyan, 0.3);
  }

  .btn-icon {
    font-weight: bold;
  }
}

.back-btn {
  border-color: rgba($cyber-cyan, 0.3);
  &:hover {
    border-color: $cyber-cyan;
  }
}

.add-btn {
  background: rgba($cyber-cyan, 0.15);
  border-color: $cyber-cyan;
  &:hover {
    background: rgba($cyber-cyan, 0.3);
    box-shadow: 0 0 20px rgba($cyber-cyan, 0.4);
  }
}

.cyber-btn-sm {
  font-family: $font-mono;
  font-size: 10px;
  letter-spacing: 1px;
  padding: 4px 12px;
  border: 1px solid $cyber-border;
  background: rgba($cyber-cyan, 0.08);
  color: $cyber-cyan;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    background: rgba($cyber-cyan, 0.2);
    border-color: $cyber-cyan;
  }
}

.cyber-btn-xs {
  font-family: $font-mono;
  font-size: 10px;
  padding: 2px 8px;
  border: 1px solid rgba($cyber-red, 0.4);
  background: rgba($cyber-red, 0.1);
  color: $cyber-red;
  cursor: pointer;

  &:hover {
    background: rgba($cyber-red, 0.3);
    border-color: $cyber-red;
  }
}

.edit-btn:hover {
  background: rgba($cyber-cyan, 0.2);
}

.delete-btn {
  border-color: rgba($cyber-red, 0.4);
  color: $cyber-red;
  background: rgba($cyber-red, 0.08);
  &:hover {
    background: rgba($cyber-red, 0.2);
    border-color: $cyber-red;
  }
}

.save-btn {
  background: rgba($cyber-cyan, 0.15);
  border-color: $cyber-cyan;
  &:hover {
    background: rgba($cyber-cyan, 0.3);
    box-shadow: 0 0 15px rgba($cyber-cyan, 0.3);
  }
}

.cancel-btn {
  border-color: rgba(255, 255, 255, 0.2);
  color: rgba(255, 255, 255, 0.5);
  background: rgba(255, 255, 255, 0.05);
  &:hover {
    background: rgba(255, 255, 255, 0.1);
    color: rgba(255, 255, 255, 0.8);
  }
}

.danger-btn {
  background: rgba($cyber-red, 0.2);
  border-color: $cyber-red;
  color: $cyber-red;
  &:hover {
    background: rgba($cyber-red, 0.4);
    box-shadow: 0 0 15px rgba($cyber-red, 0.4);
  }
}

.add-service-btn {
  margin-left: auto;
}

.delete-service-btn {
  // inherits .cyber-btn-xs
}

// ============ Main Content ============
.admin-content {
  flex: 1;
  display: flex;
  padding: 20px;
  gap: 20px;
  overflow: hidden;
  min-height: 0;
}

// ============ Server List Panel ============
.server-list-panel {
  width: 320px;
  min-width: 280px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: $cyber-bg-card;
  border: 1px solid $cyber-border;
  overflow: hidden;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  border-bottom: 1px solid $cyber-border;
  font-family: $font-mono;
  font-size: 12px;
  letter-spacing: 2px;
  color: $cyber-cyan;
  flex-shrink: 0;

  .header-prefix {
    color: $cyber-cyan-dim;
  }

  .header-title {
    text-shadow: 0 0 8px rgba($cyber-cyan, 0.4);
  }

  .header-count {
    color: rgba(255, 255, 255, 0.4);
    margin-left: 4px;
  }

  .header-actions {
    margin-left: auto;
    display: flex;
    gap: 8px;
  }
}

.server-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;

  &::-webkit-scrollbar {
    width: 4px;
  }
  &::-webkit-scrollbar-track {
    background: transparent;
  }
  &::-webkit-scrollbar-thumb {
    background: rgba($cyber-cyan, 0.3);
    border-radius: 2px;
  }
}

.server-list-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  margin-bottom: 4px;
  border: 1px solid transparent;
  background: rgba(0, 0, 0, 0.3);
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: $font-mono;

  &:hover {
    border-color: rgba($cyber-cyan, 0.3);
    background: rgba($cyber-cyan, 0.05);
  }

  &.active {
    border-color: $cyber-cyan;
    background: rgba($cyber-cyan, 0.1);
    box-shadow: 0 0 10px rgba($cyber-cyan, 0.15);

    .item-order {
      color: $cyber-cyan;
      text-shadow: 0 0 8px rgba($cyber-cyan, 0.5);
    }
  }
}

.item-order {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.3);
  min-width: 24px;
}

.item-info {
  flex: 1;
  min-width: 0;
}

.item-name {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.9);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.item-ip {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.35);
  margin-top: 2px;
}

.item-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}

.item-os {
  font-size: 9px;
  padding: 1px 6px;
  letter-spacing: 1px;
  color: $cyber-cyan;
  border: 1px solid rgba($cyber-cyan, 0.3);
  background: rgba($cyber-cyan, 0.1);

  &.linux {
    color: $neon-orange;
    border-color: rgba($neon-orange, 0.3);
    background: rgba($neon-orange, 0.1);
  }
}

.item-visibility {
  font-size: 9px;
  padding: 1px 6px;
  letter-spacing: 1px;
  color: $cyber-cyan;
  border: 1px solid rgba($cyber-cyan, 0.2);
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    border-color: $cyber-cyan;
    background: rgba($cyber-cyan, 0.15);
  }

  &.hidden {
    color: rgba(255, 255, 255, 0.3);
    border-color: rgba(255, 255, 255, 0.1);
    &:hover {
      color: $cyber-yellow;
      border-color: rgba($cyber-yellow, 0.4);
      background: rgba($cyber-yellow, 0.1);
    }
  }
}

// ============ Server Detail Panel ============
.server-detail-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: $cyber-bg-card;
  border: 1px solid $cyber-border;
  overflow-y: auto;

  &::-webkit-scrollbar {
    width: 4px;
  }
  &::-webkit-scrollbar-track {
    background: transparent;
  }
  &::-webkit-scrollbar-thumb {
    background: rgba($cyber-cyan, 0.3);
    border-radius: 2px;
  }
}

// ============ Detail Sections ============
.detail-section {
  padding: 16px 20px;
  border-bottom: 1px solid rgba($cyber-cyan, 0.1);

  &:last-child {
    border-bottom: none;
  }
}

.section-title {
  font-family: $font-mono;
  font-size: 12px;
  color: $cyber-cyan;
  letter-spacing: 2px;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba($cyber-cyan, 0.2);
  text-shadow: 0 0 8px rgba($cyber-cyan, 0.3);
  display: flex;
  align-items: center;
}

// ============ Form Elements ============
.form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 14px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-label {
  font-family: $font-mono;
  font-size: 10px;
  color: rgba(255, 255, 255, 0.4);
  letter-spacing: 1px;
  text-transform: uppercase;
}

.cyber-input {
  font-family: $font-mono;
  font-size: 13px;
  padding: 8px 12px;
  background: rgba(0, 0, 0, 0.6);
  border: 1px solid rgba($cyber-cyan, 0.2);
  color: rgba(255, 255, 255, 0.9);
  outline: none;
  transition: all 0.2s ease;

  &:focus {
    border-color: $cyber-cyan;
    box-shadow: 0 0 10px rgba($cyber-cyan, 0.2);
    background: rgba(0, 0, 0, 0.8);
  }

  &:disabled {
    color: rgba(255, 255, 255, 0.5);
    border-color: rgba(255, 255, 255, 0.1);
    background: rgba(0, 0, 0, 0.3);
    cursor: default;
  }
}

.cyber-input-inline {
  font-family: $font-mono;
  font-size: 12px;
  padding: 4px 8px;
  background: rgba(0, 0, 0, 0.5);
  border: 1px solid rgba($cyber-cyan, 0.2);
  color: rgba(255, 255, 255, 0.9);
  outline: none;
  width: 100%;
  box-sizing: border-box;

  &:focus {
    border-color: $cyber-cyan;
    box-shadow: 0 0 8px rgba($cyber-cyan, 0.15);
  }
}

.cyber-select {
  font-family: $font-mono;
  font-size: 13px;
  padding: 8px 12px;
  background: rgba(0, 0, 0, 0.6);
  border: 1px solid rgba($cyber-cyan, 0.2);
  color: rgba(255, 255, 255, 0.9);
  outline: none;
  cursor: pointer;

  &:focus {
    border-color: $cyber-cyan;
    box-shadow: 0 0 10px rgba($cyber-cyan, 0.2);
  }

  &:disabled {
    color: rgba(255, 255, 255, 0.5);
    cursor: default;
  }

  option {
    background: #0a0a0a;
    color: rgba(255, 255, 255, 0.9);
  }
}

// ============ Toggle Switch ============
.cyber-toggle {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  user-select: none;

  &.disabled {
    opacity: 0.5;
    cursor: default;
  }
}

.toggle-track {
  width: 40px;
  height: 20px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: rgba(0, 0, 0, 0.5);
  position: relative;
  transition: all 0.2s ease;
}

.toggle-thumb {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 14px;
  height: 14px;
  background: rgba(255, 255, 255, 0.3);
  transition: all 0.2s ease;
}

.cyber-toggle.active {
  .toggle-track {
    border-color: $cyber-cyan;
    background: rgba($cyber-cyan, 0.15);
  }
  .toggle-thumb {
    left: 22px;
    background: $cyber-cyan;
    box-shadow: 0 0 8px rgba($cyber-cyan, 0.5);
  }
}

.toggle-label {
  font-family: $font-mono;
  font-size: 11px;
  letter-spacing: 1px;
  color: rgba(255, 255, 255, 0.5);

  .cyber-toggle.active & {
    color: $cyber-cyan;
  }
}

// ============ Services Table ============
.services-table {
  border: 1px solid rgba($cyber-cyan, 0.15);
}

.table-header {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  background: rgba($cyber-cyan, 0.06);
  border-bottom: 1px solid rgba($cyber-cyan, 0.15);
  font-family: $font-mono;
  font-size: 10px;
  color: rgba(255, 255, 255, 0.4);
  letter-spacing: 1px;
}

.table-body {
  max-height: 300px;
  overflow-y: auto;

  &::-webkit-scrollbar {
    width: 3px;
  }
  &::-webkit-scrollbar-thumb {
    background: rgba($cyber-cyan, 0.3);
  }
}

.table-row {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  font-family: $font-mono;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
  transition: background 0.15s ease;

  &:hover {
    background: rgba($cyber-cyan, 0.03);
  }

  &:last-child {
    border-bottom: none;
  }
}

.col-name {
  flex: 1;
  min-width: 0;
  padding-right: 12px;
}

.col-display {
  flex: 1;
  min-width: 0;
  padding-right: 12px;
}

.col-actions {
  width: 50px;
  text-align: center;
  flex-shrink: 0;
}

.empty-row, .empty-state {
  padding: 20px;
  text-align: center;
  font-family: $font-mono;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.25);
  letter-spacing: 1px;
}

// ============ Process Tags ============
.process-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.process-tag {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border: 1px solid rgba($cyber-cyan, 0.3);
  background: rgba($cyber-cyan, 0.08);
  font-family: $font-mono;
  font-size: 12px;
  color: $cyber-cyan;

  .tag-remove {
    font-size: 10px;
    border: none;
    background: none;
    color: $cyber-red;
    cursor: pointer;
    padding: 0 2px;
    &:hover {
      text-shadow: 0 0 5px $cyber-red;
    }
  }
}

// ============ No Selection ============
.no-selection {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  font-family: $font-mono;
  color: rgba(255, 255, 255, 0.2);
}

.no-selection-icon {
  font-size: 48px;
  color: rgba($cyber-cyan, 0.3);
  text-shadow: 0 0 20px rgba($cyber-cyan, 0.15);
}

.no-selection-text {
  font-size: 14px;
  letter-spacing: 3px;
}

.no-selection-hint {
  font-size: 11px;
  letter-spacing: 2px;
  color: rgba(255, 255, 255, 0.15);
}

// ============ Modal ============
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(4px);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
}

.cyber-modal {
  width: 600px;
  max-width: 90vw;
  max-height: 80vh;
  background: rgba(8, 10, 14, 0.98);
  border: 1px solid $cyber-cyan;
  box-shadow: 0 0 40px rgba($cyber-cyan, 0.2), 0 20px 60px rgba(0, 0, 0, 0.8);
  display: flex;
  flex-direction: column;

  &--sm {
    width: 450px;
  }
}

.modal-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 20px;
  border-bottom: 1px solid $cyber-border;
  font-family: $font-mono;
  font-size: 14px;
  letter-spacing: 2px;
  color: $cyber-cyan;
  text-shadow: 0 0 8px rgba($cyber-cyan, 0.4);

  &--danger {
    color: $cyber-red;
    border-bottom-color: rgba($cyber-red, 0.4);
    text-shadow: 0 0 8px rgba($cyber-red, 0.4);
  }
}

.modal-close {
  margin-left: auto;
  font-family: $font-mono;
  font-size: 14px;
  border: none;
  background: none;
  color: rgba(255, 255, 255, 0.4);
  cursor: pointer;
  padding: 4px 8px;

  &:hover {
    color: $cyber-red;
  }
}

.modal-body {
  padding: 20px;
  overflow-y: auto;
  flex: 1;

  &::-webkit-scrollbar {
    width: 4px;
  }
  &::-webkit-scrollbar-thumb {
    background: rgba($cyber-cyan, 0.3);
  }
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 14px 20px;
  border-top: 1px solid rgba($cyber-cyan, 0.1);
}

.confirm-text {
  font-family: $font-mono;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.7);
  line-height: 1.8;

  .highlight {
    color: $cyber-cyan;
    font-weight: bold;
  }
}

.confirm-warning {
  font-family: $font-mono;
  font-size: 11px;
  color: $cyber-red;
  margin-top: 12px;
  letter-spacing: 1px;
}

// ============ Responsive ============
@media (max-width: 1000px) {
  .admin-content {
    flex-direction: column;
  }
  .server-list-panel {
    width: 100%;
    max-height: 250px;
  }
  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
