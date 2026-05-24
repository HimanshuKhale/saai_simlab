(function () {
  window.SAAIUploadManager = {
    async uploadSelectedFeaturePhoto(featureId) {
      const imageInput = document.getElementById('photo-image');
      const captionInput = document.getElementById('photo-caption');
      const sourceInput = document.getElementById('photo-source');
      if (!featureId || !imageInput.files.length) {
        throw new Error('Select a feature and choose a photo first.');
      }
      const formData = new FormData();
      formData.append('image', imageInput.files[0]);
      formData.append('caption', captionInput.value || '');
      formData.append('source', sourceInput ? sourceInput.value || '' : '');
      const result = await window.SAAIMapAPI.uploadPhoto(featureId, formData);
      imageInput.value = '';
      captionInput.value = '';
      if (sourceInput) sourceInput.value = '';
      return result;
    },
  };
})();
