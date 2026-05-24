(function () {
  function apiUrl(template, id) {
    return template.replace('/0/', '/' + id + '/');
  }

  async function request(url, options) {
    const config = window.SAAI_MAP_CONFIG;
    const headers = options.headers || {};
    if (!(options.body instanceof FormData)) {
      headers['Content-Type'] = 'application/json';
    }
    headers['X-CSRFToken'] = config.csrfToken;
    const response = await fetch(url, {
      credentials: 'same-origin',
      ...options,
      headers,
    });
    if (!response.ok) {
      const text = await response.text();
      throw new Error(text || response.statusText);
    }
    return response.json();
  }

  window.SAAIMapAPI = {
    apiUrl,
    listFeatures() {
      return request(window.SAAI_MAP_CONFIG.apiUrls.features, { method: 'GET' });
    },
    createFeature(feature) {
      return request(window.SAAI_MAP_CONFIG.apiUrls.features, {
        method: 'POST',
        body: JSON.stringify(feature),
      });
    },
    updateFeature(id, feature) {
      return request(apiUrl(window.SAAI_MAP_CONFIG.apiUrls.updateFeatureTemplate, id), {
        method: 'POST',
        body: JSON.stringify(feature),
      });
    },
    deleteFeature(id) {
      return request(apiUrl(window.SAAI_MAP_CONFIG.apiUrls.deleteFeatureTemplate, id), {
        method: 'POST',
        body: JSON.stringify({}),
      });
    },
    saveProject(project_json, calibration_json) {
      return request(window.SAAI_MAP_CONFIG.apiUrls.saveProject, {
        method: 'POST',
        body: JSON.stringify({ project_json, calibration_json }),
      });
    },
    uploadPhoto(id, formData) {
      return request(apiUrl(window.SAAI_MAP_CONFIG.apiUrls.uploadPhotoTemplate, id), {
        method: 'POST',
        body: formData,
        headers: {},
      });
    },
    addNote(id, note) {
      return request(apiUrl(window.SAAI_MAP_CONFIG.apiUrls.addNoteTemplate, id), {
        method: 'POST',
        body: JSON.stringify(note),
      });
    },
  };
})();
