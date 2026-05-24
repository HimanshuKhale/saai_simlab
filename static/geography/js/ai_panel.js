(function () {
  async function post(url) {
    const response = await fetch(url, {
      method: 'POST',
      credentials: 'same-origin',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': window.SAAI_MAP_CONFIG.csrfToken,
      },
      body: JSON.stringify({}),
    });
    if (!response.ok) {
      throw new Error(await response.text());
    }
    return response.json();
  }

  window.SAAIAIPanel = {
    async run(action, featureId) {
      const urls = window.SAAI_MAP_CONFIG.apiUrls;
      if (action === 'explain') {
        if (!featureId) throw new Error('Select a feature first.');
        return post(window.SAAIMapAPI.apiUrl(urls.explainFeatureTemplate, featureId));
      }
      if (action === 'questions') {
        if (!featureId) throw new Error('Select a feature first.');
        return post(window.SAAIMapAPI.apiUrl(urls.generateQuestionsTemplate, featureId));
      }
      if (action === 'check') {
        return post(urls.checkProject);
      }
      if (action === 'revision') {
        return post(urls.revisionSheet);
      }
      if (action === 'public-context') {
        if (!featureId) throw new Error('Select a feature first.');
        return window.SAAIMapAPI.publicContext(featureId);
      }
      throw new Error('Unknown AI action.');
    },
    renderTransparency(target, payload) {
      if (!target) return;
      const data = payload.explanation || payload.feature_json || payload.revision_sheet || payload.study_note || payload;
      const basis = data.source_basis || {};
      const warnings = data.warnings || [];
      target.textContent = [
        data.confidence ? 'Confidence: ' + data.confidence : '',
        warnings.length ? 'Warnings: ' + warnings.join('; ') : '',
        basis ? 'Sources: ' + JSON.stringify(basis) : '',
        data.uncertainty ? 'Uncertainty: ' + data.uncertainty : '',
        data.student_warning || 'AI explanations are study assistance. Verify with textbook/teacher.',
      ].filter(Boolean).join('\n');
    },
  };
})();
