// Diagram Design Studio Application Logic

(function() {
  const state = {
    types: [],
    categories: [],
    selectedType: 'architecture',
    selectedTheme: 'light',
    selectedCategory: 'all',
    searchQuery: '',
    currentEditorContent: '',
  };

  // DOM Elements
  const navBtns = document.querySelectorAll('.nav-btn');
  const views = document.querySelectorAll('.view');
  const typeSearch = document.getElementById('type-search');
  const categoryFilters = document.getElementById('category-filters');
  const typeList = document.getElementById('type-list');
  const variantSelect = document.getElementById('variant-select');

  // Stage Elements
  const stageEyebrow = document.getElementById('stage-eyebrow');
  const stageTitle = document.getElementById('stage-title');
  const stageDesc = document.getElementById('stage-desc');
  const galleryIframe = document.getElementById('gallery-iframe');

  // Stage Buttons
  const btnOpenInEditor = document.getElementById('btn-open-in-editor');
  const btnOpenNewTab = document.getElementById('btn-open-new-tab');
  const btnGalleryExportSvg = document.getElementById('btn-gallery-export-svg');
  const btnGalleryExportPng = document.getElementById('btn-gallery-export-png');
  const btnExportQuickSvg = document.getElementById('btn-export-quick-svg');
  const btnExportQuickPng = document.getElementById('btn-export-quick-png');

  // Studio Elements
  const templateSelect = document.getElementById('template-select');
  const codeEditor = document.getElementById('code-editor');
  const studioIframe = document.getElementById('studio-iframe');
  const btnCheckCode = document.getElementById('btn-check-code');
  const statusIndicator = document.getElementById('status-indicator');
  const checkSummary = document.getElementById('check-summary');
  const errorList = document.getElementById('error-list');
  const btnStudioDownloadHtml = document.getElementById('btn-studio-download-html');
  const btnStudioDownloadSvg = document.getElementById('btn-studio-download-svg');
  const btnStudioDownloadPng = document.getElementById('btn-studio-download-png');

  // Converter Elements
  const mermaidInput = document.getElementById('mermaid-input');
  const btnAnalyzeMermaid = document.getElementById('btn-analyze-mermaid');
  const btnConvertToEditorial = document.getElementById('btn-convert-to-editorial');
  const irDigestDisplay = document.getElementById('ir-digest-display');

  // Doctor Elements
  const doctorTbody = document.getElementById('doctor-tbody');
  const btnRefreshDoctor = document.getElementById('btn-refresh-doctor');
  const toast = document.getElementById('toast');

  // Utilities
  function showToast(msg) {
    toast.textContent = msg;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 3500);
  }

  function downloadFile(content, filename, mimeType) {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  function downloadBase64(dataUrl, filename) {
    const a = document.createElement('a');
    a.href = dataUrl;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  }

  // View Navigation
  function switchView(viewName) {
    navBtns.forEach(btn => {
      btn.classList.toggle('active', btn.dataset.view === viewName);
    });
    views.forEach(v => {
      v.classList.toggle('active', v.id === `view-${viewName}`);
    });

    if (viewName === 'doctor') {
      fetchDoctor();
    }
  }

  navBtns.forEach(btn => {
    btn.addEventListener('click', () => switchView(btn.dataset.view));
  });

  // Calculate Asset Filename for a Type and Variant
  function getAssetFilename(typeId, variant) {
    const dtype = state.types.find(t => t.id === typeId);
    const stem = dtype ? dtype.example_stem : `example-${typeId}`;
    let suffix = '';

    if (variant === 'dark') suffix = '-dark';
    else if (variant === 'full') suffix = '-full';
    else if (variant === 'animated') suffix = '-animated';
    else if (variant === 'terminal') suffix = '-terminal';

    return `${stem}${suffix}.html`;
  }

  // Update Variant Dropdown based on selected type's available variants
  function updateVariantOptions() {
    const dtype = state.types.find(t => t.id === state.selectedType);
    const available = dtype && dtype.variants ? dtype.variants : ['light', 'dark', 'full'];

    // If current theme is not supported by this type, reset to 'light'
    if (!available.includes(state.selectedTheme)) {
      state.selectedTheme = 'light';
    }

    variantSelect.innerHTML = '';
    const variantLabels = {
      'light': 'Minimal Light',
      'dark': 'Minimal Dark',
      'full': 'Full Editorial',
      'animated': 'Motion (Animated)',
      'terminal': 'Terminal Dark'
    };

    available.forEach(v => {
      const opt = document.createElement('option');
      opt.value = v;
      opt.textContent = variantLabels[v] || v;
      if (v === state.selectedTheme) opt.selected = true;
      variantSelect.appendChild(opt);
    });
  }

  // Update Gallery Stage
  function updateGalleryStage() {
    const dtype = state.types.find(t => t.id === state.selectedType);
    if (!dtype) return;

    updateVariantOptions();

    stageEyebrow.textContent = `${dtype.name} · Diagram Design`;
    stageTitle.textContent = dtype.name;
    stageDesc.textContent = dtype.description;

    const filename = getAssetFilename(dtype.id, state.selectedTheme);
    const assetUrl = `/assets/${filename}`;

    galleryIframe.src = assetUrl;
    btnOpenNewTab.onclick = () => window.open(assetUrl, '_blank');
  }

  // Render Sidebar
  function renderSidebar() {
    // Categories
    categoryFilters.innerHTML = '';
    const allPill = document.createElement('button');
    allPill.className = `cat-pill ${state.selectedCategory === 'all' ? 'active' : ''}`;
    allPill.textContent = 'All (44)';
    allPill.onclick = () => {
      state.selectedCategory = 'all';
      renderSidebar();
    };
    categoryFilters.appendChild(allPill);

    state.categories.forEach(cat => {
      const pill = document.createElement('button');
      pill.className = `cat-pill ${state.selectedCategory === cat ? 'active' : ''}`;
      pill.textContent = cat;
      pill.onclick = () => {
        state.selectedCategory = cat;
        renderSidebar();
      };
      categoryFilters.appendChild(pill);
    });

    // Types List
    typeList.innerHTML = '';
    const filtered = state.types.filter(t => {
      const matchCat = state.selectedCategory === 'all' || t.category === state.selectedCategory;
      const matchSearch = !state.searchQuery ||
        t.name.toLowerCase().includes(state.searchQuery.toLowerCase()) ||
        t.description.toLowerCase().includes(state.searchQuery.toLowerCase());
      return matchCat && matchSearch;
    });

    filtered.forEach(t => {
      const item = document.createElement('div');
      item.className = `type-item ${t.id === state.selectedType ? 'active' : ''}`;
      item.innerHTML = `
        <div class="type-item-top">
          <span class="type-item-title">${t.name}</span>
          <span class="type-item-cat">${t.category.split(' ')[0]}</span>
        </div>
        <div class="type-item-desc">${t.description}</div>
      `;
      item.onclick = () => {
        state.selectedType = t.id;
        document.querySelectorAll('.type-item').forEach(el => el.classList.remove('active'));
        item.classList.add('active');
        updateGalleryStage();
      };
      typeList.appendChild(item);
    });
  }

  // Populate Templates in Studio
  function populateStudioTemplates() {
    templateSelect.innerHTML = '';
    state.types.forEach(t => {
      const opt = document.createElement('option');
      opt.value = t.id;
      opt.textContent = `${t.name} (${t.category})`;
      templateSelect.appendChild(opt);
    });

    templateSelect.value = state.selectedType;
  }

  // Load Template into Studio
  async function loadTemplateIntoStudio(typeId, theme = 'light') {
    try {
      const res = await fetch(`/api/template?type=${typeId}&theme=${theme}&canonical=true`);
      const data = await res.json();
      codeEditor.value = data.html;
      updateStudioPreview();
      runSelfCheck();
    } catch (err) {
      showToast(`Error loading template: ${err.message}`);
    }
  }

  // Update Studio Live Preview
  let previewDebounce = null;
  function updateStudioPreview() {
    clearTimeout(previewDebounce);
    previewDebounce = setTimeout(() => {
      const html = codeEditor.value;
      studioIframe.srcdoc = html;
      runSelfCheck();
    }, 300);
  }

  // Run Self-Check
  async function runSelfCheck() {
    const html = codeEditor.value;
    if (!html.trim()) return;

    try {
      const res = await fetch('/api/check', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ html }),
      });
      const data = await res.json();

      if (data.ok) {
        statusIndicator.className = 'status-indicator';
        checkSummary.className = 'check-status ok';
        checkSummary.textContent = '✓ Self-Check Passed: compliant with accessible SVG & Diagram Design rules.';
        errorList.innerHTML = '';
      } else {
        statusIndicator.className = 'status-indicator error';
        checkSummary.className = 'check-status error';
        checkSummary.textContent = `✗ Self-Check Issues (${data.errors.length}):`;
        errorList.innerHTML = data.errors.map(e => `<li>${e}</li>`).join('');
      }
    } catch (err) {
      console.error(err);
    }
  }

  // Fetch Doctor Diagnostics
  async function fetchDoctor() {
    doctorTbody.innerHTML = '<tr><td colspan="4">Running diagnostics...</td></tr>';
    try {
      const res = await fetch('/api/doctor');
      const data = await res.json();

      doctorTbody.innerHTML = data.checks.map(c => `
        <tr>
          <td><span class="status-badge ${c.status.toLowerCase()}">${c.status}</span></td>
          <td><strong>${c.name}</strong></td>
          <td>${c.message}</td>
          <td>${c.recommendation || '—'}</td>
        </tr>
      `).join('');
    } catch (err) {
      doctorTbody.innerHTML = `<tr><td colspan="4">Error loading doctor: ${err.message}</td></tr>`;
    }
  }

  // Export from current editor
  async function exportStudioSvg() {
    const html = codeEditor.value;
    const typeObj = state.types.find(t => t.id === templateSelect.value);
    const title = typeObj ? typeObj.name : 'diagram';

    showToast('Exporting standalone SVG...');
    try {
      const res = await fetch('/api/export/svg', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ html, title }),
      });
      const data = await res.json();
      if (data.ok) {
        downloadFile(data.svg, data.filename, 'image/svg+xml');
        showToast(`Downloaded ${data.filename}`);
      } else {
        showToast(`Export error: ${data.error}`);
      }
    } catch (err) {
      showToast(`Export error: ${err.message}`);
    }
  }

  async function exportStudioPng() {
    const html = codeEditor.value;
    const typeObj = state.types.find(t => t.id === templateSelect.value);
    const title = typeObj ? typeObj.name : 'diagram';

    showToast('Rendering high-res PNG (Playwright)...');
    try {
      const res = await fetch('/api/export/png', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ html, title, scale: 2 }),
      });
      const data = await res.json();
      if (data.ok) {
        downloadBase64(data.png_base64, data.filename);
        showToast(`Downloaded ${data.filename} (${Math.round(data.size_bytes / 1024)} KB)`);
      } else {
        showToast(`PNG error: ${data.error}`);
      }
    } catch (err) {
      showToast(`PNG error: ${err.message}`);
    }
  }

  // Export current gallery diagram
  async function exportGallerySvg() {
    const filename = getAssetFilename(state.selectedType, state.selectedTheme);
    showToast(`Exporting ${filename} to standalone SVG...`);
    try {
      const resHtml = await fetch(`/assets/${filename}`);
      const html = await resHtml.text();
      const res = await fetch('/api/export/svg', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ html, title: state.selectedType }),
      });
      const data = await res.json();
      if (data.ok) {
        downloadFile(data.svg, `${state.selectedType}.svg`, 'image/svg+xml');
        showToast(`Exported ${state.selectedType}.svg`);
      } else {
        showToast(`Export error: ${data.error}`);
      }
    } catch (err) {
      showToast(`Export error: ${err.message}`);
    }
  }

  async function exportGalleryPng() {
    const filename = getAssetFilename(state.selectedType, state.selectedTheme);
    showToast(`Rendering ${filename} to hi-res PNG (2x)...`);
    try {
      const resHtml = await fetch(`/assets/${filename}`);
      const html = await resHtml.text();
      const res = await fetch('/api/export/png', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ html, title: state.selectedType, scale: 2 }),
      });
      const data = await res.json();
      if (data.ok) {
        downloadBase64(data.png_base64, `${state.selectedType}.png`);
        showToast(`Exported ${state.selectedType}.png`);
      } else {
        showToast(`PNG error: ${data.error}`);
      }
    } catch (err) {
      showToast(`PNG error: ${err.message}`);
    }
  }

  // Open Current Gallery Item in Editor
  async function openCurrentInEditor() {
    const filename = getAssetFilename(state.selectedType, state.selectedTheme);
    try {
      const res = await fetch(`/assets/${filename}`);
      const html = await res.text();
      codeEditor.value = html;
      templateSelect.value = state.selectedType;
      switchView('studio');
      updateStudioPreview();
      showToast(`Loaded ${filename} into Live Editor`);
    } catch (err) {
      showToast(`Error: ${err.message}`);
    }
  }

  // Analyze Mermaid Source
  async function analyzeMermaid() {
    const code = mermaidInput.value;
    if (!code.trim()) {
      showToast('Please enter Mermaid diagram code');
      return;
    }

    irDigestDisplay.innerHTML = '<p class="placeholder-text">Analyzing graph structure...</p>';
    try {
      const res = await fetch('/api/convert/mermaid', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code }),
      });
      const data = await res.json();
      if (data.ok) {
        const diag = data.ir.diagrams && data.ir.diagrams[0];
        const analysis = diag ? diag.analysis : {};
        const hubs = (analysis.hubs || []).map(h => `${h.label} (${h.degree})`).join(', ');

        irDigestDisplay.innerHTML = `
          <div style="margin-bottom: 1rem;">
            <h4>Analysis Summary</h4>
            <ul style="margin: 0.5rem 0 1rem 1.25rem; font-size: 0.82rem; line-height: 1.6;">
              <li><strong>Recommended Visual Type:</strong> <span style="color: var(--color-accent); font-weight: 600;">${data.suggested_type}</span></li>
              <li><strong>Nodes:</strong> ${analysis.nodes_total || 0} (${analysis.nodes_drawable || 0} drawable)</li>
              <li><strong>Edges:</strong> ${analysis.edges_total || 0} (${analysis.edges_labeled || 0} labeled)</li>
              <li><strong>Focal Hubs (Accent candidates):</strong> ${hubs || 'None'}</li>
              <li><strong>Entry Points:</strong> ${(analysis.entry_points || []).join(', ') || 'None'}</li>
            </ul>
          </div>
          <h4>Extracted Markdown Digest</h4>
          <pre>${data.digest}</pre>
        `;

        btnConvertToEditorial.onclick = () => {
          state.selectedType = data.suggested_type;
          templateSelect.value = data.suggested_type;
          loadTemplateIntoStudio(data.suggested_type, 'light');
          switchView('studio');
          showToast(`Scaffolded ${data.suggested_type} editorial diagram in Live Editor`);
        };
      } else {
        irDigestDisplay.innerHTML = `<p style="color: red;">Error: ${data.error}</p>`;
      }
    } catch (err) {
      irDigestDisplay.innerHTML = `<p style="color: red;">Error: ${err.message}</p>`;
    }
  }

  // Event Listeners
  typeSearch.addEventListener('input', e => {
    state.searchQuery = e.target.value;
    renderSidebar();
  });

  variantSelect.addEventListener('change', e => {
    state.selectedTheme = e.target.value;
    updateGalleryStage();
  });

  btnOpenInEditor.addEventListener('click', openCurrentInEditor);
  btnGalleryExportSvg.addEventListener('click', exportGallerySvg);
  btnGalleryExportPng.addEventListener('click', exportGalleryPng);
  btnExportQuickSvg.addEventListener('click', () => {
    const isStudio = document.getElementById('view-studio').classList.contains('active');
    if (isStudio) exportStudioSvg();
    else exportGallerySvg();
  });
  btnExportQuickPng.addEventListener('click', () => {
    const isStudio = document.getElementById('view-studio').classList.contains('active');
    if (isStudio) exportStudioPng();
    else exportGalleryPng();
  });

  templateSelect.addEventListener('change', e => {
    loadTemplateIntoStudio(e.target.value, state.selectedTheme);
  });

  codeEditor.addEventListener('input', updateStudioPreview);
  btnCheckCode.addEventListener('click', runSelfCheck);

  btnStudioDownloadHtml.addEventListener('click', () => {
    const typeObj = state.types.find(t => t.id === templateSelect.value);
    const title = typeObj ? typeObj.id : 'diagram';
    downloadFile(codeEditor.value, `${title}.html`, 'text/html');
  });
  btnStudioDownloadSvg.addEventListener('click', exportStudioSvg);
  btnStudioDownloadPng.addEventListener('click', exportStudioPng);

  btnAnalyzeMermaid.addEventListener('click', analyzeMermaid);
  btnRefreshDoctor.addEventListener('click', fetchDoctor);

  // Initialize
  async function init() {
    try {
      const res = await fetch('/api/types');
      const data = await res.json();
      state.types = data.types;
      state.categories = data.categories;

      renderSidebar();
      populateStudioTemplates();
      updateGalleryStage();

      // Load initial template in studio
      loadTemplateIntoStudio('architecture', 'light');
    } catch (err) {
      console.error('Initialization error:', err);
    }
  }

  init();
})();
