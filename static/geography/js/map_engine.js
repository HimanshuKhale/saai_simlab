(function () {
  const svgNS = 'http://www.w3.org/2000/svg';
  const config = window.SAAI_MAP_CONFIG;
  const api = window.SAAIMapAPI;
  const DEFAULT_INDIA_MAP_BOUNDS = config.defaultIndiaBounds || {
    minLng: 68.1,
    maxLng: 97.4,
    minLat: 6.7,
    maxLat: 37.1,
    imageContentBox: {
      xMin: 2.5,
      xMax: 97.5,
      yMin: 2.5,
      yMax: 95.0,
    },
  };
  const DEFAULT_STYLE = {
    point: {
      shape: 'circle',
      radius: 1.3,
      fillColor: '#dc2626',
      borderColor: '#ffffff',
      borderWidth: 0.5,
      opacity: 1,
      pulse: false,
    },
    label: {
      show: true,
      text: '',
      fontFamily: 'Inter',
      fontStyle: 'bold',
      fontSize: 3,
      fontColor: '#111827',
      strokeColor: '#ffffff',
      strokeWidth: 1,
      uppercase: true,
      offsetX: 1.2,
      offsetY: 0.4,
      textAlign: 'start',
    },
    line: {
      strokeColor: '#0ea5e9',
      strokeWidth: 1.5,
      strokeStyle: 'solid',
      opacity: 1,
    },
    polygon: {
      fillColor: '#16a34a',
      fillOpacity: 0.28,
      borderColor: '#166534',
      borderWidth: 1.2,
      borderStyle: 'solid',
    },
  };
  const state = {
    tool: 'select',
    features: [],
    selectedId: null,
    draftPoints: [],
    calibration: config.calibrationJson || {},
    loupe: false,
    zoom: 1,
    pan: { x: 0, y: 0 },
    currentChatId: null,
    generatedFeatureJson: null,
  };

  const elements = {};
  let saveTimer = null;
  let styleSaveTimer = null;

  function $(id) {
    return document.getElementById(id);
  }

  function stagePoint(event) {
    const rect = elements.overlay.getBoundingClientRect();
    const point = {
      x: Math.round(((event.clientX - rect.left) / rect.width) * 10000) / 100,
      y: Math.round(((event.clientY - rect.top) / rect.height) * 10000) / 100,
    };
    return addGeoToPoint(point);
  }

  function clamp(value, min, max) {
    return Math.min(max, Math.max(min, value));
  }

  function approximateIndiaGeo(point) {
    const box = DEFAULT_INDIA_MAP_BOUNDS.imageContentBox;
    const xRatio = (point.x - box.xMin) / (box.xMax - box.xMin);
    const yRatio = (point.y - box.yMin) / (box.yMax - box.yMin);
    const outside = point.x < box.xMin || point.x > box.xMax || point.y < box.yMin || point.y > box.yMax;
    const lng = DEFAULT_INDIA_MAP_BOUNDS.minLng + clamp(xRatio, 0, 1) * (DEFAULT_INDIA_MAP_BOUNDS.maxLng - DEFAULT_INDIA_MAP_BOUNDS.minLng);
    const lat = DEFAULT_INDIA_MAP_BOUNDS.maxLat - clamp(yRatio, 0, 1) * (DEFAULT_INDIA_MAP_BOUNDS.maxLat - DEFAULT_INDIA_MAP_BOUNDS.minLat);
    return {
      lat: Math.round(lat * 1000000) / 1000000,
      lng: Math.round(lng * 1000000) / 1000000,
      accuracy: 'approximate',
      calibration_mode: 'default_india_approx',
      warning: outside
        ? 'Point is outside main calibrated map content area; coordinate may be unreliable.'
        : 'Approximate coordinate for learning use.',
    };
  }

  function addGeoToPoint(point) {
    if (config.calibrationMode === 'default_india_approx') {
      return {
        ...point,
        geo: approximateIndiaGeo(point),
        grid: null,
      };
    }
    return point;
  }

  function distance(a, b) {
    const dx = a.x - b.x;
    const dy = a.y - b.y;
    return Math.round(Math.sqrt(dx * dx + dy * dy) * 100) / 100;
  }

  function featureProjectJson() {
    return {
      schema: 'saai.geography.project.v1',
      version: 1,
      project_metadata: {
        id: config.projectId,
        title: config.projectTitle,
      },
      map_metadata: config.mapMetadata || {},
      calibration_mode: config.calibrationMode || 'uncalibrated',
      calibration_warning: config.calibrationWarning || '',
      features: state.features.map((feature) => ({
        id: feature.id,
        name: feature.name,
        feature_type: feature.feature_type,
        category: feature.category,
        icse_force: feature.icse_force,
        geometry: feature.geometry,
        style: feature.style,
        properties: feature.properties,
        notes: feature.notes || [],
        photos: feature.photos || [],
        ai_outputs: feature.ai_outputs || [],
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

  function renderAiResult(result) {
    $('ai-output').textContent = JSON.stringify(result, null, 2);
    window.SAAIAIPanel.renderTransparency($('ai-transparency'), result);
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

  function normalizeStyle(style) {
    const source = style || {};
    const merged = JSON.parse(JSON.stringify(DEFAULT_STYLE));
    if (source.point) Object.assign(merged.point, source.point);
    if (source.label) Object.assign(merged.label, source.label);
    if (source.line) Object.assign(merged.line, source.line);
    if (source.polygon) Object.assign(merged.polygon, source.polygon);
    if (source.color) {
      merged.point.fillColor = source.color;
      merged.line.strokeColor = source.color;
      merged.polygon.borderColor = source.color;
    }
    if (source.radius) merged.point.radius = Number(source.radius);
    if (source.strokeWidth) {
      merged.point.borderWidth = Number(source.strokeWidth);
      merged.line.strokeWidth = Number(source.strokeWidth);
    }
    if (source.fillOpacity) merged.polygon.fillOpacity = Number(source.fillOpacity);
    if (source.labelSize) merged.label.fontSize = Number(source.labelSize);
    if (source.labelColor) merged.label.fontColor = source.labelColor;
    return merged;
  }

  function styleFromControls() {
    return {
      point: {
        shape: $('marker-shape').value,
        radius: Number($('marker-radius').value || 1.3),
        fillColor: $('marker-fill').value || '#dc2626',
        borderColor: $('marker-border').value || '#ffffff',
        borderWidth: Number($('marker-border-width').value || 0.5),
        opacity: Number($('marker-opacity').value || 1),
        pulse: $('marker-pulse').checked,
      },
      label: {
        show: $('label-show').checked,
        text: $('label-text').value,
        fontFamily: $('label-font-family').value || 'Inter',
        fontStyle: $('label-font-style').value || 'bold',
        fontSize: Number($('label-font-size').value || 3),
        fontColor: $('label-font-color').value || '#111827',
        strokeColor: $('label-stroke-color').value || '#ffffff',
        strokeWidth: Number($('label-stroke-width').value || 1),
        uppercase: $('label-uppercase').checked,
        offsetX: Number($('label-offset-x').value || 1.2),
        offsetY: Number($('label-offset-y').value || 0.4),
        textAlign: $('label-align').value || 'start',
      },
      line: {
        ...DEFAULT_STYLE.line,
        strokeColor: $('marker-fill').value || DEFAULT_STYLE.line.strokeColor,
        opacity: Number($('marker-opacity').value || 1),
      },
      polygon: {
        ...DEFAULT_STYLE.polygon,
        fillColor: $('marker-fill').value || DEFAULT_STYLE.polygon.fillColor,
      },
    };
  }

  function setSelected(featureId) {
    if (state.selectedId !== featureId) {
      state.currentChatId = null;
      if ($('chat-messages')) $('chat-messages').innerHTML = '';
    }
    state.selectedId = featureId;
    fillInspector();
    render();
  }

  function featureColor(feature) {
    const style = normalizeStyle(feature.style);
    if (feature.feature_type === 'point' || feature.feature_type === 'label') return style.point.fillColor;
    if (feature.feature_type === 'polygon') return style.polygon.borderColor;
    if (feature.feature_type === 'line' || feature.feature_type === 'measure') return style.line.strokeColor;
    return '#254edb';
  }

  function makeSvgElement(name, attrs) {
    const node = document.createElementNS(svgNS, name);
    Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, value));
    return node;
  }

  function renderFeature(feature) {
    const points = (feature.geometry && feature.geometry.points) || [];
    const style = normalizeStyle(feature.style);
    const color = featureColor(feature);
    const group = makeSvgElement('g', {});
    group.classList.add('feature');
    if (feature.id === state.selectedId) group.classList.add('selected');
    group.dataset.featureId = feature.id;
    group.addEventListener('click', (event) => {
      event.stopPropagation();
      setSelected(feature.id);
    });
    let node;
    if (feature.feature_type === 'point') {
      const point = points[0] || { x: 50, y: 50 };
      if (style.point.shape === 'square') {
        node = makeSvgElement('rect', {
          x: point.x - style.point.radius,
          y: point.y - style.point.radius,
          width: style.point.radius * 2,
          height: style.point.radius * 2,
          fill: style.point.fillColor,
          stroke: style.point.borderColor,
          'stroke-width': style.point.borderWidth,
          opacity: style.point.opacity,
        });
      } else if (style.point.shape === 'triangle') {
        const r = style.point.radius * 1.35;
        node = makeSvgElement('polygon', {
          points: `${point.x},${point.y - r} ${point.x - r},${point.y + r} ${point.x + r},${point.y + r}`,
          fill: style.point.fillColor,
          stroke: style.point.borderColor,
          'stroke-width': style.point.borderWidth,
          opacity: style.point.opacity,
        });
      } else {
        node = makeSvgElement('circle', {
          cx: point.x,
          cy: point.y,
          r: style.point.radius,
          fill: style.point.fillColor,
          stroke: style.point.borderColor,
          'stroke-width': style.point.borderWidth,
          opacity: style.point.opacity,
        });
      }
      if (style.point.pulse) node.classList.add('pulse');
      group.appendChild(node);
      if (style.label.show) group.appendChild(renderLabel(feature, point, style));
    } else if (feature.feature_type === 'polygon') {
      node = makeSvgElement('polygon', {
        points: points.map((point) => point.x + ',' + point.y).join(' '),
        fill: style.polygon.fillColor,
        'fill-opacity': style.polygon.fillOpacity,
        stroke: style.polygon.borderColor,
        'stroke-width': style.polygon.borderWidth,
      });
      group.appendChild(node);
    } else if (feature.feature_type === 'label') {
      const point = points[0] || { x: 50, y: 50 };
      node = renderLabel(feature, point, style);
      group.appendChild(node);
    } else {
      node = makeSvgElement('polyline', {
        points: points.map((point) => point.x + ',' + point.y).join(' '),
        fill: 'none',
        stroke: style.line.strokeColor,
        'stroke-width': style.line.strokeWidth,
        opacity: style.line.opacity,
      });
      group.appendChild(node);
    }
    return group;
  }

  function renderLabel(feature, point, style) {
    const label = style.label;
    const text = label.uppercase ? (label.text || feature.name).toUpperCase() : (label.text || feature.name);
    const fontWeight = label.fontStyle.includes('bold') ? '700' : '400';
    const fontStyle = label.fontStyle.includes('italic') ? 'italic' : 'normal';
    const node = makeSvgElement('text', {
      x: point.x + label.offsetX,
      y: point.y + label.offsetY,
      fill: label.fontColor,
      stroke: label.strokeColor,
      'stroke-width': label.strokeWidth,
      'paint-order': 'stroke',
      'font-size': label.fontSize,
      'font-family': label.fontFamily,
      'font-style': fontStyle,
      'font-weight': fontWeight,
      'text-anchor': label.textAlign,
    });
    node.textContent = text;
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
    const style = normalizeStyle(feature ? feature.style : {});
    const firstPoint = feature && feature.geometry && feature.geometry.points ? feature.geometry.points[0] : null;
    const geo = firstPoint && firstPoint.geo ? firstPoint.geo : null;
    $('feature-id').value = feature ? feature.id : '';
    $('feature-name').value = feature ? feature.name : '';
    $('feature-category').value = feature ? feature.category : '';
    $('feature-force').value = feature ? feature.icse_force : '';
    $('feature-tags').value = feature && Array.isArray(feature.tags) ? feature.tags.join(', ') : '';
    $('feature-importance').value = feature ? feature.importance_notes : '';
    $('feature-exam').value = feature ? feature.exam_notes : '';
    $('feature-social').value = feature ? feature.social_studies_notes : '';
    $('marker-shape').value = style.point.shape;
    $('marker-radius').value = style.point.radius;
    $('marker-fill').value = style.point.fillColor;
    $('marker-border').value = style.point.borderColor;
    $('marker-border-width').value = style.point.borderWidth;
    $('marker-opacity').value = style.point.opacity;
    $('marker-pulse').checked = Boolean(style.point.pulse);
    $('label-show').checked = Boolean(style.label.show);
    $('label-text').value = style.label.text || (feature ? feature.name : '');
    $('label-font-family').value = style.label.fontFamily;
    $('label-font-style').value = style.label.fontStyle;
    $('label-font-size').value = style.label.fontSize;
    $('label-font-color').value = style.label.fontColor;
    $('label-stroke-color').value = style.label.strokeColor;
    $('label-stroke-width').value = style.label.strokeWidth;
    $('label-uppercase').checked = Boolean(style.label.uppercase);
    $('label-offset-x').value = style.label.offsetX;
    $('label-offset-y').value = style.label.offsetY;
    $('label-align').value = style.label.textAlign;
    if (geo) {
      $('selected-coordinate-panel').textContent = `Lat ${geo.lat}, Lng ${geo.lng}. ${geo.warning || ''}`;
    } else {
      $('selected-coordinate-panel').textContent = config.calibrationMode === 'uncalibrated'
        ? 'Custom map annotation mode. Latitude/longitude unavailable.'
        : 'No coordinate selected.';
    }
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
      style: JSON.parse(JSON.stringify(DEFAULT_STYLE)),
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
    await saveSelectedFeatureFromForm();
  }

  async function saveSelectedFeatureFromForm() {
    const id = $('feature-id').value;
    if (!id) return;
    const payload = {
      name: $('feature-name').value || 'Untitled feature',
      category: $('feature-category').value,
      icse_force: $('feature-force').value,
      tags: $('feature-tags').value.split(',').map((tag) => tag.trim()).filter(Boolean),
      style: styleFromControls(),
      importance_notes: $('feature-importance').value,
      exam_notes: $('feature-exam').value,
      social_studies_notes: $('feature-social').value,
    };
    const result = await api.updateFeature(id, payload);
    state.features = state.features.map((feature) => (feature.id === result.feature.id ? result.feature : feature));
    setSelected(result.feature.id);
    debounceSave();
  }

  function updateLocalStyleFromControls() {
    const feature = selectedFeature();
    if (!feature) return;
    feature.style = styleFromControls();
    render();
    window.clearTimeout(styleSaveTimer);
    styleSaveTimer = window.setTimeout(() => {
      saveSelectedFeatureFromForm().catch((error) => setStatus(error.message));
    }, 450);
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
    let text = 'x: ' + point.x + ', y: ' + point.y;
    if (point.geo) {
      text += ' | lat: ' + point.geo.lat + ', lng: ' + point.geo.lng;
    } else if (config.calibrationMode === 'uncalibrated') {
      text += ' | annotation mode';
    }
    $('coordinate-readout').textContent = text;
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

  function renderChat(messages) {
    const wrap = $('chat-messages');
    wrap.innerHTML = '';
    messages.forEach((message) => {
      const item = document.createElement('div');
      item.className = 'chat-message';
      const role = document.createElement('strong');
      role.textContent = message.role === 'assistant' ? 'AI' : message.role;
      const content = document.createElement('div');
      content.textContent = message.content;
      item.appendChild(role);
      item.appendChild(content);
      wrap.appendChild(item);
    });
    wrap.scrollTop = wrap.scrollHeight;
  }

  async function ensureChat() {
    if (state.currentChatId) return state.currentChatId;
    if (!state.selectedId) throw new Error('Select a feature first.');
    const result = await api.startChat(state.selectedId, 'feature');
    state.currentChatId = result.chat_session_id;
    renderChat([]);
    return state.currentChatId;
  }

  async function sendChat() {
    const chatId = await ensureChat();
    const input = $('chat-input');
    const message = input.value.trim();
    if (!message) return;
    const result = await api.sendChat(chatId, message);
    input.value = '';
    const messages = await api.chatMessages(chatId);
    renderChat(messages.messages);
    window.SAAIAIPanel.renderTransparency($('ai-transparency'), result.payload || {});
  }

  function parseStylePreference() {
    const raw = $('ai-feature-style').value.trim();
    if (!raw) return {};
    try {
      return JSON.parse(raw);
    } catch (error) {
      setStatus('Style JSON is invalid; ignoring style preference');
      return {};
    }
  }

  async function generateFeatureJson() {
    const result = await api.generateFeatureJson({
      feature_type: $('ai-feature-type').value,
      name: $('ai-feature-name').value,
      force_type: $('ai-feature-force').value,
      description: $('ai-feature-description').value,
      style_preferences: parseStylePreference(),
    });
    state.generatedFeatureJson = result.feature_json;
    $('ai-feature-json').value = JSON.stringify(result.feature_json, null, 2);
    renderAiResult(result);
  }

  async function importGeneratedFeature() {
    const raw = $('ai-feature-json').value.trim();
    if (!raw) throw new Error('Generate or paste feature JSON first.');
    const featureJson = JSON.parse(raw);
    const feature = {
      name: featureJson.name || 'AI draft feature',
      feature_type: featureJson.feature_type || 'point',
      category: featureJson.category || featureJson.force_type || '',
      icse_force: featureJson.force_type || '',
      geometry: featureJson.geometry || { points: [] },
      style: normalizeStyle(featureJson.style || {}),
      properties: {
        geometry_accuracy: featureJson.geometry_accuracy || 'manual_required',
        confidence: featureJson.confidence || 'low',
        warnings: featureJson.warnings || [],
        ai_summary: featureJson.ai_summary || '',
        ai_questions: featureJson.ai_questions || [],
      },
      importance_notes: featureJson.importance || '',
      exam_notes: featureJson.exam_note || '',
      social_studies_notes: featureJson.social_studies_connection || '',
      tags: featureJson.tags || [],
    };
    const result = await api.createFeature(feature);
    state.features.push(result.feature);
    setSelected(result.feature.id);
    debounceSave();
    setStatus(feature.geometry.points && feature.geometry.points.length ? 'AI feature imported' : 'AI draft imported; place geometry manually');
  }

  function applyTransform() {
    const transform = 'translate(' + state.pan.x + 'px, ' + state.pan.y + 'px) scale(' + state.zoom + ')';
    elements.image.style.transform = transform;
    elements.overlay.style.transform = transform;
  }

  function importJson(file) {
    const reader = new FileReader();
    reader.addEventListener('load', async () => {
      try {
        const data = JSON.parse(reader.result);
        const importedFeatures = data.features || (data.state && data.state.features) || [];
        if (!Array.isArray(importedFeatures)) throw new Error('No features array found');
        const created = [];
        for (const imported of importedFeatures) {
          const safeFeature = {
            name: imported.name || imported.label || 'Imported feature',
            feature_type: imported.feature_type || imported.type || 'point',
            category: imported.category || imported.force_type || '',
            icse_force: imported.icse_force || imported.force_type || '',
            geometry: imported.geometry || { points: imported.points || [] },
            style: normalizeStyle(imported.style || {}),
            properties: imported.properties || {},
            importance_notes: imported.importance_notes || imported.importance || '',
            exam_notes: imported.exam_notes || imported.exam_note || '',
            social_studies_notes: imported.social_studies_notes || imported.social_studies_connection || '',
            tags: imported.tags || [],
          };
          const result = await api.createFeature(safeFeature);
          created.push(result.feature);
        }
        state.features = state.features.concat(created);
        render();
        debounceSave();
        setStatus(created.length + ' feature(s) imported');
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
    document.querySelector('[data-map-action="report-pdf"]').addEventListener('click', () => {
      const feature = selectedFeature();
      if (!feature) return setStatus('Select a feature first');
      window.location.href = api.featureReportUrl(feature.id);
    });
    document.querySelector('[data-map-action="calibrate"]').addEventListener('click', () => {
      state.calibration = {
        mode: 'four_point_calibrated_future',
        updated_at: new Date().toISOString(),
        warning: 'Advanced approximate calibration works best only for proportional maps. Distorted/non-scale images may produce inaccurate coordinates.',
      };
      setStatus('Advanced approximate calibration marker saved');
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
    document.querySelectorAll('.style-control').forEach((control) => {
      control.addEventListener('input', updateLocalStyleFromControls);
      control.addEventListener('change', updateLocalStyleFromControls);
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
            renderAiResult(result);
          })
          .catch((error) => {
            $('ai-output').textContent = error.message;
          });
      });
    });
    document.querySelector('[data-chat-action="start"]').addEventListener('click', () => {
      ensureChat()
        .then((chatId) => api.chatMessages(chatId))
        .then((result) => {
          renderChat(result.messages);
          setStatus('Chat ready');
        })
        .catch((error) => setStatus(error.message));
    });
    document.querySelector('[data-chat-action="send"]').addEventListener('click', () => {
      sendChat().catch((error) => setStatus(error.message));
    });
    document.querySelector('[data-chat-action="export"]').addEventListener('click', () => {
      ensureChat()
        .then((chatId) => {
          window.location.href = api.chatExportUrl(chatId);
        })
        .catch((error) => setStatus(error.message));
    });
    document.querySelector('[data-chat-action="study-notes"]').addEventListener('click', () => {
      ensureChat()
        .then((chatId) => api.studyNotes(chatId))
        .then((result) => {
          renderAiResult(result);
          setStatus('Study notes created');
        })
        .catch((error) => setStatus(error.message));
    });
    document.querySelector('[data-generate-action="generate"]').addEventListener('click', () => {
      generateFeatureJson().catch((error) => setStatus(error.message));
    });
    document.querySelector('[data-generate-action="copy"]').addEventListener('click', () => {
      navigator.clipboard.writeText($('ai-feature-json').value || '').then(() => setStatus('Feature JSON copied'));
    });
    document.querySelector('[data-generate-action="import"]').addEventListener('click', () => {
      importGeneratedFeature().catch((error) => setStatus(error.message));
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
