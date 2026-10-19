// DOM Elements
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const browseBtn = document.getElementById('browseBtn');
const sampleBtn = document.getElementById('sampleBtn');
const selectedFileBar = document.getElementById('selectedFileBar');
const selectedFileName = document.getElementById('selectedFileName');
const selectedFileSize = document.getElementById('selectedFileSize');
const removeFileBtn = document.getElementById('removeFileBtn');
const processBtn = document.getElementById('processBtn');

const loadingState = document.getElementById('loadingState');
const loadingMessage = document.getElementById('loadingMessage');
const errorBanner = document.getElementById('errorBanner');
const errorMessage = document.getElementById('errorMessage');
const closeErrorBtn = document.getElementById('closeErrorBtn');

const resultsSection = document.getElementById('resultsSection');
const ordersCountBadge = document.getElementById('ordersCountBadge');
const resultsFilename = document.getElementById('resultsFilename');
const copyAllTranscriptsBtn = document.getElementById('copyAllTranscriptsBtn');
const resetBtn = document.getElementById('resetBtn');
const orderTabs = document.getElementById('orderTabs');
const ordersList = document.getElementById('ordersList');

const toast = document.getElementById('toast');
const toastMessage = document.getElementById('toastMessage');

// Base API URL
// Jika halaman dibuka langsung via double-click file://, arahkan otomatis ke http://127.0.0.1:5000.
// Jika di Vercel atau dijalankan via web server, gunakan relative path /api.
const API_BASE = (window.location.protocol === 'file:' || !window.location.hostname)
  ? 'http://127.0.0.1:5000'
  : '';

// State
let currentFile = null;
let parsedOrders = [];
let toastTimeout = null;


// Initialize Event Listeners
function init() {
  browseBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    fileInput.click();
  });

  dropZone.addEventListener('click', () => {
    fileInput.click();
  });

  fileInput.addEventListener('change', handleFileSelect);

  // Drag and Drop
  ['dragenter', 'dragover'].forEach(name => {
    dropZone.addEventListener(name, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropZone.classList.add('drag-over');
    });
  });

  ['dragleave', 'drop'].forEach(name => {
    dropZone.addEventListener(name, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropZone.classList.remove('drag-over');
    });
  });

  dropZone.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files && files.length > 0) {
      handleFile(files[0]);
    }
  });

  removeFileBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    clearSelectedFile();
  });

  processBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    if (currentFile) {
      uploadAndParse(currentFile);
    }
  });

  sampleBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    loadSampleFile();
  });

  closeErrorBtn.addEventListener('click', hideError);

  resetBtn.addEventListener('click', () => {
    clearSelectedFile();
    resultsSection.classList.add('hidden');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });

  copyAllTranscriptsBtn.addEventListener('click', copyAllTranscripts);
}

function handleFileSelect(e) {
  if (e.target.files && e.target.files[0]) {
    handleFile(e.target.files[0]);
  }
}

function handleFile(file) {
  if (!file.name.toLowerCase().endsWith('.pdf')) {
    showError('Hanya file dokumen PDF (*.pdf) yang didukung.');
    return;
  }
  hideError();
  currentFile = file;
  selectedFileName.textContent = file.name;
  selectedFileSize.textContent = formatBytes(file.size);
  selectedFileBar.classList.remove('hidden');
}

function clearSelectedFile() {
  currentFile = null;
  fileInput.value = '';
  selectedFileBar.classList.add('hidden');
  hideError();
}

function formatBytes(bytes, decimals = 1) {
  if (!+bytes) return '0 Bytes';
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
}

// API Calls
async function uploadAndParse(file) {
  const formData = new FormData();
  formData.append('file', file);

  showLoading('Membaca dan memproses halaman laporan Credix...');
  hideError();

  try {
    const response = await fetch(`${API_BASE}/api/parse`, {
      method: 'POST',
      body: formData
    });

    const data = await response.json();
    hideLoading();

    if (!response.ok || !data.success) {
      showError(data.error || 'Gagal memproses file PDF.');
      return;
    }

    renderResults(data);
  } catch (err) {
    hideLoading();
    if (window.location.protocol === 'file:') {
      showError('Gagal terhubung ke API. Pastikan server lokal sudah berjalan dengan mengetik "python app.py" di terminal, atau buka web melalui URL: http://127.0.0.1:5000');
    } else {
      showError('Koneksi ke server gagal: ' + err.message);
    }
  }
}

async function loadSampleFile() {
  showLoading('Memuat dan mem-parsing dokumen contoh...');
  hideError();

  try {
    const response = await fetch(`${API_BASE}/api/sample`);
    const data = await response.json();
    hideLoading();

    if (!response.ok || !data.success) {
      showError(data.error || 'Gagal memuat file contoh.');
      return;
    }

    renderResults(data);
  } catch (err) {
    hideLoading();
    if (window.location.protocol === 'file:') {
      showError('Gagal terhubung ke API. Pastikan server lokal sudah berjalan (python app.py) di terminal, atau buka melalui http://127.0.0.1:5000');
    } else {
      showError('Gagal memuat contoh: ' + err.message);
    }
  }
}


