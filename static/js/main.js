$(document).ready(function() {
  $('input[type="checkbox"][name="hobby"]').on('change', function() {
      if ($('input[type="checkbox"][name="hobby"]:checked').length > 3) {
          $(this).prop('checked', false);
          alert('趣味は最大3つまで選択できます。');
      }
  });
});

$(document).ready(function() {
  $('input[type="checkbox"][name="interest"]').on('change', function() {
      if ($('input[type="checkbox"][name="interest"]:checked').length > 5) {
          $(this).prop('checked', false);
          alert('興味は最大5つまで選択できます。');
      }
  });
});
