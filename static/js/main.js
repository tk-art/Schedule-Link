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

$(document).ready(function() {
  var nav = $('#nav-wrapper');
  var hamburger = $('#js-hamburger');
  var blackBg = $('#js-black-bg');

  hamburger.click(function() {
      nav.toggleClass('open');
  });
  blackBg.click(function() {
      nav.removeClass('open');
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
      if (response.new_follower) {
        showTabIndicator("#profile-link");
        showTabIndicator("#followed_by");
      }
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
  $.ajax({
    type: "GET",
    url: "/get_follower_count/",
    success: function(response) {
      if (response.new_follower) {
        showTabIndicator("#profile-link");
        showTabIndicator("#followed-by");
      }
    },
    error: function(xhr, status, error) {
      console.log(error);
    }
  });

  function showTabIndicator(tabId) {
    var indicator = $('<span class="follower-indicator">🔴</span>');
    $(tabId).append(indicator);
  }
});

$('#followed-by').on('click', function() {
  $.ajax({
    type: "GET",
    url: "/confirm_followers_viewed/",
    success: function(response) {
      hideTabIndicator('#profile-link');
      hideTabIndicator('#followed-by');
    }
  });

  function hideTabIndicator(tabId) {
    $(tabId).find('.follower-indicator').remove();
  }
});

function requestClicked(element) {
  var userData;

  if (element) {
    var userId = $(element).data('key');
    userData = $("#selectedData-" + userId).text();
  } else {
    var userId = $('#intentionalBtn').data('key');
    userData = $("#selectedData").text();
  }

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
        $(element).hide();
        $("#intentionalBtn").hide();
      } else {
          alert("エラーが発生しました");
      }
    }
  });
}

$('#otherUserModal').on('shown.bs.modal', function () {
  var btn = $("#intentionalBtn");
  var userId = btn.data('key');
  var userData = $("#selectedData").text();
  $.ajax({
    type: "POST",
    url: "/check_user_request/" + userId + "/",
    data: {
      csrfmiddlewaretoken: csrfToken,
      userData: userData
    },
    success: function(response) {
      if (response.situation) {
        btn.hide();
      }
    }
  });
});


$(document).ready(function() {
  $('.intentional-btn').each(function() {
    var btn = $(this);
    var userId = btn.data('key');
    var userData = $("#selectedData-" + userId).text();
    $.ajax({
      type: "POST",
      url: "/check_user_request/" + userId + "/",
      data: {
        csrfmiddlewaretoken: csrfToken,
        userData: userData
      },
      success: function(response) {
        if (response.situation) {
          btn.hide();
        }
      },
      error: function(error) {
        console.log(error);
      }
    });
  });
});

