document.addEventListener('DOMContentLoaded', () => {
    
    // Connect to websocket
    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port, {transports: ['websocket']});

    // Retrieve username
    const username = document.querySelector('#get-username').innerHTML;

    // // Set default room
    // let room = document.querySelectorAll('.select-room');
    // joinRoom(room[0].innerHTML);
    // console.log(room[0].innerHTML);

    // connect to user
    document.querySelectorAll('.search-users').forEach(p => {
        p.onclick = () => {
            let friend_name = p.innerHTML;
            // Check if user already in the room
            console.log(friend_name);
            if (friend_name === username) {
                msg = `You are  ${username}, cannot connect to yourself.`;
                printSysMsg(msg);
            } else {
                // ajax
                $.ajax({
                    method: 'post',
                    url: '/connect_user',
                    data: {'name':friend_name, 'id':p.id},
                    success: function(res) {
                        console.log(res['msg']);
                        var const_p = "<p>" + res['msg'] + "</p>";
                        $('#display-message-section').html(const_p);
                    }
                });
            }
        };
    });

    // block user
    document.querySelectorAll('.block-btn').forEach(button => {
        button.onclick = () => {
            let blocked_user_id = button.id;
            let btn_value = button.value;
            console.log(btn_value);
            $.ajax({
                method: 'post',
                url: '/block_user',
                data: {'id': blocked_user_id, 'action': btn_value},
                success: function(res) {
                    console.log(res['msg']);
                    if (btn_value === 'Block') {
                        button.value = 'Un-Block';
                    }
                    else {
                        button.value = 'Block';
                    }
                }
            });
        }
    });

    // Send messages
    document.querySelector('#send_message').onclick = () => {
        socket.emit('message', {'msg': document.querySelector('#user_message').value,
            'username': username, 'room': room});
        document.querySelector('#user_message').value = '';
    };

    // Display all incoming messages
    socket.on('message', data => {
        console.log(data.msg);
        // Display current message
        if (data.msg) {
            const p = document.createElement('p');
            const span_username = document.createElement('span');
            const span_timestamp = document.createElement('span');
            const br = document.createElement('br')
            // Display user's own message
            if (data.username == username) {
                    p.setAttribute("class", "my-msg");

                    // Username
                    span_username.setAttribute("class", "my-username");
                    span_username.innerText = data.username;

                    // Timestamp
                    span_timestamp.setAttribute("class", "timestamp");
                    span_timestamp.innerText = data.time_stamp;

                    // HTML to append
                    p.innerHTML += span_username.outerHTML + br.outerHTML + data.msg + br.outerHTML + span_timestamp.outerHTML

                    //Append
                    document.querySelector('#display-message-section').append(p);
            }
            // Display other users' messages
            else if (typeof data.username !== 'undefined') {
                p.setAttribute("class", "others-msg");

                // Username
                span_username.setAttribute("class", "other-username");
                span_username.innerText = data.username;

                // Timestamp
                span_timestamp.setAttribute("class", "timestamp");
                span_timestamp.innerText = data.time_stamp;

                // HTML to append
                p.innerHTML += span_username.outerHTML + br.outerHTML + data.msg + br.outerHTML + span_timestamp.outerHTML;

                //Append
                document.querySelector('#display-message-section').append(p);
            }
            // Display system message
            else {
                printSysMsg(data.msg);
            }


        }
        scrollDownChatWindow();
    });

    // Select a room
    document.querySelectorAll('.select-room').forEach(p => {
        p.onclick = () => {
            let newRoom = p.innerHTML;
            // Check if user already in the room
            console.log(newRoom);
            if (newRoom === room) {
                msg = `You are already in ${room} room.`;
                printSysMsg(msg);
            } else {
                leaveRoom(room);
                joinRoom(newRoom);
                room = newRoom;
            }
        };
    });

    // Logout from chat
    document.querySelector("#logout-btn").onclick = () => {
        leaveRoom(room);
    };

    // Trigger 'leave' event if user was previously on a room
    function leaveRoom(room) {
        socket.emit('leave', {'username': username, 'room': room});

        document.querySelectorAll('.select-room').forEach(p => {
            p.style.color = "black";
        });
    }

    // Trigger 'join' event
    function joinRoom(room) {

        // Join room
        socket.emit('join', {'username': username, 'room': room});

        // Highlight selected room
        document.querySelector('#' + CSS.escape(room)).style.color = "#ffc107";
        document.querySelector('#' + CSS.escape(room)).style.backgroundColor = "white";

        // Clear message area
        document.querySelector('#display-message-section').innerHTML = '';

        // Autofocus on text box
        document.querySelector("#user_message").focus();
    }

    // Scroll chat window down
    function scrollDownChatWindow() {
        const chatWindow = document.querySelector("#display-message-section");
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    // Print system messages
    function printSysMsg(msg) {
        const p = document.createElement('p');
        p.setAttribute("class", "system-msg");
        p.innerHTML = msg;
        document.querySelector('#display-message-section').append(p);
        scrollDownChatWindow()

        // Autofocus on text box
        document.querySelector("#user_message").focus();
    }
});
