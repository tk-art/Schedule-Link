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

/* 赤丸　indicator */

function showHamburgerIndicator(hamburgerId) {
  if ($(hamburgerId).find('.hamburger-indicator').length === 0) {
    var indicator = $('<span class="hamburger-indicator">🔴</span>');
    $(hamburgerId).append(indicator);
  }
}

function showTabIndicator(tabId) {
  if ($(tabId).find('.follower-indicator').length === 0) {
    var indicator = $('<span class="follower-indicator">🔴</span>');
    $(tabId).append(indicator);
  }
}

function hideTabIndicator(tabId) {
  $(tabId).find('.follower-indicator').remove();
}

function showListIndicator(tabId) {
  if ($(tabId).find('.unread-indicator').length === 0) {
    var indicator = $('<span class="unread-indicator">🔴</span>');
    $(tabId).append(indicator);
  }
}

function hideListIndicator(tabId) {
  $(tabId).find('.unread-indicator').remove();
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
        showHamburgerIndicator('#js-hamburger');
        showTabIndicator('#nav-profile-link');
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
        showHamburgerIndicator('#js-hamburger');
        showTabIndicator('#nav-profile-link');
        showTabIndicator("#profile-link");
        showTabIndicator("#followed-by");
      }
    },
    error: function(xhr, status, error) {
      console.log(error);
    }
  });
});

$('#followed-by').on('click', function() {
  $.ajax({
    type: "GET",
    url: "/confirm_followers_viewed/",
    success: function(response) {
      hideTabIndicator('#js-hamburger');
      hideTabIndicator('#nav-profile-link');
      hideTabIndicator('#profile-link');
      hideTabIndicator('#followed-by');
    }
  });
});


/* リクエストクリック */

function requestClicked(element) {
  var userId, userData, eventId;

  if (element) {
    userId = $(element).data('key');
    userData = $("#selectedData-" + userId).text();
  } else {
    userId = $('#intentionalBtn').data('key');
    if ($('.profile-page-container').length) {
      userData = $("#selectedData").text();
    } else {
      eventId = $('#intentionalBtn').data('event-id');
    }
  }

  var dataToSend = {
    user_id: userId,
    csrfmiddlewaretoken: csrfToken
  };

  if (userData) {
    dataToSend.userData = userData;
  }
  if (eventId) {
    dataToSend.eventId = eventId;
  }

  $.ajax({
    type: "POST",
    url: "/intentional_request/" + userId + "/",
    data: dataToSend,
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


/* リクエストが存在する場合ヒマリクボタンを消す */

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
      }
    });
  });
});

$(document).ready(function() {
  $('.event-card').each(function() {
    var card = $(this);
    var eventId = card.data('event-id');
    var userId = card.data('key');

    $.ajax({
      type: "POST",
      url: "/check_user_request/" + userId + "/",
      data: {
        csrfmiddlewaretoken: csrfToken,
        eventId: eventId
      },
      success: function(response) {
        if (response.situation) {
          $('#eventmodal').on('shown.bs.modal', function() {
            $(this).find('#cardBtn-' + eventId).hide();
          });
        }
      }
    });
  });
});



/* カレンダー */

function customTitleGenerator() {
  var monthNames = ["1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月", "12月"];
  var now = new Date();
  var year = now.getFullYear();
  var monthIndex = now.getMonth();
  var monthName = monthNames[monthIndex];

  return year + ' ' + monthName;
}

function formatTime(data) {
  var hours = data.getHours();
  var minutes = data.getMinutes();

  if (hours < 10) hours = '0' + hours;
  if (minutes < 10) minutes = '0' + minutes;

  return hours + ':' + minutes;
}

