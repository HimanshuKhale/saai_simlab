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
      throw new Error('Unknown AI action.');
    },
  };
})();