$(document).ready(function() {
  var calendarEl = $('#calendar')[0];
  var modalCalendar;

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

            $('.free').on('change', function() {
              if ($(this).val() === '部分') {
                $('#timeSelectGroup').show();
                $('#time').on('click', function(){
                  if (!modalCalendar) {
                    modalCalendar = new FullCalendar.Calendar($('#partial-modal-content')[0], {
                        initialView: 'timeGridDay',
                        headerToolbar: {
                          left: '',
                          center: '',
                          right: ''
                        },
                        allDaySlot: false,
                        locale: 'ja',
                        selectable: true,
                        select: function(info) {
                          var start = formatTime(info.start);
                          var end = formatTime(info.end);
                          $('#time').val(start + '~' + end);
                          $('#partialmodal').modal('hide');
                        }
                    });
                  }
                  $('#partialmodal').modal('show');
                });

                $('#partialmodal').on('shown.bs.modal', function () {
                  modalCalendar.render();
                });

              } else {
                  $('#timeSelectGroup').hide();
              }
            });

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

function formatTime(data) {
  var hours = data.getHours();
  var minutes = data.getMinutes();

  if (hours < 10) hours = '0' + hours;
  if (minutes < 10) minutes = '0' + minutes;

  return hours + ':' + minutes;
}

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


$(".request-btn button").click(function() {
  $(this).closest('.request-btn').hide();
});

/*リクエストチェック*/
$(document).ready(function() {
  function checkNewRequests() {
    $.ajax({
      url: '/check_new_requests/',
      method: 'GET',
      success: function(response) {
        if (response.requests_unread) {
          showTabIndicator('#tab1-tab');
        }
        if (response.responses_unread) {
          showTabIndicator('#tab3-tab');
        }

        if (response.requests_unread || response.responses_unread) {
          showTabIndicator('#requests-link');
        } else {
          hideTabIndicator('#requests-link');
        }
      },
      error: function(error) {
        console.log('リストの問い合わせに失敗しました。', error);
      }
    });
  }

  checkNewRequests();

  $('.nav-link').click(function() {
    var tabId = $(this).attr('id');
    var requestType;

    switch (tabId) {
      case 'tab1-tab':
        requestType = 'request';
        break;
      case 'tab3-tab':
        requestType = 'response';
        break;
      default:
        requestType = null;
    }

    if (requestType) {
      $.ajax({
        url: '/mark_tab_as_read/',
        method: 'POST',
        data: {
          csrfmiddlewaretoken: csrfToken,
          type: requestType
        },
        success: function(response) {
        },
        error: function(error) {
          console.log('リクエストのマークに失敗しました。', error);
        }
      });
    }
  });

  function showTabIndicator(tabId) {
    var indicator = $('<span class="follower-indicator">🔴</span>');
    $(tabId).append(indicator);
  }

  function hideTabIndicator(tabId) {
    $(tabId).find('.follower-indicator').remove();
  }
});


/*　チャットチェック　*/
$(document).ready(function() {
  var unread_messages = false;
  var unread = [];

  $('.chat-list').each(function() {
    var chatLink = $(this);
    var userId = chatLink.data('user-id');

    var request = $.ajax({
      url: '/check_unread_messages/' + userId + '/',
      method: 'GET',
      success: function(data) {
        if (data.chat_unread) {
          showTabIndicator(chatLink);
          unread_messages = true;
        }
      }
    });

    unread.push(request);
  });

  $.when.apply($, unread).then(function() {
    if (unread_messages) {
      var headerChatLink = $('a[href="/chat_list"]');
      if (headerChatLink.find('.follower-indicator').length === 0) {
          showTabIndicator(headerChatLink);
      }
    }
  });

  $('.chat-list').click(function() {
    var userId = $(this).data('user-id');
    console.log('userId: ' + userId);

    $.ajax({
      url: '/mark_chat_as_read/' + userId + '/',
      method: 'GET',
      success: function(response) {
        hideTabIndicator(userId);
      },
      error: function(error) {
        console.log('チャットのマークに失敗しました。', error);
      }
    });
  });

  function showTabIndicator(chatList) {
    var indicator = $('<span class="follower-indicator">🔴</span>');
    $(chatList).append(indicator);
  }

  function hideTabIndicator(chatList) {
    $(chatList).find('.follower-indicator').remove();
  }

});


/*チャット*/
$(function() {
  var chatSocket = new WebSocket(
    'ws://' + window.location.host + '/ws/chat/' + roomName + '/'
  );

  chatSocket.onmessage = function(e) {
    var data = JSON.parse(e.data);
    var message = data.message;
    var delta = data.chat;
    var image = data.image;
    var sender_id = data.sender_id;
    var newChatContent = $('<div>').addClass('chat-content');

    if (image) {
      var imageElement = $('<img>').attr('src', image).attr('class', 'request-image-size');
      var linkElement = $('<a>').attr('href', '/profile/' + sender_id).append(imageElement);
      var imageContainer = $('<div>').addClass('chat-image').append(linkElement);
      newChatContent.append(imageContainer);
    }

    var messageElement = $('<p>').addClass('chat-log').text(message);
    var messsageDelta = $('<p>').addClass('chat-delta').text(delta);
    newChatContent.append(messageElement);
    newChatContent.append(messsageDelta);

    $('.chat-container').append(newChatContent);
  };

  chatSocket.onclose = function(e) {
    console.error('チャットソケットが予期せず閉じられました');
  };

  $('#chat-message-input').on('keyup', function(e) {
    if (e.keyCode === 13　&& this.value.trim() !== '') {
      $('#chat-message-submit').click();
    }
  });

  $('#chat-message-submit').on('click', function() {
    var message = $('#chat-message-input').val();
    console.log(message);
    if (message.trim() !== '') {
      chatSocket.send(JSON.stringify({
        'message': message,
        'sender_id': sender_id,
        'receiver_id': receiver_id,
        'room_name': roomName
      }));
      $('#chat-message-input').val('');
    }
  });
});

$(document).ready(function() {
  var chatContainer = $('.chat-full-container');
  chatContainer.scrollTop(chatContainer.prop('scrollHeight'));
});