$(document).ready(function() {
  var calendarEl = $('#calendar')[0];
  var modalCalendar;

  var calendar = new FullCalendar.Calendar(calendarEl, {
      initialView: 'dayGridMonth',
      fixedWeekCount: false,
      selectable: true,
      events: '/api/calendar_events/' + userId + '/',

    datesSet: function() {
      var customTitle = customTitleGenerator();
      $('#fc-dom-1').text(customTitle);
    },

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

                $('#partialmodal').on('shown.bs.modal', function() {
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

/* 検索ページカレンダー */

$('#datesearch').on('click', function() {
  var calendarEl = $('#date-calendar')[0];

  var dateCalendar = new FullCalendar.Calendar(calendarEl, {
    initialView: 'dayGridMonth',
    fixedWeekCount: false,
    selectable: true,
    selectMirror: true,

    datesSet: function() {
      var customTitle = customTitleGenerator();
      $('#fc-dom-1').text(customTitle);
    },

    select: function(info) {
      var startDate = info.startStr;
      var endDate = moment(info.endStr).subtract(1, 'days').format('YYYY-MM-DD');

      if (startDate === endDate) {
        $('#datesearch').val(startDate);
      } else {
        $('#datesearch').val(startDate + ' ~ ' + endDate);
      }
      $('#datesearchmodal').modal('hide');
    },
  });

  $('#datesearchmodal').modal('show');

  $('#datesearchmodal').on('shown.bs.modal', function() {
    dateCalendar.render();
  });
});

/* イベントページカレンダー */

$('#datetime').on('click', function() {
  var calendarEl = $('#date-calendar')[0];
  var timeCalendar;

  var dateCalendar = new FullCalendar.Calendar(calendarEl, {
      initialView: 'dayGridMonth',
      fixedWeekCount: false,
      selectable: true,

      datesSet: function() {
        var customTitle = customTitleGenerator();
        $('#fc-dom-1').text(customTitle);
        $('#fc-dom-72').text(customTitle);
      },

      select: function(info) {
        var selectedDate = info.start;

        if (!timeCalendar) {
          timeCalendar = new FullCalendar.Calendar($('#time-calendar')[0], {
              initialView: 'timeGridDay',
              initialDate: selectedDate,
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
                $('#datetime').val(info.startStr.split('T')[0] + ' ' + start + '~' + end);
                $('#timemodal').modal('hide');
              },
          });
          $('#timemodal').modal('show');
          $('#datetimemodal').modal('hide');
        }
        $('#timemodal').on('shown.bs.modal', function() {
          timeCalendar.render();
        });
      }
  })

  $('#datetimemodal').modal('show');

  $('#datetimemodal').on('shown.bs.modal', function() {
    dateCalendar.render();
  });
})

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

/* リクエストチェック */

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
          showHamburgerIndicator('#js-hamburger');
          showTabIndicator('#requests-link');
          showTabIndicator('#nav-requests-link');
        } else {
          hideTabIndicator('#js-hamburger');
          hideTabIndicator('#requests-link');
          hideTabIndicator('#nav-requests-link');
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
});

/*　チャットチェック　赤丸 */

function RedCircleDisplay() {
  $('.chat-list').each(function() {
    var chatLink = $(this);
    var userId = chatLink.data('user-id');

    $.ajax({
      url: '/check_unread_messages/' + userId + '/',
      method: 'GET',
      success: function(data) {
        if (data.chat_unread) {
          var chatListIndicator = chatLink.find('.list-indicator');
          showListIndicator(chatListIndicator);
        }
      },
      error: function(error) {
        console.log('チャットのマークに失敗しました。', error);
      }
    });
  });

  $('.chat-list').click(function() {
    var userId = $(this).data('user-id');

    $.ajax({
      url: '/mark_chat_as_read/' + userId + '/',
      method: 'GET',
      success: function(response) {
        hideListIndicator(userId);
      },
      error: function(error) {
        console.log('チャットのマークに失敗しました。', error);
      }
    });
  });
}

$(document).ready(function() {
  var path = window.location.pathname;

  $.ajax({
    url: '/check_unread_full_messages/',
    method: 'GET',
    success: function(data) {
      if (data.chat_unread) {
        if (!path.includes('/chat_list') && !data.sender_ids.includes('sender_id')) {
          showHamburgerIndicator('#js-hamburger');
          showTabIndicator('#chat-link');
          showTabIndicator('#nav-chat-link');
        }
      }
    },
    error: function(error) {
      console.log('チャットのマークに失敗しました。', error);
    }
  });
  RedCircleDisplay();
});

function displayChatMessage(senderId, message, message_id, image, delta) {
  var newChatContent = $('<div>').addClass('chat-content');
  var chatContainer = $('.chat-full-container');
  var senderLastMessage = $('<div>').addClass('sender-last-message').attr('id', 'message-' + message_id);

  if (senderId !== currentUserId) {
    if (image) {
      var imageElement = $('<img>').attr('src', image).attr('class', 'chat-room-image');
      var linkElement = $('<a>').attr('href', '/profile/' + senderId).append(imageElement);
      var imageContainer = $('<div>').append(linkElement);
      newChatContent.append(imageContainer);
    }

    var messageElement = $('<p>').addClass('receiver-chat').text(message);
    var messsageDelta = $('<p>').addClass('chat-other-delta').text(delta);
    newChatContent.append(messageElement);
    newChatContent.append(messsageDelta);

    $('.chat-container').append(newChatContent);
  } else {
    var readMark = $('<span>').addClass('chat-current-delta read-mark').text('既読').hide();
    var messsageDelta = $('<p>').addClass('chat-current-delta').text('たった今');
    var messageElement = $('<p>').addClass('sender-chat').text(message);
    senderLastMessage.append(readMark);
    senderLastMessage.append(messsageDelta);
    newChatContent.append(senderLastMessage);
    newChatContent.append(messageElement);

    $('.chat-container').append(newChatContent);
  }
  chatContainer.scrollTop(chatContainer.prop('scrollHeight'));
}

/* チャット */

$(function() {
  var chatSocket = new WebSocket(
    'ws://' + window.location.host + '/ws/chat/' + currentUserId + '/'
  );

  chatSocket.onmessage = function(e) {
    var data = JSON.parse(e.data);
    var message = data.message;
    var delta = data.chat;
    var image = data.image;
    var sender_id = data.sender_id;
    var receiver_id = data.receiver_id;
    var message_id = data.message_id;
    var path = window.location.pathname;

    if (data.temporary_id) {
      $('#message-' + data.temporary_id).attr('id', 'message-' + data.message_id);
    }

    if (data.action === 'readReceipt') {
        $('#message-' + data.message_id + ' .read-mark').show();
    }

    if (receiver_id　=== currentUserId) {
      $('.read-mark').hide();
      displayChatMessage(sender_id, message, message_id, image, delta);
      if (path.includes('/chat_list')) {
        RedCircleDisplay();
      } else if (path.includes('/chat/' + sender_id)){
        $.ajax({
          url: '/mark_chat_as_read/' + sender_id + '/',
          method: 'GET',
        });
      } else {
        showHamburgerIndicator('#js-hamburger');
        showTabIndicator('#chat-link');
        showTabIndicator('#nav-chat-link');
      }
    }
    $('#room-' + sender_id).html(message);
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
    var temporaryId = Date.now();
    var message = $('#chat-message-input').val();
    if (message.trim() !== '') {
      chatSocket.send(JSON.stringify({
        'message': message,
        'sender_id': sender_id,
        'receiver_id': receiver_id,
        'room_name': roomName,
        'temporaryId': temporaryId,
      }));

      displayChatMessage(sender_id, message, temporaryId, null, null);
      $('.read-mark').hide();
      $('#chat-message-input').val('');
    }
  });
});

$(document).ready(function() {
  var chatContainer = $('.chat-full-container');
  chatContainer.scrollTop(chatContainer.prop('scrollHeight'));
});

/* イベントクリック時のモーダル動作 */
$('.event-modal').on('click', function() {
  var eventId = $(this).data('event-id');
  var userId = $(this).data('key');

  $.ajax({
    url: '/get_event_details/',
    data: {
        'event_id': eventId
    },
    success: function(data) {
      $('#eventmodal .card-modal-profile a').attr('href', '/profile/' + userId);
      $('#eventmodal .card-modal-profile img').attr('src', data.profile_url);
      $('#eventmodal .card-modal-profile .card-modal-name').text(data.username);
      $('#eventmodal .card-modal-profile .chat-delta').text(data.delta);
      $('#eventmodal .card-modal-left img').attr('src', data.image_url);
      $('#eventmodal .card-modal-right .title').text(data.title);
      $('#eventmodal .card-modal-right .place').text(data.place);
      $('#eventmodal .card-modal-right .date').text(data.date);
      $('#eventmodal .card-modal-right .time').text(data.time);
      $('#eventmodal .card-modal-right .detail').text(data.detail);

      $('#eventmodal .card-btn .intentional-btn').attr('data-key', userId);
      $('#eventmodal .card-btn .intentional-btn').attr('data-event-id', eventId);

      $('#card_editing_modal .modal-body form').attr('action', '/card_editing/' + eventId + '/');
      $('#eventmodal .card-edit-btn form').attr('action', '/delete_card/' + eventId + '/');

      if (!data.current_user) {
        $('#eventmodal .card-btn').show();
        $('#eventmodal .card-btn').attr('id', 'cardBtn-' + eventId );
      } else {
        $('#eventmodal .card-btn').hide();
      }

      $('#eventmodal').modal('show');
    }
  })
})

/* トップページカテゴリー検索 */
function searchCategory(categoryType) {
  var selector = categoryType === 'phone' ? '#phone-size-category' : '#category';
  var selectedCategory = $(selector).val();
  window.location.href = `?category=${selectedCategory}`;
}

function searchRecom(recommendationType) {
  var selector = recommendationType === 'phone' ? '#phone-size-recommendation' : '#recommendation';
  var selectedRecom = $(selector).val();
  if (selectedRecom === 'おすすめユーザー') {
    window.location.href = `?recommend_user=${selectedRecom}`;
  } else {
    window.location.href = `?recommend_event=${selectedRecom}`;
  }
}
