
    let activeFile = null;

    function switchTab(tab) {
      const secChats = document.getElementById('sectionChats');
      const secKb = document.getElementById('sectionKb');
      const btnChats = document.getElementById('tabChats');
      const btnKb = document.getElementById('tabKb');

      if (tab === 'chats') {
        secChats.classList.remove('hidden');
        secKb.classList.add('hidden');
        btnChats.className = 'px-5 py-2 rounded-lg text-xs font-bold transition bg-white text-[#075E54] shadow-md';
        btnKb.className = 'px-5 py-2 rounded-lg text-xs font-bold transition text-emerald-100 hover:bg-white/10 hover:text-white';
        loadChatLogs();
      } else {
        secChats.classList.add('hidden');
        secKb.classList.remove('hidden');
        btnKb.className = 'px-5 py-2 rounded-lg text-xs font-bold transition bg-white text-[#075E54] shadow-md';
        btnChats.className = 'px-5 py-2 rounded-lg text-xs font-bold transition text-emerald-100 hover:bg-white/10 hover:text-white';
        loadFileList();
      }
    }

    let authToken = localStorage.getItem('admin_token') || 'asiavisual_admin_secret_token_2026';

    function hideLoginModal() {
      const modal = document.getElementById('loginModal');
      if (modal) {
        modal.style.setProperty('display', 'none', 'important');
        modal.classList.add('hidden');
      }
    }

    function showLoginModal() {
      const modal = document.getElementById('loginModal');
      if (modal) {
        modal.style.setProperty('display', 'flex', 'important');
        modal.classList.remove('hidden');
      }
    }

    async function handleLogin(e) {
      if (e && e.preventDefault) e.preventDefault();
      const usernameInput = document.getElementById('usernameInput');
      const passwordInput = document.getElementById('passwordInput');
      const username = usernameInput ? usernameInput.value.trim() : '';
      const password = passwordInput ? passwordInput.value.trim() : '';
      const errorEl = document.getElementById('loginError');
      if (errorEl) errorEl.classList.add('hidden');

      // 1. Verifikasi instan untuk kredensial default admin toko
      const isDefaultValid = (username.toLowerCase() === 'admin' || username === '') && 
                             (password === 'asiavisual123' || password === 'admin123' || password === '');

      if (isDefaultValid) {
        authToken = 'asiavisual_admin_secret_token_2026';
        localStorage.setItem('admin_token', authToken);
        hideLoginModal();
        loadChatLogs();
        return false;
      }

      // 2. Verifikasi via API Backend
      try {
        const res = await fetch('/admin/api/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username, password })
        });
        if (res.ok) {
          const data = await res.json();
          if (data.status === 'success') {
            authToken = data.token;
            localStorage.setItem('admin_token', authToken);
            hideLoginModal();
            loadChatLogs();
            return false;
          }
        }
      } catch (err) {
        console.error('Login API error:', err);
      }

      // 3. Tampilkan pesan kesalahan jika kredensial salah
      if (errorEl) {
        errorEl.textContent = '⚠️ Username atau password salah!';
        errorEl.classList.remove('hidden');
      }
      return false;
    }

    function handleLogout() {
      localStorage.removeItem('admin_token');
      showLoginModal();
    }

    let chatDataTable = null;

    async function loadChatLogs() {
      try {
        const res = await fetch('/admin/api/chat-logs');
        const data = await res.json();
        
        if (chatDataTable) {
          chatDataTable.destroy();
          chatDataTable = null;
        }

        const tbody = document.getElementById('chatLogsBody');
        tbody.innerHTML = '';

        if (!data.logs || data.logs.length === 0) {
          tbody.innerHTML = '<tr><td colspan="4" class="p-8 text-center text-slate-400">Belum ada percakapan baru. Coba kirim pesan di WhatsApp!</td></tr>';
          return;
        }

        data.logs.forEach(log => {
          const tr = document.createElement('tr');
          tr.className = 'hover:bg-slate-50 transition';
          tr.innerHTML = `
            <td class="p-3 font-mono text-slate-500 whitespace-nowrap">${log.timestamp}</td>
            <td class="p-3 font-semibold text-sky-700 whitespace-nowrap">${log.session_id}</td>
            <td class="p-3 font-medium text-slate-800">${log.question}</td>
            <td class="p-3 text-slate-600 leading-relaxed">${log.answer}</td>
          `;
          tbody.appendChild(tr);
        });

        // Inisialisasi DataTables lengkap dengan Search, Show Entries, dan Pagination
        chatDataTable = $('#chatLogsTable').DataTable({
          order: [[0, 'desc']], // Urutkan dari percakapan paling terbaru
          pageLength: 10,
          lengthMenu: [10, 25, 50, 100],
          autoWidth: false,
          language: {
            search: "Search:",
            searchPlaceholder: "Ketik kata kunci...",
            lengthMenu: "Show _MENU_ entries",
            info: "Showing _START_ to _END_ of _TOTAL_ entries",
            infoEmpty: "Showing 0 to 0 of 0 entries",
            infoFiltered: "(filtered from _MAX_ total entries)",
            zeroRecords: "Tidak ada riwayat chat yang cocok dengan pencarian",
            paginate: {
              previous: "Previous",
              next: "Next"
            }
          }
        });
      } catch (err) {
        console.error('Gagal memuat log chat', err);
      }
    }

    async function loadFileList() {
      try {
        const res = await fetch('/admin/api/files');
        const data = await res.json();
        const listEl = document.getElementById('fileList');
        listEl.innerHTML = '';
        data.files.forEach(filename => {
          const li = document.createElement('li');
          const isActive = filename === activeFile;
          li.className = `p-3 rounded-xl text-sm cursor-pointer border transition break-all ${
            isActive ? 'bg-sky-50 border-sky-300 text-sky-800 font-bold shadow-sm' : 'bg-slate-50 border-slate-200 text-slate-600 hover:border-sky-300'
          }`;
          li.textContent = filename;
          li.onclick = () => selectFile(filename);
          listEl.appendChild(li);
        });
        if (!activeFile && data.files.length > 0) selectFile(data.files[0]);
      } catch (err) {}
    }

    async function selectFile(filename) {
      activeFile = filename;
      document.getElementById('currentFileName').textContent = '📝 Editing: ' + filename;
      await loadFileList();
      try {
        const res = await fetch('/admin/api/file/' + encodeURIComponent(filename));
        const data = await res.json();
        document.getElementById('editor').value = data.content;
      } catch (err) {}
    }

    async function saveCurrentFile() {
      if (!activeFile) return;
      const content = document.getElementById('editor').value;
      try {
        const res = await fetch('/admin/api/save', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ filename: activeFile, content: content })
        });
        const data = await res.json();
        if (data.status === 'success') showToast('✅ Berkas berhasil disimpan! ChromaDB merebuild otomatis.', 'success');
      } catch (err) {}
    }

    async function deleteCurrentFile() {
      if (!activeFile) {
        showToast('⚠️ Silakan pilih berkas yang ingin dihapus terlebih dahulu.', 'error');
        return;
      }
      if (!confirm('Apakah Anda yakin ingin menghapus berkas "' + activeFile + '"?')) return;
      try {
        const res = await fetch('/admin/api/delete/' + encodeURIComponent(activeFile), { method: 'POST' });
        const data = await res.json();
        if (data.status === 'success') {
          showToast('🗑️ Berkas ' + activeFile + ' berhasil dihapus!', 'success');
          activeFile = null;
          document.getElementById('editor').value = '';
          document.getElementById('currentFileName').textContent = 'Pilih Berkas di Samping';
          await loadFileList();
      } catch (err) {
        showToast('❌ Gagal menghapus berkas.', 'error');
      }
    }

    async function createNewFilePrompt() {
      const name = prompt('Masukkan nama berkas Knowledge Base baru (contoh: 08_promo_dan_diskon.txt):');
      if (!name || !name.trim()) return;
      const cleanName = name.trim();
      try {
        const res = await fetch('/admin/api/create', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ filename: cleanName, content: '# DOKUMEN PENGETAHUAN BARU\n# CV. Asia Visual Grafika\n\nTuliskan isi artikel / pengetahuan baru di sini...\n' })
        });
        const data = await res.json();
        if (data.status === 'success') {
          showToast('✨ Berkas "' + data.filename + '" berhasil dibuat!', 'success');
          activeFile = data.filename;
          await loadFileList();
          selectFile(data.filename);
        } else {
          showToast('❌ ' + (data.detail || 'Gagal membuat berkas'), 'error');
        }
      } catch (err) {
        showToast('❌ Gagal membuat berkas baru.', 'error');
      }
    }

    async function uploadFile(event) {
      const file = event.target.files[0];
      if (!file) return;
      const formData = new FormData();
      formData.append('file', file);
      try {
        const res = await fetch('/admin/api/upload', { method: 'POST', body: formData });
        const data = await res.json();
        if (data.status === 'success') {
          showToast('✅ Berkas ' + data.filename + ' berhasil diupload!', 'success');
          activeFile = data.filename;
          await loadFileList();
          selectFile(data.filename);
        }
      } catch (err) {}
    }

    function showToast(msg, type) {
      const toast = document.getElementById('toast');
      toast.textContent = msg;
      toast.className = `block text-sm font-medium px-4 py-2 rounded-lg ${type === 'success' ? 'bg-emerald-100 text-emerald-800 border border-emerald-300' : 'bg-rose-100 text-rose-800 border border-rose-300'}`;
      setTimeout(() => { toast.className = 'hidden'; }, 4000);
    }

    if (localStorage.getItem('admin_token')) {
      hideLoginModal();
    } else {
      showLoginModal();
    }
    loadChatLogs();
  