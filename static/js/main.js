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

function requestClicked() {
  var userData = $("#selectedData").text();

  $.ajax({
    type: "POST",
    url: "/intentional_request/" + userId + "/",
    data: {
      user_id: userId,
      csrfmiddlewaretoken: csrfToken,
      userData: userData
    },
    success: function(response) {
      if(response.status == "success"){
        alert("正常にリクエストが送信されました");
      } else {
          alert("エラーが発生しました");
      }
    }
  });
}

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
      if (currentUser == 'true') {
        var events = calendar.getEvents();
        var eventExists = events.some(event => {
            return event.startStr === info.startStr;
        });

        if (eventExists) {
          $('#deleteEvent').show();
        } else {
            $('#deleteEvent').hide();
            $('#selectedDate').val(info.startStr);
            $('#eventModal').modal('show');

            $('#saveEvent').off('click').on('click', function() {
                var title = $('#eventTitle').val();

                if (title) {
                    calendar.addEvent({
                        title: title,
                        start: info.startStr,
                        end: info.endStr,
                    });
                }
                $('#eventModal').modal('hide');
                calendar.unselect();
            });
        }

      }
    },

    eventClick: function(info) {
      var localDate = new Date(info.event.start - info.event.start.getTimezoneOffset() * 60000);
      var selectedDateStr = localDate.toISOString().split('T')[0];


      if (currentUser == "true") {
        $('#selectedDate').val(info.startStr);
        $('#selectedDate').val(selectedDateStr);

        $('#deleteDate').val(info.startStr);
        $('#deleteDate').val(selectedDateStr);

        $('#eventTitle').val(info.event.title);
        $('#deleteEvent').show();

        $('#eventModal').modal('show');


        $('#saveEvent').off('click').on('click', function() {
            var newTitle = $('#eventTitle').val();
            if (newTitle) {
                info.event.setProp('title', newTitle);
            }
            $('#eventModal').modal('hide');
        });
      } else {
        getEventData(selectedDateStr, function(data) {
          $('#selectedData').text(selectedDateStr);
          $('#otherUserData').text(info.event.title);
          $('#timeData').text(data.time);
          $('#messageData').text(data.message);

          $('#otherUserModal').modal('show');
        });

      }
    },
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

function getEventData(selectedDate, callback) {
  $.ajax({
      url: "/get_event_data/" + userId + "/",
      method: "GET",
      data: {
          date: selectedDate,
      },
      success: function(data) {
          callback(data);
      }
  });
}

/* 画像用モーダル */
$('.profile-image-modal').click(function() {
  const modal = $('#modal');
  const modalImage = $('#modal-image');

  modalImage.attr('src', $(this).attr('src'));
  modal.show();
});

$('#close-modal').click(function() {
  $('#modal').hide();
});