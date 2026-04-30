// 파일 업로드 버튼 클릭 이벤트 처리
document.addEventListener('DOMContentLoaded', function () {
  const fileInput = document.getElementById('file-input');
  if (fileInput) {
    fileInput.addEventListener('change', function () {
      if (this.files.length > 0) {
        document.getElementById('upload-form').submit();
      }
    });
  }
});
