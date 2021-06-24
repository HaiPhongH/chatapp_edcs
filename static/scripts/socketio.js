document.addEventListener('DOMContentLoaded', () => {
    
    // Connect to websocket
    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);

    // Retrieve username
    const username = document.querySelector('#get-username').innerHTML;
    const id = document.querySelector('#get-iduser').innerHTML;

    if (username !== null) {
        socket.emit('online', {'id':id, 'username': username});
    }

    // // Set default room
    let room = document.querySelectorAll('.select-room')[0].id;
    let oldName = document.querySelectorAll('.select-room')[0].innerHTML;
    let block_statuses = document.querySelectorAll('.block-btn');

    console.log(room, oldName);

    // connect to user
    // document.querySelectorAll('.search-users').forEach(p => {
    //     p.onclick = () => {
    //         let friend_name = p.innerHTML;
    //         // Check if user already in the room
    //         console.log(friend_name);
    //         if (friend_name === username) {
    //             msg = `You are  ${username}, cannot connect to yourself.`;
    //             printSysMsg(msg);
    //         } else {
    //             // ajax
    //             $.ajax({
    //                 method: 'post',
    //                 url: '/connect_user',
    //                 data: {'name':friend_name, 'id':p.id},
    //                 success: function(res) {
    //                     console.log(res['msg']);
    //                     var const_p = "<p>" + res['msg'] + "</p>";
    //                     $('#display-message-section').html(const_p);
    //                 }
    //             });
    //         }
    //     };
    // });

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
                    var const_p = "<p>" + res['msg'] + "</p>";
                    $('#display-message-section').html(const_p);
                    if (btn_value === 'Block') {
                        button.value = 'Un-Block';
                    }
                    else {
                        button.value = 'Block';
                    }
                    socket.emit('block_sending', {'userid': id, 'blocked_id': blocked_user_id, 'action': btn_value});
                }
            });
        }
    });

    // Send messages
    document.querySelector('#send_message').onclick = () => {
        socket.emit('message', {'msg': document.querySelector('#user_message').value,
            'username': username, 'room': room});
        // console.log({'msg': document.querySelector('#user_message').value,
        // 'username': username, 'room': room});
        document.querySelector('#user_message').value = '';
    };

    socket.on('status_change', data => {
        // console.log(data);
        let new_id = data['id'];
        let new_name = data['username'];
        let new_status = data['status'];

        if (new_name !== username) {
            document.querySelector('#status_' + new_id).innerHTML = new_status;
        }
        // document.querySelector('#status_' + data['id']).innerHTML = data['status'];
    });

    socket.on('disable_button', data => {
        let userid = data['userid'];
        let blocked_id = data['blocked_id'] ;
        let action = data['action'];

        if (blocked_id !== id) {
            if (action === 'Block') {              
                document.getElementById("div_send_message_" + blocked_id).querySelector('#send_message').disabled=true;
            }
            else {
                document.getElementById("div_send_message_" + blocked_id).querySelector('#send_message').disabled=false;
            }
        }
    });

    // Display all incoming messages
    socket.on('message', data => {
        // console.log(data);
        // Display current message
        if (data.msg) {
            const p = document.createElement('p');
            const span_username = document.createElement('span');
            const span_timestamp = document.createElement('span');
            const br = document.createElement('br')
            // Display user's own message
            // console.log({'username': data.username, 'msg': data.msg, 'timestamp': data.time_stamp});
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

    function disable_send_btn(block_id) {
        if (id === block_id) {
            document.getElementById("send_message").disabled = true;
        }
    }

    function enable_send_btn(block_id) {
        if (id === block_id) {
            document.getElementById("send_message").disabled = false;
        }
    }

    // Select a room
    document.querySelectorAll('.select-room').forEach((p, index, value) => {
        p.onclick = () => {
            let newRoom = p.id;
            let roomName = p.innerHTML;
            // Check if user already in the room
            // console.log(block_statuses[index]);
            // if (block_statuses[index].value === 'Un-Block') {
            //     document.getElementById("send_message").disabled = true;
            // }
            // else {
            //     document.getElementById("send_message").disabled = false;
            // }
            if (newRoom === room) {
                msg = `You are already in the room with ${roomName}.`;
                printSysMsg(msg);
            } else {
                leaveRoom(room, oldName);
                joinRoom(newRoom, roomName);
                room = newRoom;
            }
        };
    });

    window.addEventListener('beforeunload', function(e) {
        socket.emit('offline', {'id':id, 'username': username});
    });

    // Logout from chat
    document.querySelector("#logout-btn").onclick = () => {
        socket.emit('offline', {'id':id, 'username': username});
        leaveRoom(room);
    };

    // Trigger 'leave' event if user was previously on a room
    function leaveRoom(room, roomName) {
        socket.emit('leave', {'username': username, 'room': room, 'roomName': roomName});

        document.querySelectorAll('.select-room').forEach(p => {
            p.style.color = "black";
        });
    }

    // Trigger 'join' event
    function joinRoom(room, roomName) {

        // Join room
        socket.emit('join', {'username': username, 'room': room, 'roomName': roomName});

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
