(function () {
  window.SAAIUploadManager = {
    async uploadSelectedFeaturePhoto(featureId) {
      const imageInput = document.getElementById('photo-image');
      const captionInput = document.getElementById('photo-caption');
      if (!featureId || !imageInput.files.length) {
        throw new Error('Select a feature and choose a photo first.');
      }
      const formData = new FormData();
      formData.append('image', imageInput.files[0]);
      formData.append('caption', captionInput.value || '');
      const result = await window.SAAIMapAPI.uploadPhoto(featureId, formData);
      imageInput.value = '';
      captionInput.value = '';
      return result;
    },
  };
})();