// Rendering Results
function renderResults(data) {
  parsedOrders = data.orders || [];
  resultsFilename.textContent = data.filename || 'Dokumen PDF';
  ordersCountBadge.textContent = `${parsedOrders.length} Order Ditemukan`;

  if (parsedOrders.length === 0) {
    showError('Tidak ada data order yang terdeteksi di dalam dokumen PDF ini.');
    return;
  }

  // Render Tabs if > 1 order
  if (parsedOrders.length > 1) {
    orderTabs.classList.remove('hidden');
    orderTabs.innerHTML = parsedOrders.map((order, idx) => `
      <button type="button" class="order-tab ${idx === 0 ? 'active' : ''}" data-target="order-${idx}">
        #${idx + 1} ${escapeHtml(order.nama_toko || 'Order')}
      </button>
    `).join('');

    // Tab click listeners
    orderTabs.querySelectorAll('.order-tab').forEach((tab, index) => {
      tab.addEventListener('click', () => {
        orderTabs.querySelectorAll('.order-tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        const targetEl = document.getElementById(`order-${index}`);
        if (targetEl) {
          targetEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      });
    });
  } else {
    orderTabs.classList.add('hidden');
    orderTabs.innerHTML = '';
  }

  // Render Order Cards
  ordersList.innerHTML = parsedOrders.map((order, idx) => renderOrderCard(order, idx)).join('');

  // Attach interactive listeners (copy buttons, toggle accordion)
  attachCardEvents();

  resultsSection.classList.remove('hidden');
  resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function renderOrderCard(order, idx) {
  const otoOverlimitBadge = order.oto_overlimit ? `<span class="badge badge-oto">Oto Overlimit: ${escapeHtml(order.oto_overlimit)}</span>` : '';
  const otoOverdueBadge = order.oto_overdue ? `<span class="badge badge-overdue">Oto Overdue: ${escapeHtml(order.oto_overdue)}</span>` : '';
  const pctBadge = order.pct_overlimit_val > 0 ? `<span class="badge badge-danger">${escapeHtml(order.pct_overlimit)}</span>` : `<span class="badge badge-success">Under Limit</span>`;

  // Faktur list
  const fakturList = order.list_faktur || [];
  const hasFaktur = fakturList.length > 0;

  return `
    <article class="order-card" id="order-${idx}">
      <div class="order-card-header">
        <div class="order-title-group">
          <h2>Order #${order.order_num || (idx + 1)}: ${escapeHtml(order.nama_toko)}</h2>
          <div class="order-subtitle">Tanggal Order: <strong>${escapeHtml(order.tanggal_order)}</strong> &bull; Customer No: <strong>${escapeHtml(order.nomor_customer)}</strong></div>
          <div class="order-header-badges">
            ${pctBadge}
            ${otoOverlimitBadge}
            ${otoOverdueBadge}
          </div>
        </div>
        <div>
          <button type="button" class="btn btn-primary btn-sm btn-copy-transcript" data-transcript="${escapeAttr(order.formatted_transcript)}">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
            Salin Transkrip Order Ini
          </button>
        </div>
      </div>

      <!-- Field Grid for Copy Paste -->
      <div class="fields-grid">
        ${renderFieldItem('Tanggal Order', order.tanggal_order)}
        ${renderFieldItem('Nama Toko & STR', order.nama_toko_str || `${order.nama_toko} STR ${order.oto_overlimit || order.oto_overdue}`.trim())}
        ${renderFieldItem('Nomor Customer', order.nomor_customer)}
        ${renderFieldItem('Amount Penjualan', order.amount_penjualan)}
        ${renderFieldItem('Quantity', order.quantity)}
        ${renderFieldItem('Persentase Overlimit', order.pct_overlimit)}
        ${renderFieldItem('Overdue', order.overdue_str)}
        ${renderFieldItem('Otorisasi OverLimit', order.oto_overlimit || '-')}
        ${renderFieldItem('Otorisasi OverDue', order.oto_overdue || '-')}
        ${renderFieldItem('Total Piutang Faktur', order.total_piutang)}
        ${renderFieldItem('Limit Kredit', order.limit_kredit, true)}
      </div>

      <!-- Faktur Accordion -->
      <div class="faktur-accordion">
        <div class="faktur-header" data-toggle="faktur-${idx}">
          <h4>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
            Daftar Piutang Faktur Menggantung (${fakturList.length})
          </h4>
          <span class="faktur-count">Klik untuk ${hasFaktur ? 'lihat rincian' : 'cek'}</span>
        </div>
        <div class="faktur-content" id="faktur-${idx}">
          ${hasFaktur ? `
            <table class="faktur-table">
              <thead>
                <tr>
                  <th>No Faktur</th>
                  <th>Nominal</th>
                  <th>Jatuh Tempo</th>
                  <th>Overdue</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                ${fakturList.map(f => `
                  <tr>
                    <td><strong>${escapeHtml(f.inv)}</strong></td>
                    <td>${escapeHtml(f.nominal)}</td>
                    <td>${escapeHtml(f.due)}</td>
                    <td>${f.overdue} Hari</td>
                    <td><span class="badge ${f.is_overlimit ? 'badge-danger' : 'badge-success'}">${escapeHtml(f.status || '-')}</span></td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          ` : '<p style="color: var(--text-muted); font-size: 0.85rem;">Tidak ada faktur piutang menggantung.</p>'}
          <div class="total-piutang-row">
            <span>Total Piutang Faktur:</span>
            <span>${escapeHtml(order.total_piutang)}</span>
          </div>
        </div>
      </div>

      <!-- Raw Standard Transcript Block -->
      <div class="transcript-box">
        <div class="transcript-header">
          <span class="transcript-label">Format Standar Transkrip (WhatsApp / Report Ready)</span>
          <button type="button" class="copy-btn-mini btn-copy-field" data-copy="${escapeAttr(order.formatted_transcript)}">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
            Salin Transkrip
          </button>
        </div>
        <pre class="transcript-content">${escapeHtml(order.formatted_transcript)}</pre>
      </div>
    </article>
  `;
}

function renderFieldItem(label, value, fullWidth = false) {
  const safeVal = value || '-';
  return `
    <div class="field-item ${fullWidth ? 'full-width' : ''}">
      <div class="field-header">
        <span class="field-label">${escapeHtml(label)}</span>
        <button type="button" class="copy-btn-mini btn-copy-field" data-copy="${escapeAttr(safeVal)}" title="Salin ${escapeAttr(label)}">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
          Salin
        </button>
      </div>
      <div class="field-body">
        <span class="field-value">${escapeHtml(safeVal)}</span>
      </div>
    </div>
  `;
}

function attachCardEvents() {
  // Mini copy buttons
  document.querySelectorAll('.btn-copy-field').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const textToCopy = btn.getAttribute('data-copy');
      copyToClipboard(textToCopy, btn);
    });
  });

  // Whole transcript copy buttons
  document.querySelectorAll('.btn-copy-transcript').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const textToCopy = btn.getAttribute('data-transcript');
      copyToClipboard(textToCopy, btn, 'Transkrip order berhasil disalin!');
    });
  });

  // Toggle Faktur Accordion
  document.querySelectorAll('.faktur-header').forEach(header => {
    header.addEventListener('click', () => {
      const targetId = header.getAttribute('data-toggle');
      const content = document.getElementById(targetId);
      if (content) {
        content.classList.toggle('hidden');
      }
    });
  });
}

function copyAllTranscripts() {
  if (!parsedOrders || parsedOrders.length === 0) return;
  const fullText = parsedOrders.map(order => order.formatted_transcript).join('\n\n------------------------------------------------------------\n\n');
  copyToClipboard(fullText, copyAllTranscriptsBtn, `Semua ${parsedOrders.length} transkrip berhasil disalin!`);
}

// Clipboard helper
function copyToClipboard(text, triggerBtn = null, customMsg = null) {
  if (!text) return;

  const performFeedback = () => {
    showToast(customMsg || 'Tersalin ke clipboard!');
    if (triggerBtn) {
      const origHtml = triggerBtn.innerHTML;
      triggerBtn.classList.add('copied');
      triggerBtn.innerHTML = `
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>
        Tersalin!
      `;
      setTimeout(() => {
        triggerBtn.innerHTML = origHtml;
        triggerBtn.classList.remove('copied');
      }, 1800);
    }
  };

  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard.writeText(text)
      .then(performFeedback)
      .catch(() => fallbackCopy(text, performFeedback));
  } else {
    fallbackCopy(text, performFeedback);
  }
}

function fallbackCopy(text, callback) {
  const textarea = document.createElement('textarea');
  textarea.value = text;
  textarea.style.position = 'fixed';
  textarea.style.left = '-999999px';
  textarea.style.top = '-999999px';
  document.body.appendChild(textarea);
  textarea.focus();
  textarea.select();
  try {
    document.execCommand('copy');
    if (callback) callback();
  } catch (err) {
    showError('Gagal menyalin teks ke clipboard.');
  }
  document.body.removeChild(textarea);
}

// UI State Helpers
function showLoading(msg) {
  loadingMessage.textContent = msg || 'Sedang memproses...';
  loadingState.classList.remove('hidden');
}

function hideLoading() {
  loadingState.classList.add('hidden');
}

function showError(msg) {
  errorMessage.textContent = msg;
  errorBanner.classList.remove('hidden');
}

function hideError() {
  errorBanner.classList.add('hidden');
}

function showToast(msg) {
  toastMessage.textContent = msg;
  toast.classList.add('show');
  if (toastTimeout) clearTimeout(toastTimeout);
  toastTimeout = setTimeout(() => {
    toast.classList.remove('show');
  }, 2200);
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function escapeAttr(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', init);
