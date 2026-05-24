(function () {
  const svgNS = 'http://www.w3.org/2000/svg';
  const config = window.SAAI_MAP_CONFIG;
  const api = window.SAAIMapAPI;
  const state = {
    tool: 'select',
    features: [],
    selectedId: null,
    draftPoints: [],
    calibration: config.calibrationJson || {},
    loupe: false,
    zoom: 1,
    pan: { x: 0, y: 0 },
  };

  const elements = {};
  let saveTimer = null;

  function $(id) {
    return document.getElementById(id);
  }

  function stagePoint(event) {
    const rect = elements.overlay.getBoundingClientRect();
    return {
      x: Math.round(((event.clientX - rect.left) / rect.width) * 10000) / 100,
      y: Math.round(((event.clientY - rect.top) / rect.height) * 10000) / 100,
    };
  }

  function distance(a, b) {
    const dx = a.x - b.x;
    const dy = a.y - b.y;
    return Math.round(Math.sqrt(dx * dx + dy * dy) * 100) / 100;
  }

  function featureProjectJson() {
    return {
      version: 1,
      features: state.features.map((feature) => ({
        id: feature.id,
        name: feature.name,
        feature_type: feature.feature_type,
        category: feature.category,
        icse_force: feature.icse_force,
        geometry: feature.geometry,
        style: feature.style,
        properties: feature.properties,
        tags: feature.tags,
      })),
      filters: {
        category: $('feature-filter').value,
        icse_force: $('force-filter').value,
      },
    };
  }

  function setStatus(message) {
    $('save-status').textContent = message;
  }

  function debounceSave() {
    window.clearTimeout(saveTimer);
    saveTimer = window.setTimeout(saveProject, 800);
  }

  async function saveProject() {
    try {
      setStatus('Saving...');
      await api.saveProject(featureProjectJson(), state.calibration);
      setStatus('Saved');
    } catch (error) {
      setStatus('Save failed');
    }
  }

  function selectedFeature() {
    return state.features.find((feature) => feature.id === state.selectedId) || null;
  }

  function setSelected(featureId) {
    state.selectedId = featureId;
    fillInspector();
    render();
  }

  function featureColor(feature) {
    if (feature.style && feature.style.color) return feature.style.color;
    if (feature.feature_type === 'polygon') return '#2f9e44';
    if (feature.feature_type === 'line' || feature.feature_type === 'measure') return '#c92a2a';
    return '#254edb';
  }

  function makeSvgElement(name, attrs) {
    const node = document.createElementNS(svgNS, name);
    Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, value));
    return node;
  }

  function renderFeature(feature) {
    const points = (feature.geometry && feature.geometry.points) || [];
    const color = featureColor(feature);
    let node;
    if (feature.feature_type === 'point') {
      const point = points[0] || { x: 50, y: 50 };
      node = makeSvgElement('circle', {
        cx: point.x,
        cy: point.y,
        r: 6,
        fill: color,
        stroke: '#ffffff',
        'stroke-width': 2,
      });
    } else if (feature.feature_type === 'polygon') {
      node = makeSvgElement('polygon', {
        points: points.map((point) => point.x + ',' + point.y).join(' '),
        fill: color,
        'fill-opacity': 0.24,
        stroke: color,
        'stroke-width': 0.7,
      });
    } else if (feature.feature_type === 'label') {
      const point = points[0] || { x: 50, y: 50 };
      node = makeSvgElement('text', {
        x: point.x,
        y: point.y,
        fill: color,
        'font-size': 14,
        'font-weight': 700,
      });
      node.textContent = feature.name;
    } else {
      node = makeSvgElement('polyline', {
        points: points.map((point) => point.x + ',' + point.y).join(' '),
        fill: 'none',
        stroke: color,
        'stroke-width': 0.8,
      });
    }
    node.classList.add('feature');
    if (feature.id === state.selectedId) node.classList.add('selected');
    node.dataset.featureId = feature.id;
    node.addEventListener('click', (event) => {
      event.stopPropagation();
      setSelected(feature.id);
    });
    return node;
  }

  function renderDraft() {
    if (!state.draftPoints.length) return;
    const node = makeSvgElement('polyline', {
      points: state.draftPoints.map((point) => point.x + ',' + point.y).join(' '),
      fill: 'none',
      stroke: '#111827',
      'stroke-dasharray': '2 2',
      'stroke-width': 0.6,
    });
    elements.overlay.appendChild(node);
  }

  function renderList() {
    const categoryFilter = $('feature-filter').value;
    const forceFilter = $('force-filter').value;
    const list = $('feature-list');
    list.innerHTML = '';
    state.features
      .filter((feature) => !categoryFilter || feature.category === categoryFilter)
      .filter((feature) => !forceFilter || feature.icse_force === forceFilter)
      .forEach((feature) => {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = feature.id === state.selectedId ? 'active' : '';
        button.textContent = feature.name + ' - ' + feature.feature_type;
        button.addEventListener('click', () => setSelected(feature.id));
        list.appendChild(button);
      });
  }

  function render() {
    elements.overlay.innerHTML = '';
    state.features.forEach((feature) => elements.overlay.appendChild(renderFeature(feature)));
    renderDraft();
    renderList();
  }

  function fillInspector() {
    const feature = selectedFeature();
    $('feature-id').value = feature ? feature.id : '';
    $('feature-name').value = feature ? feature.name : '';
    $('feature-category').value = feature ? feature.category : '';
    $('feature-force').value = feature ? feature.icse_force : '';
    $('feature-importance').value = feature ? feature.importance_notes : '';
    $('feature-exam').value = feature ? feature.exam_notes : '';
    $('feature-social').value = feature ? feature.social_studies_notes : '';
  }

  async function createFeature(point) {
    const type = state.tool;
    const points = state.draftPoints.concat([point]);
    if ((type === 'line' || type === 'polygon' || type === 'measure') && points.length < 2) {
      state.draftPoints = points;
      render();
      return;
    }
    const feature = {
      name: type.charAt(0).toUpperCase() + type.slice(1) + ' ' + (state.features.length + 1),
      feature_type: type,
      category: type === 'point' ? 'city' : '',
      geometry: { points },
      style: {},
      properties: {},
      tags: [],
    };
    if (type === 'measure') {
      feature.properties.measurement_px = distance(points[0], points[points.length - 1]);
      $('measurement-readout').textContent = 'Measure: ' + feature.properties.measurement_px + ' px';
    }
    const result = await api.createFeature(feature);
    state.features.push(result.feature);
    state.draftPoints = [];
    setSelected(result.feature.id);
    debounceSave();
  }

  async function updateSelectedFromForm(event) {
    event.preventDefault();
    const id = $('feature-id').value;
    if (!id) return;
    const payload = {
      name: $('feature-name').value || 'Untitled feature',
      category: $('feature-category').value,
      icse_force: $('feature-force').value,
      importance_notes: $('feature-importance').value,
      exam_notes: $('feature-exam').value,
      social_studies_notes: $('feature-social').value,
    };
    const result = await api.updateFeature(id, payload);
    state.features = state.features.map((feature) => (feature.id === result.feature.id ? result.feature : feature));
    setSelected(result.feature.id);
    debounceSave();
  }

  async function deleteSelected() {
    const feature = selectedFeature();
    if (!feature) return;
    await api.deleteFeature(feature.id);
    state.features = state.features.filter((item) => item.id !== feature.id);
    state.selectedId = null;
    fillInspector();
    render();
    debounceSave();
  }

  function handleOverlayClick(event) {
    const point = stagePoint(event);
    if (state.tool === 'select') {
      setSelected(null);
      return;
    }
    createFeature(point).catch((error) => setStatus(error.message));
  }

  function handlePointerMove(event) {
    const point = stagePoint(event);
    $('coordinate-readout').textContent = 'x: ' + point.x + ', y: ' + point.y;
    if (state.loupe) {
      const loupe = $('map-loupe');
      loupe.hidden = false;
      loupe.style.left = event.offsetX - 65 + 'px';
      loupe.style.top = event.offsetY - 65 + 'px';
    }
  }

  function setTool(tool) {
    state.tool = tool;
    state.draftPoints = [];
    document.querySelectorAll('[data-tool]').forEach((button) => {
      button.classList.toggle('active', button.dataset.tool === tool);
    });
    render();
  }

  function exportJson() {
    const blob = new Blob([JSON.stringify(featureProjectJson(), null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    window.open(url, '_blank', 'noopener');
  }

  function applyTransform() {
    const transform = 'translate(' + state.pan.x + 'px, ' + state.pan.y + 'px) scale(' + state.zoom + ')';
    elements.image.style.transform = transform;
    elements.overlay.style.transform = transform;
  }

  function importJson(file) {
    const reader = new FileReader();
    reader.addEventListener('load', () => {
      try {
        const data = JSON.parse(reader.result);
        if (Array.isArray(data.features)) {
          state.features = data.features;
          render();
          debounceSave();
          setStatus('Imported JSON');
        }
      } catch (error) {
        setStatus('Import failed');
      }
    });
    reader.readAsText(file);
  }

  function initializeImage() {
    if (!config.mapImageUrl) return;
    elements.image.src = config.mapImageUrl;
    elements.image.hidden = false;
    $('map-placeholder').hidden = true;
  }

  async function initializeFeatures() {
    const response = await api.listFeatures();
    state.features = response.features;
    if (!state.features.length && config.initialProjectJson && Array.isArray(config.initialProjectJson.features)) {
      state.features = config.initialProjectJson.features;
    }
    render();
  }

  function bindEvents() {
    elements.overlay.addEventListener('click', handleOverlayClick);
    elements.overlay.addEventListener('mousemove', handlePointerMove);
    elements.overlay.addEventListener('mouseleave', () => {
      $('map-loupe').hidden = true;
    });
    document.querySelectorAll('[data-tool]').forEach((button) => {
      button.addEventListener('click', () => setTool(button.dataset.tool));
    });
    document.querySelector('[data-map-action="save"]').addEventListener('click', saveProject);
    document.querySelector('[data-map-action="delete-feature"]').addEventListener('click', () => {
      deleteSelected().catch((error) => setStatus(error.message));
    });
    document.querySelector('[data-map-action="calibrate"]').addEventListener('click', () => {
      state.calibration = { mode: 'four_point', updated_at: new Date().toISOString() };
      setStatus('Calibration marker saved');
      debounceSave();
    });
    document.querySelector('[data-map-action="loupe"]').addEventListener('click', () => {
      state.loupe = !state.loupe;
      $('map-loupe').hidden = !state.loupe;
    });
    document.querySelector('[data-map-action="zoom-in"]').addEventListener('click', () => {
      state.zoom = Math.min(3, Math.round((state.zoom + 0.2) * 10) / 10);
      applyTransform();
    });
    document.querySelector('[data-map-action="zoom-out"]').addEventListener('click', () => {
      state.zoom = Math.max(0.6, Math.round((state.zoom - 0.2) * 10) / 10);
      applyTransform();
    });
    document.querySelector('[data-map-action="export-json"]').addEventListener('click', exportJson);
    document.querySelector('[data-map-action="import-json"]').addEventListener('click', () => {
      $('json-import').click();
    });
    $('json-import').addEventListener('change', (event) => {
      if (event.target.files.length) importJson(event.target.files[0]);
      event.target.value = '';
    });
    $('feature-filter').addEventListener('change', render);
    $('force-filter').addEventListener('change', render);
    $('feature-form').addEventListener('submit', (event) => {
      updateSelectedFromForm(event).catch((error) => setStatus(error.message));
    });
    $('photo-form').addEventListener('submit', (event) => {
      event.preventDefault();
      window.SAAIUploadManager.uploadSelectedFeaturePhoto(state.selectedId)
        .then(() => api.listFeatures())
        .then((response) => {
          state.features = response.features;
          render();
          setStatus('Photo uploaded');
        })
        .catch((error) => setStatus(error.message));
    });
    $('note-form').addEventListener('submit', (event) => {
      event.preventDefault();
      if (!state.selectedId) return setStatus('Select a feature first');
      api.addNote(state.selectedId, {
        note_type: $('note-type').value,
        body: $('note-body').value,
      })
        .then(() => {
          $('note-body').value = '';
          setStatus('Note added');
        })
        .catch((error) => setStatus(error.message));
    });
    document.querySelectorAll('[data-ai-action]').forEach((button) => {
      button.addEventListener('click', () => {
        window.SAAIAIPanel.run(button.dataset.aiAction, state.selectedId)
          .then((result) => {
            $('ai-output').textContent = JSON.stringify(result, null, 2);
          })
          .catch((error) => {
            $('ai-output').textContent = error.message;
          });
      });
    });
    window.addEventListener('keydown', (event) => {
      if (event.ctrlKey && event.key.toLowerCase() === 's') {
        event.preventDefault();
        saveProject();
      }
      if (event.ctrlKey && event.key.toLowerCase() === 'e') {
        event.preventDefault();
        exportJson();
      }
      if (event.key === 'Escape') {
        state.draftPoints = [];
        render();
      }
      if (event.key === 'ArrowLeft') state.pan.x += 10;
      if (event.key === 'ArrowRight') state.pan.x -= 10;
      if (event.key === 'ArrowUp') state.pan.y += 10;
      if (event.key === 'ArrowDown') state.pan.y -= 10;
      if (event.key.startsWith('Arrow')) applyTransform();
    });
  }

  function init() {
    elements.stage = $('map-stage');
    elements.image = $('map-image');
    elements.overlay = $('map-overlay');
    elements.overlay.setAttribute('viewBox', '0 0 100 100');
    initializeImage();
    bindEvents();
    initializeFeatures().catch((error) => setStatus(error.message));
  }

  document.addEventListener('DOMContentLoaded', init);
})();
