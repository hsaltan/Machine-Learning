(() => {
  const $ = (s, o=document) => o.querySelector(s);
  const $$ = (s, o=document) => [...o.querySelectorAll(s)];

  const yearEl = $('#year');
  if (yearEl) yearEl.textContent = new Date().getFullYear();

  const input = $('#fileInput');
  const btn = $('#uploadBtn');
  const status = $('#status');
  const progress = $('#progress');
  const bar = progress ? progress.querySelector('.bar') : null;
  const preview = $('#preview');

  const bytesToSize = (bytes) => {
    if (!bytes && bytes !== 0) return '';
    const sizes = ['B','KB','MB','GB'];
    if (bytes === 0) return '0 B';
    const i = Math.floor(Math.log(bytes)/Math.log(1024));
    return `${(bytes/Math.pow(1024,i)).toFixed(i ? 1 : 0)} ${sizes[i]}`;
  };

  const resetUI = () => {
    if (status) { status.hidden = true; status.textContent = ''; }
    if (progress) { progress.hidden = true; if (bar) bar.style.width = '0'; }
    if (preview) { preview.hidden = true; preview.removeAttribute('src'); preview.load?.(); }
  };

  const simulateProgress = (cb) => {
    if (!progress || !bar) { cb?.(); return; }
    progress.hidden = false;
    // Restart animation
    bar.style.width = '0';
    // Force reflow
    void bar.offsetWidth;
    bar.style.animation = 'none';
    // Re-trigger keyframes with timeout to ensure style flush
    setTimeout(() => {
      bar.style.animation = '';
      bar.style.animation = 'load 1.8s ease-out forwards';
    }, 20);
    setTimeout(() => cb?.(), 1900);
  };

  const onFiles = (files) => {
    resetUI();
    if (!files || !files.length) return;
    const file = files[0];

    // Basic validation
    if (!/^video\//.test(file.type)) {
      status.hidden = false;
      status.textContent = 'Please choose a video file.';
      return;
    }

    status.hidden = false;
    status.textContent = `Uploading ${file.name} (${bytesToSize(file.size)})…`;

    simulateProgress(() => {
      status.textContent = 'Uploaded! Generating your mini‑doc (demo)…';
      setTimeout(() => {
        status.textContent = 'All set! Preview your clip below (local preview only).';
        const url = URL.createObjectURL(file);
        preview.src = url;
        preview.hidden = false;
        // Revoke URL when video unloads
        preview.onended = preview.onpause = () => {
          // Keep URL until user leaves or resets; safe to keep for preview session
        };
      }, 700);
    });
  };

  btn?.addEventListener('click', () => input?.click());
  input?.addEventListener('change', (e) => onFiles(e.target.files));

  // Optional: keyboard paste of file (mobile unlikely, but harmless)
  document.addEventListener('paste', (e) => {
    const items = e.clipboardData?.files;
    if (items && items.length) onFiles(items);
  });
})();
