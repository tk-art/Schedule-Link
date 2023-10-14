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


function followButtonClicked() {
  $.ajax({
    type: "POST",
    url: "/follow/" + userId + "/",
    data: {
      user_id: userId,
      csrfmiddlewaretoken: csrfToken,
    },
    success: function(response) {
      if (response.success) {
        isFollowing = response.is_following;
        console.log("isFollowing value is: ", isFollowing);

        if (isFollowing === true) {
          $("#follow-button").addClass("follow-btn");
        } else {
          $("#follow-button").removeClass("follow-btn");
        }
        $("#follow-button").text(isFollowing ? "フォロー中" : "フォロー");
        $("#follow-button").attr("data-following", isFollowing);
      }
    }
  });
}

$(document).ready(function() {
  $.ajax({
    type: "GET",
    url: "/get_follow_status/" + userId + "/",
    data: {
      user_id: userId,
    },
    success: function(response) {
      if (response.success) {
        $("#follow-button").addClass("follow-btn");
        $("#follow-button").text("フォロー中");
      }
    },
    error: function(xhr, status, error) {
      console.log(error);
    }
  });
});

$(document).ready(function() {
  var calendarEl = $('#calendar')[0];

  var calendar = new FullCalendar.Calendar(calendarEl, {
      initialView: 'dayGridMonth',
      locale: 'ja',
      buttonText: {
        today: '今日'
    },
    fixedWeekCount: false,
    selectable: true,
    events: '/api/calendar_events/' + userId + '/',

    select: function(info) {
      if (currentUser) {
        $('#selectedDate').val(info.startStr);
        $('#eventModal').modal('show');

        $('#saveEvent').off('click').on('click', function() {
            var title = $('#eventTitle').val();
            if (title) {
                calendar.addEvent({
                    title: title,
                    start: info.startStr,
                    end: info.endStr
                });
            }
            $('#eventModal').modal('hide');
            calendar.unselect();
        });
      }
    },

    eventClick: function(info) {
      if (currentUser) {
        $('#selectedDate').val(info.startStr);
        var localDate = new Date(info.event.start - info.event.start.getTimezoneOffset() * 60000);
        $('#selectedDate').val(localDate.toISOString().split('T')[0]);
        $('#eventTitle').val(info.event.title);
        $('#eventModal').modal('show');

        $('#saveEvent').off('click').on('click', function() {
            var newTitle = $('#eventTitle').val();
            if (newTitle) {
                info.event.setProp('title', newTitle);
            }
            $('#eventModal').modal('hide');
        });
      }
    }
  });

  calendar.render();
});

$(document).ready(function() {
  $('.free').on('change', function() {
      if ($(this).val() === '部分') {
          $('#timeSelectGroup').show();
      } else {
          $('#timeSelectGroup').hide();
      }
  });
});